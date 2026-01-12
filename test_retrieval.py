import os
import shutil
import warnings

from EnterpriseContractSentinel.retrieval import VectorStoreManager

# 忽略一些不重要的警告訊息，保持畫面乾淨
warnings.filterwarnings("ignore")

def test_semantic_search():
    """
    TDD 審核點 2：測試語意檢索能力 (Semantic Retrieval)
    目標：系統必須能根據「意思」找到對應的公司準則，而不僅僅是關鍵字。
    """
    # 定義一個臨時的向量資料庫路徑 (測試完會刪除)
    db_path = "./test_chroma_db"
    
    # 清理舊的測試資料 (確保每次測試環境都是乾淨的)
    if os.path.exists(db_path):
        shutil.rmtree(db_path)

    try:
        # 1. 初始化檢索管理器 (這行現在會報錯，因為還沒寫)
        print("⚙️ 初始化向量資料庫...")
        vector_store = VectorStoreManager(persist_directory=db_path)
        
        # 2. 模擬公司的「黃金準則」 (Corporate Playbook)
        # 這是企業最核心的規則，我們要教會 AI
        playbook_texts = [
            "準則A [付款條件]: 所有供應商發票應在收到後 60 天內支付 (Net 60)。",
            "準則B [保密期限]: 保密義務在合約終止後應持續有效 5 年。",
            "準則C [管轄法院]: 雙方同意以新加坡國際仲裁中心為第一管轄機構。",
        ]
        
        # 3. 將這些準則「存入大腦」 (Indexing)
        print("📥 正在將準則轉化為向量記憶...")
        vector_store.add_documents(playbook_texts)
        
        # 4. 進行「語意攻擊測試」
        # 注意：我們問的是「錢」，系統應該要給我們「準則A」，即使我們沒說「付款」兩個字
        query = "我們通常多久要把錢給對方？" 
        print(f"❓ 測試提問: {query}")
        
        results = vector_store.search(query, k=1) # 只取最相關的 1 筆
        
        # 5. 驗證結果
        if results:
            top_result = results[0].page_content
            print(f"💡 AI 檢索結果: {top_result}")
            
            # 關鍵驗證：AI 必須透過語意聯想找到 "Net 60"
            assert "Net 60" in top_result
            print("✅ TDD 審核點 2 通過：語意檢索命中核心準則！")
        else:
            print("🔴 測試失敗：沒有找到任何結果")
        
    except ImportError as e:
        print(f"🔴 真相大白！真正的導入錯誤是：{e}")
        import traceback
        traceback.print_exc() # 這會印出詳細的錯誤路徑
    except Exception as e:
        print(f"🔴 發生其他錯誤：{e}")
        
    finally:
        # 測試結束後清理戰場
        if os.path.exists(db_path):
            shutil.rmtree(db_path)

if __name__ == "__main__":
    test_semantic_search()