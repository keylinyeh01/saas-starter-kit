import pytest
from app.ingestion.chunker import SemanticChunker

def test_semantic_chunker_separates_distinct_topics():
    """
    測試目標：驗證語意分塊器能否正確分離兩個截然不同的主題。
    """
    # 準備測試資料：包含生物學與歷史學兩個明顯不同的段落
    text = """
    光合作用是植物、藻類和某些細菌利用光能將二氧化碳和水轉化為葡萄糖的過程。
    這個過程釋放出氧氣作為副產品，對於地球上的生命至關重要。
    葉綠體是進行光合作用的主要細胞器，其中含有葉綠素。
    
    工業革命標誌著從手工生產方法到機器生產方法的轉變。
    這一轉變始於 18 世紀的英國，隨後傳播到歐洲大陸和美國。
    蒸汽機的發明和改良是工業革命的核心動力。
    """
    
    # 初始化分塊器（這裡假設類別尚未實作，測試應失敗）
    chunker = SemanticChunker(threshold_percentile=90)
    chunks = chunker.split_text(text)
    
    # 斷言 1: 應該至少產生兩個區塊
    assert len(chunks) >= 2, "分塊數量不足，未能識別主題轉換"
    
    # 斷言 2: 第一個區塊應包含光合作用相關詞彙，且不含工業革命詞彙
    first_chunk_content = chunks[0].page_content
    assert "光合作用" in first_chunk_content
    assert "蒸汽機" not in first_chunk_content
    
    # 斷言 3: 第二個區塊應包含工業革命相關詞彙
    second_chunk_content = chunks[1].page_content
    assert "工業革命" in second_chunk_content
    assert "葉綠體" not in second_chunk_content