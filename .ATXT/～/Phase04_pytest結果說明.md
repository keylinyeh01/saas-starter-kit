## Phase 04：Chunking 可控（可解釋/可重現）— TDD 作戰文件

Phase 3 把「檔案怎麼來都不崩、錯誤可交代」打底；Phase 4 要解決的是：**chunk 怎麼切**會直接決定檢索命中率、引用可回溯性、以及操作者信任感。

**本階段核心 KPI**：同一份文本、同一份設定 → chunk 結果必須 **可重現**、**可解釋**、**可追溯到來源位置**，且能避免「條款被切斷」造成誤判。

---

### Phase 04 目標（對產品完整度的真影響）

- **Chunk schema 固定**：
  - `chunk_id`
  - `page_content`
  - `source`（檔名/路徑/doc_id）
  - `span`（在原文中的 offset 或頁碼/段落索引）
  - `chunk_index`（第幾段）
  - `hash`（可選，用來偵測重複/回放）
- **可控參數**：
  - `chunk_size`、`chunk_overlap`
  - `separator`/規則（段落/標題/條號）
  - `max_chunks`（防止爆量）
- **可替換 chunker**：rule-based / semantic（semantic 放 `slow` 或 `wip`）

---

### TDD 節奏（Phase 4 的做法）

1. **先測試（先鎖住「不會切壞」）**
2. **最小實作（先 rule-based，語意版後補）**
3. **重構（把 chunking 從 ingestion 中抽出成純函式/組件）**

---

### Phase 04：先寫哪些測試？（優先順序）

#### 1) Determinism Tests（可重現＝信任地板）

建議新增 `tests/unit/test_chunking_determinism.py`

- **Given** 固定文本 + 固定設定
- **When** chunk 兩次
- **Then** chunk 數量、每個 chunk 的 `page_content`、`span` 必須完全一致

> 你要教學/交付時，determinism 是最值錢的特性：能 debug、能回放、能對齊客戶的問題。

#### 2) Boundary Tests（避免條款被切斷）

建議新增 `tests/unit/test_chunking_boundaries.py`

測試案例（一定要先寫）：
- **條號/章節**（例如 `ARTICLE 11.1`、`第十一條`）不能被切成兩半
- **表格/條列**（`1) 2) 3)`）要盡量在同 chunk
- **長條款**（超過 chunk_size）：
  - 允許切，但要保留清楚的 `span`，並且 overlap 足夠讓檢索接得回來

#### 3) Metadata/Span Tests（可追溯＝可審核）

建議新增 `tests/contracts/test_chunk_schema_contract.py`

- **Then** 每個 chunk 必須包含 `source`、`chunk_index`、`span`
- **Then** span 必須落在原文範圍內（不可以出界）

#### 4) Performance Guardrail（防止爆量）

建議新增 `tests/unit/test_chunking_limits.py`

- **Given** 超大文本
- **Then** chunk 數不得超過 `max_chunks`
- **Then** 若超過，回 warning（不是 crash）

---

### Phase 04：Gherkin（操作者情境）

建議新增 `certification/features/phase04_chunking_control.feature`

Scenario（先寫 3 條就夠硬）：
- 同一份文件重跑 ingestion，chunk 結果一致（可回放）
- 條款（ARTICLE/條號）不被切斷，檢索引用完整
- 超大文件 chunk 數量受控，系統不爆 memory

---

### Phase 04：最小實作（測試先寫完才做）

建議先做「rule-based chunker」當主力（Phase 4 不急著上 semantic）：

- `app/ingestion/chunker.py`
  - 新增：`RuleBasedChunker(chunk_size, overlap, split_rules, max_chunks)`
  - 產出：`Chunk`（包含 span/metadata）

接著把 semantic chunker 改成 **optional**：
- 只在有 API key / embeddings / langchain_experimental 時啟用
- 沒有就 fallback 到 rule-based

---

### Phase 04：重構重點（為了可教＋可維護）

- **Chunker 純函式化**
  - input：`raw_text + config + source_meta`
  - output：`List[Chunk]`
  - 不做 I/O、不做 DB
- **把 span 設計成「offset」優先**
  - offset 比「頁碼」穩（PDF 解析頁碼可能飄）
  - 若有頁碼就額外附上（best-effort）

---

### Phase 04 Definition of Done（通過標準）

- `pytest -q`（預設不跑 slow/wip）全綠
- Phase 04 `.feature` 對應測試全綠
- 必須滿足：
  - chunk 結果可重現（deterministic）
  - chunk schema 完整（source/span/chunk_index）
  - chunk 數量受控（max_chunks guardrail）
  - 條款邊界不被切壞（至少覆蓋 ARTICLE/條號的測試）

---

### 一句狠話（Phase 4 的真價值）

如果 chunking 不可重現、不可追溯，你後面 Phase 5~7 做再多 retrieval/rerank/generation，都只是在對「漂移的輸入」打補丁；Phase 4 先把地板鋪平，後面才會變成工程，而不是玄學。

