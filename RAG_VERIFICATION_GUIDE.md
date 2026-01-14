# RAG 基礎認證執行指南

本指南將協助您逐步完成 RAG 系統的三項基礎認證測試。

---

## 📋 前置準備

### 1. 確認 Docker 容器運行狀態

```bash
# 檢查 nexus_db 容器是否運行
docker ps | grep nexus_db

# 如果沒有運行，啟動資料庫
docker-compose up -d db

# 確認容器狀態
docker ps
```

**預期結果**: 應該看到 `nexus_db` 容器正在運行，狀態為 `Up`。

---

### 2. 安裝 Python 依賴

```bash
# 如果還沒有虛擬環境，先建立一個
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝測試所需的套件
pip install -r requirements.txt

# 確認關鍵套件已安裝
pip list | grep -E "(langchain-postgres|sentence-transformers|psycopg2)"
```

**預期結果**: 應該看到 `langchain-postgres`, `sentence-transformers`, `psycopg2-binary` 都已安裝。

---

## 🚀 執行認證測試

### 方法一：使用自動化測試腳本（推薦）

```bash
# 確保在虛擬環境中
source venv/bin/activate

# 執行測試腳本
python test_rag_basic.py
```

**測試腳本會自動執行以下三個步驟：**

1. **Docker 容器連線測試**
   - 檢查 `nexus_db` 容器是否運行
   - 測試 PostgreSQL 連線
   - 確認 `pgvector` 擴充已安裝

2. **向量資料庫寫入測試**
   - 載入 Embedding 模型（BAAI/bge-m3）
   - 連線到 pgvector 資料庫
   - 寫入 3 筆測試文件
   - 驗證資料是否成功寫入

3. **檢索準確度測試**
   - 執行 3 個測試查詢
   - 檢查檢索結果是否包含預期關鍵字
   - 評估匹配準確度

---

### 方法二：手動逐步驗證

如果您想更深入了解每個步驟，可以手動執行：

#### 步驟 1: 測試資料庫連線

```bash
# 使用 psql 連線測試
psql -h localhost -p 5432 -U postgres -d nexus

# 在 psql 中執行：
# SELECT version();
# SELECT * FROM pg_extension WHERE extname = 'vector';
# \q
```

#### 步驟 2: 測試向量寫入

```python
# 在 Python REPL 中執行
from langchain_postgres import PGVector
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
vector_store = PGVector(
    collection_name="test_collection",
    connection="postgresql+psycopg://postgres:postgres@localhost:5432/nexus",
    embedding_function=embeddings,
)

doc = Document(page_content="測試文件內容")
vector_store.add_documents([doc])
print("寫入成功！")
```

#### 步驟 3: 測試檢索

```python
# 繼續在 Python REPL 中
results = vector_store.similarity_search("測試", k=1)
print(results[0].page_content)
```

---

## 📊 預期結果

### ✅ 成功情況

```
============================================================
RAG 基礎認證測試
============================================================

============================================================
步驟 1: Docker 容器連線測試
============================================================
✅ Docker 容器 'nexus_db' 正在運行
ℹ️  正在測試 PostgreSQL 連線...
✅ PostgreSQL 連線成功
✅ pgvector 擴充已安裝

============================================================
步驟 2: 向量資料庫寫入測試
============================================================
ℹ️  正在測試使用 langchain-postgres 寫入向量...
ℹ️  載入 Embedding 模型 (BAAI/bge-m3)...
✅ 成功寫入 3 筆文件到向量資料庫
✅ 資料庫中確認有 3 筆向量記錄

============================================================
步驟 3: 檢索準確度測試
============================================================
✅ 檢索到 2 筆結果
✅ 關鍵字匹配率: 2/3 (67%)

============================================================
認證測試總結
============================================================
docker_connection          : ✅ 通過
vector_write              : ✅ 通過
retrieval_accuracy        : ✅ 通過

🎉 所有測試通過！RAG 基礎認證完成。
```

---

## ⚠️ 常見問題排除

### 問題 1: Docker 容器未運行

**錯誤訊息**: `Docker 容器 'nexus_db' 未運行`

**解決方法**:
```bash
docker-compose up -d db
docker ps | grep nexus_db  # 確認狀態
```

---

### 問題 2: PostgreSQL 連線失敗

**錯誤訊息**: `PostgreSQL 連線失敗: connection refused`

**解決方法**:
1. 確認容器正在運行: `docker ps`
2. 檢查連線資訊是否正確（預設: `postgres:postgres@localhost:5432/nexus`）
3. 檢查防火牆設定

---

### 問題 3: pgvector 擴充未安裝

**錯誤訊息**: `pgvector 擴充未安裝`

**解決方法**:
測試腳本會自動安裝，如果失敗，可以手動執行：
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

### 問題 4: Embedding 模型載入失敗

**錯誤訊息**: `OSError: Can't load tokenizer`

**解決方法**:
1. 確認網路連線（首次下載模型需要網路）
2. 檢查磁碟空間
3. 如果持續失敗，可以改用較小的模型：
   ```python
   embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
   ```

---

### 問題 5: 缺少套件

**錯誤訊息**: `ImportError: No module named 'langchain_postgres'`

**解決方法**:
```bash
pip install langchain-postgres sentence-transformers psycopg2-binary
```

---

## 📝 下一步

完成基礎認證後，您可以：

1. **進行 RAG 壓力測試**：上傳複雜合約，測試切分與回答品質
2. **整合到 Streamlit UI**：修改 `app.py` 使用 pgvector 後端
3. **優化檢索策略**：實作混合檢索（Dense + Sparse）

---

## 🔗 相關檔案

- `test_rag_basic.py` - 自動化測試腳本
- `PHASE_1_AUDIT_REPORT.md` - 專案盤點報告
- `retrieval.py` - 目前的檢索模組（使用 Chroma/Naive）
- `app/retrieval/engine.py` - 使用 pgvector 的檢索模組（未使用）
