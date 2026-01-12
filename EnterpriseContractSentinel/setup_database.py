from retrieval import VectorStoreManager

def init_knowledge_base():
    print("🚀 正在初始化企業知識庫...")
    
    # 1. 初始化向量資料庫管理器
    # 這次我們不刪除舊資料，而是直接往裡面寫入
    vector_store = VectorStoreManager()
    
    # 2. 定義我們要注入的「企業黃金準則」
    # 這些就是我們希望 AI 記住的規則
    playbook_texts = [
        "準則A [付款條件]: 所有供應商發票應在收到後 60 天內支付 (Net 60)。若逾期未付，將按每日 0.05% 計算滯納金。",
        "準則B [保密期限]: 保密義務在合約終止後應持續有效 5 年。違反者需支付懲罰性違約金新台幣 100 萬元。",
        "準則C [管轄法院]: 若發生爭議，雙方同意以台灣台北地方法院為第一審管轄法院。",
        "準則D [驗收條款]: 交付之軟體需經過 14 個工作天的使用者驗收測試 (UAT)，始視為完成交付。",
    ]
    
    # 3. 寫入資料庫
    print(f"📥 正在寫入 {len(playbook_texts)} 條核心準則...")
    vector_store.add_documents(playbook_texts)
    
    print("✅ 知識庫建立完成！現在 main.py 有東西可以讀了。")

if __name__ == "__main__":
    init_knowledge_base()