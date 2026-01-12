## Phase 02：可替換後端（Backend Abstraction）— TDD 作戰文件

Phase 1 的 `7 passed` 只是「不崩壞基線」：我們用 dummy/fallback 拿到可跑、可教、可收集測試的結構。
Phase 2 要開始做「產品完整度」真正會影響交付/客戶下單信心的部分：**外部依賴抽象化 + 可注入 + 可測**。

---

### Phase 02 目標（你要的完整度，最優先的真風險）

- **核心目標**：LLM / Embeddings / VectorStore / Retriever 全部可注入、可 mock、可降級（fallback），且輸出/行為有 contract。
- **關鍵結果**：
  - integration tests 不依賴外部服務也能跑（不需要 Postgres、不需要 OpenAI key、不需要 Ollama）
  - 真實後端測試可以放到 `slow`（需要外部資源的才跑 slow）
  - 「換 provider」不會造成 API/UI/管線爆炸（靠測試鎖定介面）

---

### TDD 原則（本 phase 的節奏）

1. **先測試（Spec/Contract First）**
   - 先把「介面」與「行為保證」用測試寫死
   - 先把最常見的失敗情境（timeouts / missing env / empty corpus）寫成測試
2. **再最小實作（Make It Work）**
   - 先寫最小可跑的 adapter + in-memory 後端
3. **最後重構（Make It Right）**
   - 把 `src/main.py` / `app/retrieval/engine.py` 這類綁死 provider 的東西拆成可 DI 的組件
   - 把 fallback/dummy 收斂成一致的 provider interface（避免到處 if/else）

---

### Phase 02：先寫哪些測試？（優先順序）

#### 1) Provider Contract Tests（最重要，先鎖介面）

**目的**：你以後要教、要賣、要交付，最怕的是「換模型/換庫 → 全系統炸」。contract tests 先把地板鋪好。

要先寫的測試（建議放 `tests/contracts/`）：

- `test_llm_provider_contract.py`
  - **Given** 一個 LLM provider（dummy / ollama / openai）
  - **When** 呼叫 `generate(question, context)`
  - **Then** 回傳必須符合 schema：`{status, content, risk?}`，且 `status != ERROR`（除非故意測 error）
  - **Then** 超時/缺 env 時要回 `ERROR` 且 meta 有原因（不可丟 exception 讓上層 crash）

- `test_vector_store_contract.py`
  - **Given** 一個 VectorStore provider（naive / chroma / pgvector）
  - **When** `add(texts)` 後 `search(query, k)`
  - **Then** `search` 回 list，元素有 `page_content`
  - **Then** 空 query / 空 corpus 不崩，回空結果

> Phase 2 的精髓：**先讓「介面」穩，再談「品質」**。

#### 2) DI / Wiring Tests（鎖住「組裝方式」）

**目的**：避免 `src/main.py` 這種「import 時就載模型/連 DB」的反模式回歸。

要先寫的測試：

- `test_app_does_not_init_external_deps_on_import.py`
  - import app 模組不應建立外部連線（可用 monkeypatch 檢查是否觸發某些初始化）

- `test_api_can_run_with_inmemory_backends.py`
  - FastAPI/CLI 在 in-memory backend 下可跑最小流程（不真的開 server，用 TestClient/直接呼叫 handler）

#### 3) Integration Tests（不靠外部資源也能跑）

**目的**：讓「最小端到端」在 Phase 2 變成更真實的 pipeline，而不是只靠 fallback 的局部測試。

要先寫的測試：

- `test_pipeline_e2e_inmemory.py`
  - ingest 2~3 個 docs
  - query 一次
  - assert：retrieved evidence 包含預期片段；generation 回 structure

---

### Phase 02：Gherkin（DSL）該怎麼寫？（先規格，再測試）

建議新增（先寫 `.feature`，再寫 step defs）：

- `certification/features/phase02_backend_abstraction.feature`
  - Scenario: 換 LLM provider 不影響輸出 schema
  - Scenario: 無外部服務也能跑 e2e（in-memory）
  - Scenario: 外部服務故障時回 ERROR（不 crash）且有可讀原因

---

### Phase 02：最小實作（測試寫完才動手）

你會需要新增一層抽象（Python interface/Protocol）：

- `providers/llm.py`：`LLMProvider.generate(question, context) -> AnalystResult`
- `providers/vector_store.py`：`VectorStore.add(texts)`, `VectorStore.search(query, k) -> list[Doc]`

然後把現有實作包成 adapter：

- `EnterpriseContractSentinel/generation.py` → `OllamaLLMProvider` + `DummyLLMProvider`
- `EnterpriseContractSentinel/retrieval.py` → `ChromaVectorStore` + `NaiveVectorStore`
- `app/retrieval/engine.py` → 改成接受 `vector_store`/`embeddings`/`bm25` 的 DI（不要在 `__init__` 綁死連線字串）

---

### Phase 02：重構目標（可教、可賣、可交付）

- **單一入口點**：一個 `create_app(config)` 或 `build_pipeline(config)`，把 wiring 集中化
- **環境變數只在 config 層讀一次**：避免程式各處亂讀 env（難測、難 debug）
- **可觀測性最小配備（Phase 2 先打底）**：
  - request id / run id
  - 每次 query 的 topK evidence（可回放）

---

### Phase 02 Definition of Done（通過標準）

- `pytest -q`（預設不跑 slow/wip）全綠
- 新增的 contract tests 覆蓋：
  - LLM provider：dummy +（至少一個真實 provider，但標 slow）
  - vector store：naive +（至少一個真實 provider，但標 slow）
- integration tests 可在「無外部服務」環境全綠（in-memory e2e）
- `slow` 測試（選跑）可以在你有 Postgres/Ollama/OpenAI key 的環境下跑通（不納入預設 gating）

---

### 你下一步可以直接做的命令（Phase 2 開始後）

列出被 skip/deselect 的原因（追進度很有用）：

```bash
pytest -q -rs
```

只跑認證 feature（Phase 2 寫完後同理）：

```bash
pytest -q tests/certification/
```

