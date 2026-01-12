Feature: Phase 01 - Smoke / 不崩壞（最小端到端）
  目標：確保在「無外部依賴（無 torch/無 ollama/無 openai key）」的情境下，
  核心模組仍可被 import、可走通最小 ingest → retrieve → generate，且回傳結構化結果。

  Scenario: Dummy backends can complete minimal end-to-end flow
    Given 使用 dummy backends（LLM=dummy, VectorStore=naive）
    When 建立 VectorStoreManager
    And 我把文件加入向量庫
    Then 我能用問題檢索到相關片段
    When 我用 ContractAnalyst 分析問題與片段
    Then 回傳必須是結構化報告（含 status/content，且 status 不可為 ERROR）
