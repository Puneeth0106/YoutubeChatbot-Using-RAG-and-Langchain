import re
import os
from dotenv import load_dotenv
import streamlit as st

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from youtube_transcript_api._transcripts import Transcript
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

load_dotenv()


def extract_video_id(url_or_id: str) -> str:
    """Extract YouTube video id from a full URL or return the id unchanged."""
    if not url_or_id:
        return ""
    # common URL formats
    # https://www.youtube.com/watch?v=VIDEOID
    m = re.search(r"[?&]v=([A-Za-z0-9_-]{11})", url_or_id)
    if m:
        return m.group(1)
    # youtu.be/VIDEOID
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", url_or_id)
    if m:
        return m.group(1)
    # fallback: assume raw id
    return url_or_id.strip()


def build_retriever_from_video(video_id: str, chunk_size: int = 200, chunk_overlap: int = 20, k: int = 4):
    """Fetch transcript, split, create embeddings and return retriever + vector store.

    This function will try the following in order:
      1. Fetch English transcript if available.
      2. Otherwise pick a manually created transcript if present.
      3. Otherwise pick a generated transcript and attempt to translate it to English if possible.
    Returns (retriever, vector_store, used_language_description)
    """
    api = YouTubeTranscriptApi()
    # get available transcripts first
    transcript_list = api.list(video_id)
    available_manual = [t.language_code for t in transcript_list if not t.is_generated]
    # re-create iterator to examine generated as well
    transcript_list = api.list(video_id)
    available_generated = [t.language_code for t in transcript_list if t.is_generated]

    used_lang_desc = None
    transcript_obj = None

    # Prefer English if present
    if "en" in available_manual or "en" in available_generated:
        transcript_obj = api.fetch(video_id, languages=["en"])
        used_lang_desc = "en"
    else:
        # Try manually created first
        transcript_list = api.list(video_id)
        chosen = None
        for t in transcript_list:
            if not t.is_generated:
                chosen = t
                break

        # If no manual, try generated
        if chosen is None:
            transcript_list = api.list(video_id)
            for t in transcript_list:
                if t.is_generated:
                    chosen = t
                    break

        if chosen is None:
            # No transcripts at all
            raise TranscriptsDisabled(video_id)

        # If chosen transcript supports translation to English, use it
        try:
            if chosen.is_translatable:
                transcript_obj = chosen.translate("en").fetch()
                used_lang_desc = f"{chosen.language_code}->en"
            else:
                transcript_obj = chosen.fetch()
                used_lang_desc = chosen.language_code
        except Exception:
            # fallback to raw fetch
            transcript_obj = chosen.fetch()
            used_lang_desc = chosen.language_code

    # Build corpus
    transcript = " ".join(snippet.text for snippet in transcript_obj)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = text_splitter.create_documents([transcript])

    embedding = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = FAISS.from_documents(documents=chunks, embedding=embedding)
    retriever = vector_store.as_retriever(search_kwargs={"k": k})
    return retriever, vector_store, used_lang_desc


def build_chain(retriever):
    parser = StrOutputParser()

    def format_context(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    parallel_chain = RunnableParallel({
        "question": RunnablePassthrough(),
        "context": retriever | RunnableLambda(format_context),
    })

    prompt = PromptTemplate(
        template="""You are a helpful assistant.
      Answer ONLY from the provided transcript context.
      If the context is insufficient, just say you don't know.

      {context}
      Question: {question}
        """,
        input_variables=["context", "question"],
    )

    model = ChatOpenAI()
    final_chain = parallel_chain | prompt | model | parser
    return final_chain


st.set_page_config(page_title="YouTube Transcript Q&A", layout="wide")
st.title("YouTube Transcript Q&A")

# Read query params to allow pre-filling from the extension (e.g. ?video_id=...)
query_params = st.query_params
# Be defensive: query_params values can be lists or strings depending on Streamlit version.
prefill_video = None
if "video_id" in query_params:
    raw = query_params.get("video_id")
    if isinstance(raw, (list, tuple)):
        raw_val = raw[0] if raw else None
    else:
        raw_val = raw
    if raw_val is not None:
        # coerce to str and normalize to an 11-char id when possible
        raw_str = str(raw_val)
        prefill_video = extract_video_id(raw_str)

# (debug output removed)

auto_index_flag = False
if "auto_index" in query_params:
    auto_index_flag = str(query_params.get("auto_index", ["false"])[0]).lower() == "true"

with st.sidebar:
    st.markdown("## Settings")
    # priority: query param > env var > empty
    default_video = prefill_video or os.environ.get("YOUTUBE_VIDEO_ID", "")
    if prefill_video:
        st.info(f"Prefilled video id from URL: {prefill_video}")
    video_input = st.text_input("YouTube URL or Video ID", value=default_video)
    index_button = st.button("Index Video")

# If the app was opened with auto_index=true, trigger indexing automatically
# but only if we haven't already built an index for this video in this session.
if auto_index_flag and default_video:
    # Avoid re-indexing if retriever already built for this video
    already_indexed_for = st.session_state.get("indexed_for_video")
    if already_indexed_for != default_video:
        vid = extract_video_id(default_video)
        if vid:
            with st.spinner("Auto-indexing video — fetching transcript and building index..."):
                try:
                    retriever, vector_store, used_lang = build_retriever_from_video(vid)
                    st.session_state.retriever = retriever
                    st.session_state.vector_store = vector_store
                    st.session_state.indexed_for_video = default_video
                    st.success("Index built successfully — ask a question below.")
                    st.info(f"Transcript language used: {used_lang}")
                except TranscriptsDisabled:
                    st.error("Transcripts are disabled or not available for this video.")
                except Exception as e:
                    st.exception(e)

if "retriever" not in st.session_state:
    st.session_state.retriever = None
    st.session_state.vector_store = None

if index_button:
    vid = extract_video_id(video_input)
    if not vid:
        st.error("Enter a YouTube video URL or ID.")
    else:
        with st.spinner("Fetching transcript and building index — this may take a minute..."):
            try:
                retriever, vector_store, used_lang = build_retriever_from_video(vid)
                st.session_state.retriever = retriever
                st.session_state.vector_store = vector_store
                st.success("Index built successfully — ask a question below.")
                st.info(f"Transcript language used: {used_lang}")
            except TranscriptsDisabled:
                st.error("Transcripts are disabled or not available for this video.")
            except Exception as e:
                # If the youtube_transcript_api raised a helpful error, show a concise message
                st.exception(e)

st.subheader("Ask a question about the video")
question = st.text_input("Your question")
ask = st.button("Ask")

if ask:
    if st.session_state.retriever is None:
        st.error("No index available. Please index a video first.")
    elif not question:
        st.error("Enter a question.")
    else:
        with st.spinner("Retrieving context and generating answer..."):
            try:
                # show retrieved docs for transparency
                # Use the retriever Runnable API: invoke(...) returns a list of Documents
                docs = st.session_state.retriever.invoke(question)
                with st.expander("Retrieved context (top docs)"):
                    for i, d in enumerate(docs, start=1):
                        st.markdown(f"**Doc {i}** - {d.metadata.get('source', '')}")
                        st.write(d.page_content)

                chain = build_chain(st.session_state.retriever)
                result = chain.invoke(question)
                st.markdown("### Answer")
                st.write(result)
            except TranscriptsDisabled:
                st.error("Transcripts are disabled or not available for this video.")
            except Exception as e:
                st.exception(e)

# Run with:
# streamlit run Youtube_Chatbot/streamlit_app.py
