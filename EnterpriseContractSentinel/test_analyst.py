# test_analyst.py
from EnterpriseContractSentinel.generation import ContractAnalyst

def test_legal_brain():
    print("🚀 開始執行單元測試...")
    analyst = ContractAnalyst()
    
    # 測試案例 1：歧義偵測 (預期回傳字典包含 status: 'CONSULT')
    # 目前的程式碼會回傳字串，這裡應該會報錯
    ambiguous_context = "ARTICLE 11.1: 借款人門檻 30%。 ARTICLE 12.5: 被許可人門檻 50%。"
    print("\n--- 測試 1: 歧義偵測 ---")
    try:
        res1 = analyst.analyze(ambiguous_context, "What is the threshold for Change of Control?")
        # 這裡會因為 res1 是字串而導致 res1['status'] 噴出 TypeError
        status1 = res1.get('status', 'Unknown')
        print(f"結果狀態: {status1}")
    except Exception as e:
        print(f"❌ 測試 1 失敗 (預期內): {e}")

    # 測試案例 2：風險判定 (預期門檻 < 50% 時 risk 為 'HIGH_RISK')
    risk_context = "本合約控制權變更門檻設定為 30%。"
    print("\n--- 測試 2: 風險判定 ---")
    try:
        res2 = analyst.analyze(risk_context, "分析此合約風險")
        risk2 = res2.get('risk', 'Unknown')
        print(f"風險等級: {risk2}")
    except Exception as e:
        print(f"❌ 測試 2 失敗 (預期內): {e}")

if __name__ == "__main__":
    test_legal_brain()