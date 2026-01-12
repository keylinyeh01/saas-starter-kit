## 10 階段嚴格認證（Roadmap）

### Phase 01：Smoke / 不崩壞（最小端到端）
- **目標**：無外部依賴也能 import + 跑通最小 ingest→retrieve→generate。
- **驗證**：`certification/features/phase01_smoke.feature`

### Phase 02：可替換後端（Backend Abstraction）
- **目標**：LLM / embeddings / vector store 全部可注入、可 mock、可降級。
- **驗證**：mock + contract tests；避免「改一個 provider 全系統炸」。

### Phase 03：Ingestion 強固性（格式/空檔/大檔/錯誤）
- **目標**：PDF/DOCX/TXT/（選）XLSX；空內容與解析失敗不崩、可回報原因。
- **驗證**：Golden files + property tests（邊界條件）。

### Phase 04：Chunking 可控（可解釋/可重現）
- **目標**：chunker 可配置；切分結果可重現；保留條款邊界/來源。
- **驗證**：規格化 chunk schema、 deterministic tests。

### Phase 05：Retrieval 正確性（可調參、可回放）
- **目標**：K、filter、hybrid weights 可調；可回放 query→topK 結果。
- **驗證**：固定 corpus + query set；precision/recall 的最小門檻。

### Phase 06：Reranking 正確性（否定/例外/細節）
- **目標**：能處理否定、例外條款、定義衝突；fallback 也合理。
- **驗證**：專門的 hard cases 測資（法律/合約語言）。

### Phase 07：Generation 結構化（schema + 引用 + 防幻覺）
- **目標**：輸出 schema 固定；每個結論能對應 evidence；錯誤可解釋。
- **驗證**：schema validation + citation checks。

### Phase 08：E2E 使用者下單情境（操作者滿意）
- **目標**：以「操作者」工作流設計：上傳→索引→問答→匯出報告→回饋。
- **驗證**：BDD user journeys + UX acceptance checks（可先用文字）。

### Phase 09：可靠性（timeouts/retry/觀測性）
- **目標**：超時、重試、熔斷；logging/metrics/trace 基本配備。
- **驗證**：故障注入測試（mock timeouts / transient errors）。

### Phase 10：交付/上線（Docker/CI/版本化/回滾）
- **目標**：可重建、可部署、可回滾；最小監控與健康檢查。
- **驗證**：容器啟動、health endpoint、CI pipeline。

