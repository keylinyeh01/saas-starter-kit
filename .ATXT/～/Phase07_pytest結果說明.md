## Phase 07：Generation 結構化（schema + 引用 + 防幻覺）— TDD 作戰文件

Phase 7 的目標是把「回答」從聊天變成 **可審核的報告輸出**：每個結論都要能指向 evidence。

**本階段 KPI**：輸出必須符合固定 schema；每個 claim 都要帶 citation（chunk_id/span/source）；模型失敗時不崩，回 ERROR 且可讀原因。

---

### TDD 節奏

1. **先寫 schema validation tests**（鎖定輸出格式）
2. **最小實作**：先用 dummy backend 產出合格 schema（可測、可教）
3. **重構**：把 prompt/formatter 分層，讓不同 LLM provider 共用 formatter

---

### 先寫哪些測試（優先順序）

#### 1) Output Schema Contract

新增：`tests/contracts/test_generation_schema.py`

要求（最小）：
- `status` ∈ {REPORT, CONSULT, ERROR}
- `content` 非空
- `risk`（若有）∈ {HIGH_RISK, NORMAL}
- `citations`（Phase 7 必加）為 list，元素含：
  - `source`, `chunk_id`, `span_start`, `span_end`, `quote`

#### 2) Citation Integrity

新增：`tests/unit/test_citation_integrity.py`

- quote 必須是 evidence chunk 的子字串
- span 必須在 chunk 範圍內

#### 3) Hallucination Guardrail（最低限度）

新增：`tests/golden/test_generation_refuses_without_evidence.py`

- **Given** evidence 空或不相關
- **Then** 必須回 `CONSULT` 或 `ERROR`（不可硬編造）

---

### Gherkin

新增：`certification/features/phase07_generation_structured.feature`

- Scenario: 回答輸出包含 citations（可審核）
- Scenario: evidence 不足時拒答並請求補充（CONSULT）
- Scenario: LLM timeout 時回 ERROR（不 crash）

---

### 最小實作（測試先寫完才做）

- 把 `ContractAnalyst` 進一步拆成：
  - `LLMProvider`：只負責生成 raw text
  - `ReportFormatter`：把 raw text + evidence 組成 schema（含 citations）
- dummy backend 先達標；真實 LLM 標 slow

---

### 重構重點

- prompt 版本化（prompt_id），方便回放
- generation trace：記錄 model/provider、latency、token usage（若可得）

---

### DoD

- schema contract 全綠
- citation integrity 全綠
- golden「無 evidence 不編造」全綠

