import sys
from langchain_huggingface import HuggingFaceEmbeddings

def test_local_embedding():
    print("--- 正在初始化本地嵌入模型 (首次執行會下載模型) ---")
    try:
        # 使用輕量級模型進行測試
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        text = "SaaS Starter Kit 是一個具備多租戶架構的 AI 解決方案。"
        print(f"--- 正在生成測試文本向量: '{text}' ---")
        
        vector = embeddings.embed_query(text)
        
        print(f"✅ 成功! 向量維度: {len(vector)} (預期: 384)")
        print(f"向量前五碼: {vector[:5]}")
        return True
    except Exception as e:
        print(f"❌ 失敗: {e}")
        return False

if __name__ == "__main__":
    test_local_embedding()