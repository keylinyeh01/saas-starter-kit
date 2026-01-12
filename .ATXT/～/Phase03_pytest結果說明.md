## Phase 03：Ingestion 強固性（格式/空檔/大檔/錯誤）— TDD 作戰文件

Phase 2 解決的是「可替換後端/可注入/可測」；Phase 3 開始把「操作者會真遇到的 ingestion 崩壞」全部收斂成可驗證的規格。

**本階段核心 KPI**：不論上傳什麼檔、檔案多爛、解析多失敗，系統都 **不 crash**，而且 **能回報可讀的錯誤原因**，並留下可追蹤的 ingestion run 記錄。

---

### Phase 03 目標（最直接影響操作者滿意度）

- **支援格式（Phase 3 最小範圍）**：`pdf` / `docx` / `txt`
  - （選配）`xlsx` 放 `wip`，避免一開始就被 unstructured/依賴拖下水
- **輸出一致**：Ingestion 回傳固定 schema：成功/失敗、文字長度、chunk 數、警告、錯誤碼、可回放 metadata
- **邊界條件不崩**：空檔、只有圖片的 PDF、巨大檔案、亂編碼、不可讀檔案

---

### TDD 節奏（Phase 3 的做法）

1. **先測試（以操作者情境寫）**
   - “我上傳一份掃描 PDF（抽不到字）→ 系統要怎麼回？”
   - “我上傳空的 docx → 系統要怎麼回？”
2. **最小實作（先達到不崩 + 可回報）**
   - 先讓 ingestion 層回傳 `Result`（不要用 print/st.error 當 API）
3. **重構（讓 ingestion pipeline 可教、可維護）**
   - 把 loader / normalizer / chunker / deduper / metadata 分層

---

### Phase 03：先寫哪些測試？（優先順序）

#### 1) Loader Contract Tests（先鎖「讀檔」行為）

建議新增 `tests/contracts/test_ingestion_loader_contract.py`

- **PDF：空白頁 / 無可抽取文字**
  - **Given** 一個只有空白頁的 PDF（測試內用 `pypdf` 產生）
  - **When** 呼叫 `load_document(path)`
  - **Then** 不丟 exception
  - **Then** 回傳 `content=""`（或 content 為空字串）
  - **Then** 回傳 `warnings` 包含「可能是掃描圖／抽不到字」的提示（這是操作者體感關鍵）

- **DOCX：正常 docx**
  - **Given** 一個小 docx（測試內動態生成，避免依賴 repo sample 檔）
  - **Then** 文字應包含預期片段（保證不是空）

- **TXT：亂編碼**
  - **Given** 一個用 `latin-1` 或錯誤 bytes 寫出的 `.txt`
  - **Then** ingestion 不 crash
  - **Then** 回 `ERROR` + `error_code=UNSUPPORTED_ENCODING`（或類似）

> 這邊重點不是「讀得多好」，是「不崩壞 + 可交代」。

#### 2) Chunking/Normalization Tests（先鎖「可重現」）

建議新增 `tests/unit/test_ingestion_normalize.py`

- **空白/多餘空行**：normalize 後不應產生大量空 chunk
- **超長單段文本**：chunker 必須能切出上限內的 chunks（例如 max_chars/max_tokens）

#### 3) Ingestion Pipeline E2E（in-memory，不靠外部 DB）

建議新增 `tests/integration/test_ingestion_pipeline_e2e.py`

- **Given** 一份 docx/txt
- **When** ingest
- **Then** 回傳 schema 正確（run_id、doc_id、chunk_count、errors/warnings）
- **Then** vector store 被呼叫 add（mock 或 naive backend）

---

### Phase 03：Gherkin（操作者情境）

建議新增 `certification/features/phase03_ingestion_robustness.feature`

Scenario（最該先寫的 4 條）：
- 掃描 PDF（抽不到字）不崩，且提示「需要 OCR」
- 空 docx 不崩，且提示「內容為空」
- 不支援副檔名不崩，且回明確錯誤碼
- 超大檔案被拒絕（或分段處理），且回明確限制（例如 max_bytes）

---

### Phase 03：最小實作（測試先寫完才做）

建議把 ingestion API 統一成一個「回傳結構化結果」的函式（或 class），避免 UI/CLI 各自處理例外：

- `ingestion/loaders.py`
  - `load_pdf(path) -> LoadResult`
  - `load_docx(path) -> LoadResult`
  - `load_txt(path, encoding="utf-8") -> LoadResult`
- `ingestion/types.py`
  - `LoadResult { ok, content, warnings, error_code, meta }`
- `ingestion/pipeline.py`
  - `ingest_file(path, *, chunker, vector_store, limits) -> IngestResult`

**Phase 3 的底線**：任何失敗都回 `ok=false` + `error_code`，不向上丟 exception 造成 UI crash。

---

### Phase 03：重構重點（為了「可教」）

- **把 side effects 移出 core**
  - core ingestion 不應依賴 streamlit（`st.error/st.spinner`）
  - UI 只是 consume result，把 warning/error 呈現出來
- **run log**
  - 每次 ingestion 產生 `run_id`，讓操作者能回報問題（debug 可回放）

---

### Phase 03 Definition of Done（通過標準）

- `pytest -q`（預設不跑 slow/wip）全綠
- `.feature`（Phase 03）對應的測試全綠
- 以下情境都必須 **不 crash** 且 **回報可讀原因**：
  - 空白 PDF / 抽不到字（提示 OCR）
  - 空 docx / 空 txt
  - 不支援副檔名
  - 超大檔案（明確限制/策略）

---

### 建議你 Phase 03 先做的兩個反直覺選擇（但很值）

- **先不追求「讀得很完整」**：先追求「不崩 + 可交代 + 可回放」，這才是產品/下單信心的地板。
- **先把 sample 檔移出測試依賴**：測試內動態生成檔案（PDF/DOCX/TXT），避免未來 refactor 造成測試脆弱。

