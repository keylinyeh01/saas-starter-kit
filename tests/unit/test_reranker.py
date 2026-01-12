from app.reranking.cross_encoder import Reranker

def test_reranker_prioritizes_logical_correctness():
    """
    測試目標：驗證重排序器能處理邏輯否定與具體細節，而非僅依賴關鍵字共現。
    """
    query = "標準保固是否涵蓋進水損壞？"
    
    # 模擬檢索結果 (Retrieved Docs)
    # 注意：這些文檔在向量空間中可能非常接近
    retrieved_docs = [
        # Doc A: directly answers by exclusion (should rank highest)
        "標準保固：明確排除任何液體/進水造成的損壞。",
        # Doc B: mentions water but is about premium plan (should be lower)
        "高級保固：涵蓋進水損壞，但需額外購買並登錄。",
        # Doc C: irrelevant
        "保固申請流程：請於購買後 7 日內完成註冊。",
    ]
    
    reranker = Reranker()
    # 執行重排序
    ranked_docs = reranker.rank(query, retrieved_docs, top_k=3)
    
    # 斷言：重排序器應理解 "明確排除...液體" 是對 "是否涵蓋...水" 的直接回答
    # 文檔 A 應該排在第一位
    assert ranked_docs, "重排序失敗：沒有返回任何結果"
    assert "明確排除" in ranked_docs[0], "重排序失敗：未能識別最具邏輯相關性的回答"
    
    # 文檔 B 雖然包含 "進水"，但屬於 "高級保固"，應該被降級
    assert "高級保固" not in ranked_docs[0]