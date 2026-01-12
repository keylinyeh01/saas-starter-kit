from EnterpriseContractSentinel.generation import ContractAnalyst

def test_ai_response():
    # 1. 模擬我們從資料庫找到的條款 (Raw Data)
    retrieved_context = """
    準則A [付款條件]: 所有供應商發票應在收到後 60 天內支付 (Net 60)。
    若逾期未付，將按每日 0.05% 計算滯納金。
    """
    
    user_question = "請問如果我們晚付款會怎樣？"
    
    print(f"📄 檢索到的條款:\n{retrieved_context}")
    print(f"❓ 問題: {user_question}")
    print("-" * 30)
    
    # 2. 初始化 AI
    analyst = ContractAnalyst()
    
    # 3. 請 AI 回答
    answer = analyst.analyze(retrieved_context, user_question)
    
    print(f"💡 AI 的專業回答:\n{answer}")

if __name__ == "__main__":
    test_ai_response()