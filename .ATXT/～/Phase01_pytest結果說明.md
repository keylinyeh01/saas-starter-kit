## `pytest -q` 跑完 `7 passed, 3 skipped, 1 deselected` 代表什麼？

你這次跑的結果：

```text
7 passed, 3 skipped, 1 deselected in 28.90s
```

### 直接結論（Phase 1 的意思）

- **7 passed**：有 **7 個測試「真的被執行」**，而且全數通過 → 目前 repo 的 **Phase 1（不崩壞）基線成立**：至少「可被 import、可跑測試、最小端到端（dummy/fallback）能走通」。
- **3 skipped**：有 **3 個測試被刻意跳過**（通常是 `pytest.skip(...)` / 環境不滿足）→ 這些不算通過也不算失敗，代表「我們還沒認證這塊」。
- **1 deselected**：有 **1 個測試被你的選擇條件排除**（不是 skip，是「根本沒納入這次執行」）。
  - 目前 `pytest.ini` 設了：`-m "not slow and not wip"`，所以 **標記成 `slow` 或 `wip` 的測試預設不跑**。
- **in 28.90s**：只代表本次跑完的耗時；不代表效能達標。

### 這次「真的被執行」的 7 個測試是哪些？

以下是 `pytest -vv -m "not slow and not wip"` 顯示的 **7 個 selected tests**（也就是你的 `7 passed`）：

- `EnterpriseContractSentinel/test_analyst.py::test_legal_brain`
- `EnterpriseContractSentinel/test_docx.py::test_docx_loading`
- `EnterpriseContractSentinel/test_generation.py::test_ai_response`
- `EnterpriseContractSentinel/test_retrieval.py::test_semantic_search`
- `tests/certification/test_phase01_smoke.py::test_phase01_feature`
- `tests/unit/test_chunking.py::test_semantic_chunker_separates_distinct_topics`
- `tests/unit/test_reranker.py::test_reranker_prioritizes_logical_correctness`

### 這不代表什麼（避免誤判）

- 不代表「整個產品都 OK / 已達企業級 SLA」  
因為：真正會讓產品崩的東西（外部 DB、真實 embeddings、真實 LLM、容器化、故障注入）很多目前被 `wip/slow/skip` 擋住，Phase 1 的目標是先把「一跑就炸」的結構問題清乾淨。

### 你可以怎麼驗證「到底哪些被跳過/排除」

列出哪些測試被 deselect/skip（高訊號）：

```bash
pytest -q -rs
```

顯示收集到哪些測試（包含 deselected 之前的收集狀態）：

```bash
pytest -q --collect-only
```

### 想跑 `slow/wip`（覆蓋 `pytest.ini` 的預設 addopts）

因為我們在 `pytest.ini` 內寫死了 `addopts = ... -m "not slow and not wip"`，所以要跑全部測試，你應該用 pytest 的 override：

跑「全部」（不套用預設 addopts）：

```bash
pytest -q --override-ini addopts=
```

只跑 slow：

```bash
pytest -q --override-ini addopts= -m slow
```

只跑 wip：

```bash
pytest -q --override-ini addopts= -m wip
```

### Phase 1 的核心認證（Gherkin DSL）

你現在最重要的 Phase 1 規格在：

- `certification/features/phase01_smoke.feature`

只跑 Phase 1：

```bash
pytest -q tests/certification/test_phase01_smoke.py
```

### 下一步（你要的「10 階段嚴格認證」從 Phase 2 開始會變硬）

- Phase 2 要做的是 **把外部依賴抽象化成可注入介面**（LLM / embeddings / vector store），讓 integration test 不靠外部服務也能跑，然後再把真實後端的測試移到 `slow`。

