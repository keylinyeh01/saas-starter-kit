## Phase 10：交付/上線（Docker/CI/版本化/回滾）— TDD 作戰文件

Phase 10 是「可賣」：客戶關心的不是你能跑，而是你能穩定交付、可部署、可回滾、可維運。

**本階段 KPI**：乾淨的 build、可重建的 Docker image、可部署的 compose、CI gating、health checks、版本化與回滾策略。

---

### TDD 節奏（交付版）

1. 先寫「交付驗收測試」：容器啟動、health endpoint、最小 e2e
2. 最小實作：Dockerfile/compose/health route
3. 重構：把 config/secret/依賴注入整理成可重建的部署單元

---

### 先寫哪些測試（先鎖交付底線）

#### 1) Health Check Contract

新增：`tests/contracts/test_health_endpoint.py`（若你走 FastAPI）

- `GET /health` 回 200
- 回傳版本、commit（若可）、time

#### 2) Container Smoke（標 slow）

新增：`tests/slow/test_docker_smoke.py`

- `docker compose up` 後 API 可回應
- 最小 ingest/query 走通（可以 stubbed backend）

---

### 最小實作（Phase 10 的核心）

- `Dockerfile`：鎖 python/node 版本，避免漂移
- `docker-compose.yml`：外部依賴（postgres/redis）清楚列出
- `Makefile` 或 `scripts/`：一鍵 build/run/test
- `README`：最小啟動命令 + env 範例

---

### 重構重點

- **配置集中**：所有 env 讀取集中到 config module
- **分層 image**：base deps 與 app code 分層，build 快、cache 穩
- **回滾策略**：tagging + migration strategy（資料庫 schema 變更要可回滾）

---

### DoD

- CI：`pytest -q`（不含 slow）全綠
- `docker build` 可重建
- `docker compose up` 起得來，health check OK
- 有清楚的「如何回滾」文件（至少一頁）

