## Phase 08：E2E 操作者下單情境（操作者滿意）— TDD 作戰文件

Phase 8 不再談元件正確性，而是談「操作者流程」：上傳→索引→提問→出報告→匯出→留痕。

**本階段 KPI**：5~8 條核心 user journey（BDD）全綠，且每條都有 clear success criteria（可 demo、可交付）。

---

### TDD 節奏

1. 先寫 Gherkin journeys（用戶語言）
2. 先用 stubbed backend 跑通 UI/CLI journey（不靠外部服務）
3. 重構：把 UI event handlers 變薄，把流程移到 `usecases/`

---

### 先寫哪些測試

#### 1) BDD Journeys（最重要）

新增：`certification/features/phase08_operator_journeys.feature`

最少 5 條（也對應你今天 demo）：
- 上傳文件→索引成功→顯示 chunk/字數
- 提問→顯示 evidence→產生結構化報告
- evidence 不足→CONSULT（請操作者補充/選擇條款）
- 清除記憶/重置→結果可預期
- 匯出報告（markdown/json）→可下載/可複製

#### 2) UI Safety Tests（不崩）

新增：`tests/integration/test_streamlit_flow_smoke.py`（可先標 wip）

- 不用真的跑瀏覽器，先測 usecase 層輸入輸出（Phase 8 重構後才會有）

---

### 最小實作

- 建立 `usecases/`：
  - `ingest_usecase.ingest(file) -> IngestResult`
  - `ask_usecase.ask(question) -> AnswerResult`
  - `export_usecase.export(answer) -> bytes/str`
- Streamlit/FastAPI 只負責 I/O 與顯示

---

### 重構重點

- 所有 side effects（cache/session_state/檔案 I/O）集中到邊界層
- usecase 必須可直接被 pytest 呼叫（這才算真 TDD）

---

### DoD

- Phase 08 journeys 對應測試全綠
- 「無外部服務」下也能 demo 完整流程（stubbed backends）

