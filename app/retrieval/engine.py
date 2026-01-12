from langchain_community.retrievers import BM25Retriever
from langchain_postgres import PGVector
from langchain.retrievers import EnsembleRetriever
from langchain_openai import OpenAIEmbeddings
from typing import List

class HybridRetriever:
    def __init__(self):
        # 初始化 Embedding 模型
        self.embeddings = OpenAIEmbeddings()
        
        # 初始化向量資料庫連接 (Postgres + pgvector)
        # 注意：實際連線字串應從環境變數讀取
        self.vector_store = PGVector(
            collection_name="enterprise_docs",
            connection_string="postgresql+psycopg://admin:secret@localhost:5432/rag_db",
            embedding_function=self.embeddings,
        )
        
        self.bm25_retriever = None
        self.ensemble_retriever = None

    async def ingest(self, text_list: List[str]):
        """
        資料攝取流程：同時更新向量庫與關鍵字索引
        """
        # 1. 寫入向量資料庫 (Dense Index)
        await self.vector_store.aadd_texts(text_list)
        
        # 2. 構建 BM25 索引 (Sparse Index)
        # 在生產環境中，BM25 索引通常需要持久化（例如使用 Elasticsearch 或 Redis）
        # 這裡為演示目的使用記憶體版本
        self.bm25_retriever = BM25Retriever.from_texts(text_list)
        self.bm25_retriever.k = 5  # 設定檢索數量
        
        # 3. 創建集成檢索器 (Ensemble)
        # weights=[0.5, 0.5] 表示兩者權重相等
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[
                self.bm25_retriever, 
                self.vector_store.as_retriever(search_kwargs={"k": 5})
            ],
            weights=[0.5, 0.5] 
        )

    async def search(self, query: str):
        """
        執行混合檢索
        """
        if not self.ensemble_retriever:
            raise ValueError("索引未建立，請先執行 ingest()")
            
        return await self.ensemble_retriever.ainvoke(query)