## Phase 09：可靠性（timeouts/retry/觀測性）— TDD 作戰文件

Phase 9 是「不崩壞」的高級版：不只不 crash，還要在壞網路/壞模型/壞 DB 時維持可用性，並且可觀測。

**本階段 KPI**：關鍵 call chain 有 timeout、可控重試、熔斷/降級；logs/traces 足以定位問題；故障注入測試全綠。

---

### TDD 節奏

1. 先寫 failure-mode tests（故障注入）
2. 最小實作：timeout + retry + error mapping
3. 重構：統一 error types、統一 logging/tracing

---

### 先寫哪些測試

#### 1) Timeout Tests

新增：`tests/contracts/test_timeouts.py`

- LLM provider 超時 → 回 ERROR（不 crash）
- retrieval backend 超時 → 回 ERROR 或降級（可配置）

#### 2) Retry/Backoff Tests

新增：`tests/unit/test_retry_policy.py`

- transient error（例如 503）→ retry N 次
- permanent error（401/invalid request）→ 不 retry

#### 3) Fallback/Degrade Tests

新增：`tests/integration/test_fallback_paths.py`

- vector store 掛掉 → fallback 到 naive（可選）
- LLM 掛掉 → 回 CONSULT（提示稍後重試/改用離線摘要）

---

### 最小實作

- `core/errors.py`：定義 error_code 與可序列化錯誤
- `core/retry.py`：retry policy（可測）
- `core/telemetry.py`：統一 log event schema（run_id/query_id）

---

### 重構重點

- 所有外部呼叫都必須經過同一層 wrapper（才能一致 timeout/retry/trace）
- 「能講清楚」比「吞錯誤」重要：ERROR 必須帶原因與下一步

---

### DoD

- 故障注入 tests 全綠
- 每次 ask 都會產出 run_id + trace（可回放）

