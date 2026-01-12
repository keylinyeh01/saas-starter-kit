import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# 1. 引入 HuggingFace Embeddings (PDF 第 2 頁)
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI 
from langchain.chains import RetrievalQA

# 載入 .env 設定
load_dotenv()

app = FastAPI(title="Enterprise RAG Demo (OpenRouter Edition)")

class IngestRequest(BaseModel):
    content: str
    metadata: dict

class QueryRequest(BaseModel):
    query: str

# --- 架構變更點 (PDF 第 3 頁) ---

# 1. 設定 Embeddings (使用本地模型: all-MiniLM-L6-v2)
print("正在載入 Embedding 模型，請稍候...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
print("Embedding 模型載入完成！")

# 2. 設定 LLM (使用 OpenRouter)
llm = ChatOpenAI(
    model="anthropic/claude-3.5-sonnet", # 或 "meta-llama/llama-3-8b-instruct"
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0
)

# 3. 資料庫連接 (初始化 vector_store) <--- 你剛剛缺的就是這段
CONNECTION_STRING = os.getenv("DATABASE_URL")

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="demo_collection",
    connection=CONNECTION_STRING,
    use_jsonb=True,
)

# --- API 定義 ---

@app.post("/ingest")
async def ingest_document(request: IngestRequest):
    try:
        doc = Document(page_content=request.content, metadata=request.metadata)
        vector_store.add_documents([doc])
        return {"status": "success", "id": "doc_123"}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_knowledge_base(request: QueryRequest):
    try:
        # 搜尋最相似的 1 筆資料
        retriever = vector_store.as_retriever(search_kwargs={"k": 1})
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        result = qa_chain.invoke({"query": request.query})
        
        return {
            "answer": result["result"],
            "source": [doc.metadata for doc in result["source_documents"]]
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))