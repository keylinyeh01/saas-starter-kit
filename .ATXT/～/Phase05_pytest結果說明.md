## Phase 05：Retrieval 正確性（可調參、可回放）— TDD 作戰文件

Phase 4 把 chunking 地板鋪平後，Phase 5 才能開始把「檢索命中」變成工程：可調參、可回放、可量化。

**本階段核心 KPI**：對固定 corpus + 固定 query set，retrieval 的 topK 命中必須達到門檻，並且每次查詢都能輸出「為什麼這些結果被選到」（可回放）。

---

### Phase 05 目標

- **檢索行為可配置**：`k`、filter（metadata）、hybrid 權重、score 閾值
- **可回放**：每次 query 產出 `retrieval_trace`（query、params、候選集合、分數、topK、時間）
- **離線可測**：in-memory corpus 也能跑 integration tests（不靠外部 DB/Embeddings）

---

### TDD 節奏

1. **先測試**：固定 corpus + query set → assert topK 命中
2. **最小實作**：先做 deterministic retriever（BM25/naive overlap），再接真實 vector
3. **重構**：把 retriever 組裝（wiring）集中，避免各處散落 search kwargs

---

### 先寫哪些測試（優先順序）

#### 1) Golden Retrieval Set（最重要）

新增：`tests/golden/test_retrieval_topk.py`

- **Given** 10~30 條「公司準則/合約條款」固定文本（直接寫在測試內，或放 `tests/fixtures/`）
- **When** 針對 10 個 query 檢索
- **Then** top1 / top3 必須命中指定 doc_id（用 metadata 或 hash）

最先鎖的 query 類型（直接影響下單信心）：
- 同義詞（付款/匯款/給錢）
- 否定（不包含/排除）
- 定義衝突（控制權門檻 30%/50%）

#### 2) Filters / Metadata（可控）

新增：`tests/unit/test_retrieval_filters.py`

- filter by `source` / `doc_id` / `section`
- assert：被 filter 掉的 doc 不應出現在 topK

#### 3) Trace / Replay（可回放）

新增：`tests/contracts/test_retrieval_trace_schema.py`

- `retrieval_trace` 必須包含：
  - `query`, `k`, `filters`, `candidates_count`, `topk`, `scores`, `latency_ms`

---

### Gherkin（操作者情境）

新增：`certification/features/phase05_retrieval_correctness.feature`

- Scenario: 同一 query 重跑，topK 一致（deterministic backend）
- Scenario: 開啟 filter 後結果正確縮小
- Scenario: trace 可被輸出並用於回放 debug

---

### 最小實作（測試先寫完才做）

- `retrieval/retriever.py`
  - `Retriever.search(query, *, k, filters) -> (docs, trace)`
  - 先提供 `NaiveRetriever`（token overlap）+ `BM25Retriever`（純文字）
  - 真實 vector 後端先標 `slow`

---

### 重構重點

- **把 retrieval params 統一成 config dataclass**
- **把 trace 變成第一級輸出**（別用 print）

---

### DoD（通過標準）

- `pytest -q` 全綠
- golden retrieval tests：top3 命中率達門檻（例如 ≥ 0.9）
- trace schema contract tests 全綠

