# Youtube Chatbot — RAG Q&A over YouTube transcripts

A Streamlit-based Retrieval-Augmented Generation (RAG) app that indexes YouTube transcripts and answers natural-language questions using LangChain and an LLM (OpenAI by default). The project also includes a Chrome extension to prefill videos and a small FastAPI backend to enable in-extension chat for local setups.

## Highlights
- Index YouTube transcripts (with fallback for non-English transcripts)
- Split, embed and store transcript chunks in a vector store (FAISS by default)
- Query via a Streamlit UI (with URL prefill and auto-indexing)
- Optional local FastAPI server to let a Chrome extension perform indexing and chat from the extension popup
- Deployment-ready guidance for Streamlit Community Cloud and Docker

## Table of contents
- Features
- Quick start (local)
- Docker
- Streamlit Community Cloud
- Chrome extension & local API
- Files of interest
- Tools & dependencies
- Notes & troubleshooting

## Features
- Fetch transcripts using `youtube-transcript-api` (handles enforced languages and translation fallback)
- Vector store retrieval pipeline using LangChain: splitting → embedding → FAISS
- LLM-powered answers using `ChatOpenAI` (OpenAI key required)
- Auto-indexing when the app is opened with `?video_id=<id>&auto_index=true`

## Quick start (local)
1. Create and activate your Python virtualenv and install packages (see `requirements.txt`).
2. Export your OpenAI key:

```bash
export OPENAI_API_KEY="sk-..."
```

3. From the project root run the Streamlit app:

```bash
cd Youtube_Chatbot
streamlit run streamlit_app.py
```

4. Paste a YouTube video URL or ID into the UI. To open the app prefilled from the browser or extension use:

```
<your-app-url>?video_id=<YOUTUBE_VIDEO_ID>&auto_index=true
```

Notes:
- The first index operation builds embeddings and stores them in FAISS (in-memory by default). Large videos will take longer and consume memory.

## Docker
Build and run the included Docker image (see `README_DEPLOY.md` for details):

```bash
cd Youtube_Chatbot
docker build -t ytqa .
docker run -it --rm -p 8501:8501 -p 8000:8000 ytqa
```

The container runs the Streamlit app by default. To run the FastAPI server inside the container:

```bash
docker run -it --rm -p 8000:8000 ytqa bash -lc "uvicorn Youtube_Chatbot.api_server:app --host 0.0.0.0 --port 8000"
```

## Streamlit Community Cloud
Follow the steps in `README_DEPLOY.md`:

- Push this repository to GitHub.
- Create a new app on https://streamlit.io/cloud and point it to `Youtube_Chatbot/streamlit_app.py`.
- Add the `OPENAI_API_KEY` in the Streamlit app's Secrets.

Important: `faiss-cpu` may fail to build on Streamlit Cloud. If you see build errors for FAISS, either:

- Use the provided Docker option (recommended), or
- Modify `requirements.txt` to use a different vectorstore (e.g. `chromadb`) or implement the FAISS fallback code (see next section).

## Chrome extension & local API
- The `chrome_extension/` folder contains a small MV3 extension that extracts the current YouTube video ID and offers a popup which can open the Streamlit app prefilled with `video_id` and `auto_index=true`.
- Optionally, a small FastAPI server (`api_server.py`) is included so the extension popup can call `POST /index` and `POST /query` on `http://localhost:8000` to index and chat without opening the Streamlit UI. This is intended for local development only.

Security notes:
- The FastAPI backend is open by default (CORS enabled) for local development. If you expose it publicly, add authentication and tighten CORS.

## Files of interest
- `streamlit_app.py` — Streamlit UI: index and query videos
- `backend.py` — shared indexing and chain-building logic used by the app and API
- `api_server.py` — small FastAPI server (index and query endpoints)
- `chatbot.py` — small local script demonstrating `youtube-transcript-api` usage
- `requirements.txt` — Python dependencies used by the app
- `Dockerfile` — containerized runtime for the app and API
- `chrome_extension/` — manifest, popup UI, content script and background worker for the Chrome extension
- `README_DEPLOY.md` — deployment guidance and notes

## Tools & dependencies
This project uses the following main tools and libraries:

- Python 3.11+ (the project was developed and tested with 3.11)
- Streamlit — UI framework for the web app
- youtube-transcript-api — fetch YouTube transcripts and translations
- LangChain (langchain-core + adapters) — building the retrieval + LLM pipeline
- OpenAI (Chat models) — LLM used for answering questions (requires `OPENAI_API_KEY`)
- FAISS (`faiss-cpu`) — vector store (embedding index). Note: may not build on some cloud hosts; see fallback options.
- Chroma (optional) — alternative vector store if FAISS is problematic on your host
- FastAPI & Uvicorn — optional lightweight API server used by the Chrome extension popup
- Docker — optional containerization for reproducible deployments

The full list of Python packages is in `requirements.txt`.

## Troubleshooting & tips
- AttributeError with `youtube-transcript-api`: use the instance interface:

```py
from youtube_transcript_api import YouTubeTranscriptApi
transcript = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
```

- If you see errors about `get_relevant_documents`, it may be due to LangChain version differences — the project uses retriever runnables and calls the retriever with `invoke(...)`.
- If Streamlit Cloud build fails due to FAISS, either switch to Docker, remove `faiss-cpu` from requirements and use Chroma, or implement the fallback in code to prefer Chroma when FAISS isn't available.

## Contributing & next steps
- Persist FAISS indices to disk so you don't re-index on every restart.
- Add a FAISS → Chroma fallback to improve compatibility with cloud hosts.
- Add CI to build and publish a Docker image on push.

If you'd like, I can implement the FAISS fallback and add a small README snippet showing how to switch to Chroma.

---
Project created to demonstrate RAG over YouTube transcripts with LangChain, a Streamlit UI, and a lightweight dev-friendly Chrome extension.

If you need a shorter README for the repository root or a GitHub-ready README with badges, I can add that next.
