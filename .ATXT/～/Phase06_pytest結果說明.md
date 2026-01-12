## Phase 06：Reranking 正確性（否定/例外/細節）— TDD 作戰文件

Retrieval 命中後，rerank 決定「最先展示哪段 evidence」，這直接影響操作者信任與下單。

**本階段 KPI**：對一組 hard cases（否定/例外/定義衝突），reranker 的 top1 必須選到「邏輯上最直接回答問題」的證據片段。

---

### TDD 節奏

1. 先寫 hard cases 測試（最值錢）
2. 先用 heuristic reranker 達標（不靠 torch）
3. 再接 cross-encoder（標 slow），最後重構成可替換 provider

---

### 先寫哪些測試

#### 1) Hard Cases Golden Set

新增：`tests/golden/test_rerank_hard_cases.py`

至少先寫 12 條（越貼近合約越好）：
- 問「是否涵蓋水損？」→ top1 應是「明確排除液體」而不是「高級保固涵蓋」
- 問「控制權門檻？」→ top1 應抓到包含門檻數字的定義段
- 問「逾期付款後果？」→ top1 應抓到滯納金/違約條款

每條測試都要有：
- query
- candidates（至少 3 段）
- expected_top1_contains（關鍵子字串）

#### 2) Stability Tests

新增：`tests/unit/test_rerank_stability.py`

- 相同輸入 → output 必須 deterministic（至少在 heuristic backend）

---

### Gherkin

新增：`certification/features/phase06_reranking_logic.feature`

- Scenario: 否定語意優先
- Scenario: 例外條款優先
- Scenario: 定義段優先（Definition wins）

---

### 最小實作

- 先把目前 `app/reranking/cross_encoder.py` 的 fallback heuristic 擴充成「可配置規則表」
- cross-encoder provider 放 slow，避免 demo/CI 被 torch 卡死

---

### 重構重點

- reranker input/output schema 固定（documents 應包含 metadata）
- rerank trace：輸出每個候選的 score（可回放）

---

### DoD

- hard cases top1 命中率 ≥ 門檻（例如 0.9）
- rerank trace schema 全綠

