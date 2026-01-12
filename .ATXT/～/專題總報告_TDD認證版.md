## 專題總報告（TDD 嚴格認證版）— 給下一代的交付與傳承

> 這份報告不是「寫給現在的我」；是寫給「未來要接手、要教學、要賣給企業」的你/你們。  
> 核心承諾：**先測試、再實作、最後重構**，並且把這件事落到 repo 裡可被執行、可被驗證。

---

### 0. 一句話（TL;DR）

這個專題把「企業級 RAG」做成一套**可驗證的產品**：我們用 **pytest + Gherkin DSL** 建立「10 階段嚴格認證」，先把最會翻車的 import/依賴/測試結構問題清乾淨，確保 **不崩壞（Phase 1）**，並且把後續 Phase 2~10 的測試優先順序、最小實作與重構策略寫死成文件，讓專題能被延伸、被交付、被教學。

---

### 1. 你在賣什麼（產品定位與交付語言）

你目前的產品方向包含三條線（都能用同一套認證方法管理）：

- **企業級 RAG 系統建置（Fixed-Price）**  
  交付重點：可部署、可審核（evidence）、可回放（trace）、可匯出（report）
- **開源模型微調服務（Fine-Tuning as a Service）**  
  交付重點：資料治理、可重現訓練、評測門檻、回滾策略
- **多代理工作流自動化（AI Agent Workflow Automation）**  
  交付重點：流程可視化、失敗可復原、權限/審計、可測的工具鏈

這個 repo 目前最成熟、最可 demo 的主軸是：**合約審查型 RAG（Enterprise Contract Sentinel）**：上傳→索引→提問→顯示 evidence →輸出報告。

---

### 2. TDD 在本專題是「真的落地」，不是口號

這次的 TDD 落地方式有三層（從硬到軟）：

- **（硬）pytest gating：一行命令判斷是否能交付**
  - `pytest -q` 必須穩定全綠
  - 目前結果：`7 passed, 3 skipped, 1 deselected`
- **（硬）Phase 1 BDD：用 Gherkin 把最小端到端寫成可執行規格**
  - 規格：`certification/features/phase01_smoke.feature`
  - Runner：`certification/gherkin.py`
  - 可執行測試：`tests/certification/test_phase01_smoke.py`
- **（軟）10 階段認證：把未來工作拆成可驗收的序列**
  - 路線：`docs/certification/10-phases.md`
  - 每一 phase 都先寫「要先測什麼」，再談實作與重構（見 `.ATXT/～/Phase02~10_pytest結果說明.md`）

> 關鍵原則：**先把「介面」與「失敗模式」寫成測試鎖死**，再動程式。  
> 這會讓你永遠知道「現在到底能交付到哪一步」。

---

### 3. Phase 1（不崩壞）你已經拿到什麼確定性？

#### 3.1 Phase 1 通過標準（我們已達成）

- import-time 不會因外部依賴（torch/transformers/ollama/openai）直接爆炸
- 在「無外部服務」下，最小端到端仍可跑通（dummy/fallback）
- 測試可以被收集、可執行、可重現

#### 3.2 你現在真的跑過哪些測試？（可被引用的事實）

`pytest -vv -m "not slow and not wip"` 的 7 個通過測試：

- `EnterpriseContractSentinel/test_analyst.py::test_legal_brain`
- `EnterpriseContractSentinel/test_docx.py::test_docx_loading`
- `EnterpriseContractSentinel/test_generation.py::test_ai_response`
- `EnterpriseContractSentinel/test_retrieval.py::test_semantic_search`
- `tests/certification/test_phase01_smoke.py::test_phase01_feature`
- `tests/unit/test_chunking.py::test_semantic_chunker_separates_distinct_topics`
- `tests/unit/test_reranker.py::test_reranker_prioritizes_logical_correctness`

#### 3.3 「不能出事」層級修復（最值錢的一刀）

你機器上 torch/transformers 會因權限噴 `PermissionError`。  
我們把 **Streamlit app** 的 chunker 匯入改成 **lazy import + fallback chunker**，避免 demo 現場「程式一開就死」。

---

### 4. 認證系統（10 Phases）是怎麼幫你管理專案的？

你不是在寫一堆 TODO；你是在建立「可驗收的工程節奏」：

- Phase 01：Smoke / 不崩壞（最小端到端）
- Phase 02：可替換後端（DI/contract tests）
- Phase 03：Ingestion 強固性（格式/空檔/大檔/錯誤不崩）
- Phase 04：Chunking 可控（可重現/可追溯/span）
- Phase 05：Retrieval 正確性（topK 命中、可回放 trace）
- Phase 06：Reranking 正確性（否定/例外/定義衝突 hard cases）
- Phase 07：Generation 結構化（schema + citations + 拒答）
- Phase 08：操作者 Journey（下單情境）
- Phase 09：可靠性（timeouts/retry/觀測性/故障注入）
- Phase 10：交付/上線（Docker/CI/回滾）

這 10 階段的「先測試重點、最小實作、重構方向、DoD」都已產生成文件（在 `.ATXT/～/Phase02~Phase10_pytest結果說明.md`）。

---

### 5. DEMO（拿單）你要展示的不是模型，是「交付能力」

你下午 DEMO 最強的 5 個情境已整理好（含話術/成功判準/Plan B）：

- `.ATXT/～/DEMO_5個情境_拿單版.md`

另外，為了「交付感」我們在 Streamlit 報告頁新增：

- **一鍵匯出 Markdown/JSON**（可直接給客戶內部留存/對接）

---

### 6. 你要怎麼跑（最小命令，傳承必備）

#### 6.1 只看是否能交付（預設 gating）

```bash
pytest -q
```

#### 6.2 列出 skip/deselect 的原因（控風險）

```bash
pytest -q -rs
```

#### 6.3 只跑 Phase 1 認證（最小端到端）

```bash
pytest -q tests/certification/test_phase01_smoke.py
```

#### 6.4 DEMO 安全模式（建議）

```bash
export ECS_LLM_BACKEND=dummy
export ECS_VECTORSTORE_BACKEND=naive
```

---

### 7. 給下一代：你要怎麼「正確地繼承」這個專題？

#### 7.1 永遠先問：我現在在哪個 phase？

不要「想到什麼就加什麼」。  
先把需求對應到 phase，然後：

1) 先寫 `.feature`（用戶語言）  
2) 再寫 pytest（可執行）  
3) 再補最小實作  
4) 再重構（抽介面、抽 config、集中 wiring）

#### 7.2 永遠先鎖失敗模式（企業最在意）

對企業來說，最致命不是「答得不夠漂亮」，而是：

- **會崩**（import 就死、外部服務掛就死）
- **無法解釋**（沒 evidence、沒 trace）
- **無法交付**（不能匯出、不能留痕、不能回放）

所以這套認證是「由下往上」：先保不崩、再保可審核、最後才拼品質。

---

### 8. 附錄：你現在 repo 內的「高信號資產」清單

- **Phase 1 認證**：
  - `certification/features/phase01_smoke.feature`
  - `certification/gherkin.py`
  - `tests/certification/test_phase01_smoke.py`
- **10 phases 路線**：`docs/certification/10-phases.md`
- **Phase 1 報告**：`docs/reports/phase01.md`
- **Phase 1/2/3/4/5/6/7/8/9/10 說明**：`.ATXT/～/Phase01~Phase10_pytest結果說明.md`
- **DEMO 腳本（拿單版）**：`.ATXT/～/DEMO_5個情境_拿單版.md`

