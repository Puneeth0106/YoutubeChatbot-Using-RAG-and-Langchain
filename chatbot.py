import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
#from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnableParallel, RunnableBranch, RunnableSequence, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
load_dotenv()

#1. Fetch Transcript with YoutubeTranscriptApi

video_id="QP86-ThM8-8"

try:
    transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
    transcript=' '.join(line.text for line in transcript_list)
    #print(transcript)
except TranscriptsDisabled:
    print("No captions available for this video.")

#2. TextSplitting the transcript into multiple chunks 

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=20,
)
chunks= text_splitter.create_documents([transcript])


#2.1 Storing the embeddings into vector store
embedding=OpenAIEmbeddings(model="text-embedding-3-small")
vector_store= FAISS.from_documents(
    documents=chunks,
    embedding=embedding)

#2.2 Retrieving the results

retriever= vector_store.as_retriever(
    search_kwargs={"k": 4}
)

#3. Augmentation

model= ChatOpenAI()
prompt= PromptTemplate(
    template="""You are a helpful assistant.
      Answer ONLY from the provided transcript context.
      If the context is insufficient, just say you don't know.

      {context}
      Question: {question}
        """,
    input_variables=['context','question']
)


# retrieved_docs= retriever.invoke(question)



# #4. Generation

# final_prompt= prompt.invoke({'context':context,'question':question})
# print(final_prompt)
# print('\n')


# final_result= model.invoke(final_prompt)
# print('Final-Result: \n\n',final_result.content)


#5. Chain

parser= StrOutputParser()

def format_context(docs):
    context= '\n\n'.join(doc.page_content for doc in docs)
    return context

parallel_chain= RunnableParallel(
    {'question':RunnablePassthrough(),
     'context' : retriever | RunnableLambda(format_context)}
)

final_chain= parallel_chain | prompt | model | parser

results= final_chain.invoke("is the topic How to build mental strength. if yes, what are they")

print(results)
