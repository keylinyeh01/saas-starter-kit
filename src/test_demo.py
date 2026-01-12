import pytest
pytest.skip("WIP: 需要把 src/main.py 拆成可測的 DI 架構，且避免外部依賴", allow_module_level=True)

from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from src.main import app, get_vector_store

client = TestClient(app)

# 1. 建立一個 Mock 的 Vector Store
mock_vector_store = MagicMock()

# 2. 強制替換 FastAPI 的相依注入 (Dependency Injection)
# 這會讓 API 在跑測試時，不去執行真的 get_vector_store，而是改用我們的 mock
app.dependency_overrides[get_vector_store] = lambda: mock_vector_store

def test_ingest_document():
    payload = {
        "content": "本公司允許每週五進行遠端工作，但必須在早上 9 點前登入 Slack。",
        "metadata": {"source": "hr_policy_v1"}
    }
    
    # 執行測試
    response = client.post("/ingest", json=payload)
    
    # 驗證結果
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # 驗證 vector_store.add_documents 是否真的有被呼叫
    mock_vector_store.add_documents.assert_called_once()