from dotenv import load_dotenv
load_dotenv() # This line loads the variables from .env

import os
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from pinecone import Pinecone

app = FastAPI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
index_name = "pdf-index"

vectorstore = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embedding
)

# Initialize ChatOpenAI
llm = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY,
    model_name='gpt-4o',
    temperature=0.0
)

# Creating Prompt
prompt_template = """Use the following pieces of context to answer the question at the end. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Provide a concise answer in 1-4 sentences:"""

PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

# Creating a Langchain QA chain
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(),
    chain_type_kwargs={"prompt": PROMPT}
)

class Query(BaseModel):
    question: str
   
# Create API Endpoint
@app.post("/ask")
async def ask_question(query: Query):
    response = qa.invoke(query.question)
    return {"answer": response['result']}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)