import pytest
import pytest_asyncio

pytest.skip("WIP: 需要可替換的 vector store（避免測試依賴外部 Postgres/OpenAI）", allow_module_level=True)

from app.retrieval.engine import HybridRetriever

@pytest.mark.asyncio
@pytest.mark.wip
async def test_hybrid_retrieval_capabilities():
    """
    測試目標：驗證混合檢索器能同時處理關鍵字精確查詢與語意模糊查詢。
    """
    # 準備測試文檔
    docs = [
        "文檔A: 產品型號 XJ-900-Z 支援 220V 並附帶 2 年保固。",
        "文檔B: 渦輪增壓器可提升進氣效率，讓引擎呼吸更順暢。",
    ]
    
    retriever = HybridRetriever()
    pytest.skip("WIP: 需要可替換的 vector store（避免測試依賴外部 Postgres）", allow_module_level=False)
    
    # 測試案例 1: 精確型號查詢 (BM25 應主導)
    # 預期：即使語意上不完整，必須找到包含精確型號的文檔 A
    results_sku = await retriever.search("XJ-900-Z")
    assert results_sku.page_content == docs[0], "關鍵字檢索失敗：未能優先返回精確型號文檔"
    
    # 測試案例 2: 概念功能查詢 (Vector 應主導)
    # 預期：查詢詞彙與文檔 B 無重疊，但語意一致，應找到文檔 B
    results_concept = await retriever.search("什麼裝置能幫助引擎呼吸更順暢？")
    assert results_concept.page_content == docs[1], "語意檢索失敗：未能識別功能描述"