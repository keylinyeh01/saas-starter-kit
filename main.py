import sys
from EnterpriseContractSentinel.retrieval import VectorStoreManager
from EnterpriseContractSentinel.generation import ContractAnalyst

def main():
    print("===========================================")
    print("🕵️‍♂️ 企業合約守門員 (Enterprise Contract Sentinel) 已啟動")
    print("===========================================")

    # 1. 初始化大腦 (檢索系統)
    # 注意：這裡假設你之前已經跑過 test_ingestion.py 或 test_retrieval.py
    # 所以資料庫裡應該已經有資料了。
    print("⚙️ 正在載入向量記憶庫...")
    vector_store = VectorStoreManager()
    
    # 2. 初始化嘴巴 (生成模型)
    print("🤖 正在喚醒 AI 法務助理...")
    analyst = ContractAnalyst()
    
    print("\n✅ 系統準備就緒！請輸入關於合約的問題 (輸入 'exit' 或 'quit' 離開)")
    print("-" * 50)

    # 3. 進入對話迴圈
    while True:
        try:
            # 獲取使用者輸入
            user_query = input("\n🙋 你問: ").strip()
            
            # 檢查是否要離開
            if user_query.lower() in ['exit', 'quit', 'bye']:
                print("👋 再見！")
                break
            
            if not user_query:
                continue

            # A. 檢索 (Retrieval)
            print("   🔍 翻閱合約中...")
            results = vector_store.search(user_query, k=3)
            
            if not results:
                print("   ⚠️ 找不到相關條款，請換個方式問問看。")
                continue
            
            # 把找到的片段組合成一段長文字
            context_text = "\n\n".join([doc.page_content for doc in results])
            
            # B. 生成 (Generation)
            print("   🤔 分析條款並撰寫回答...")
            response = analyst.analyze(context_text, user_query)
            
            # C. 輸出結果
            print(f"\n💡 AI 回答:\n{response}")
            print("-" * 50)

        except KeyboardInterrupt:
            # 處理 Ctrl+C 強制結束
            print("\n👋 程式已終止")
            break
        except Exception as e:
            print(f"🔴 發生錯誤: {e}")

if __name__ == "__main__":
    main()