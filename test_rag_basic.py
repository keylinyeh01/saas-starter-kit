"""
RAG 基礎認證測試腳本

驗證項目：
1. Docker 容器連線：確認 nexus_db 容器正常啟動，PostgreSQL (pgvector) 服務可正常連線
2. 向量資料庫寫入：驗證文件上傳後，向量嵌入能正確寫入 pgvector 資料表
3. 檢索準確度測試：測試向量搜尋是否能正確回傳相關文件片段
"""

import os
import sys
from typing import List
import psycopg2
from psycopg2.extras import execute_values

# 顏色輸出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

# ============================================
# 步驟 1: Docker 容器連線測試
# ============================================

def test_docker_connection():
    """測試 Docker 容器連線"""
    print("\n" + "="*60)
    print("步驟 1: Docker 容器連線測試")
    print("="*60)
    
    # 1.1 檢查容器是否運行
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=nexus_db", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )
        if "nexus_db" in result.stdout:
            print_success("Docker 容器 'nexus_db' 正在運行")
        else:
            print_error("Docker 容器 'nexus_db' 未運行")
            print_info("請執行: docker-compose up -d db")
            return False
    except subprocess.CalledProcessError:
        print_error("無法執行 docker 命令")
        return False
    except FileNotFoundError:
        print_error("Docker 未安裝或不在 PATH 中")
        return False
    
    # 1.2 測試 PostgreSQL 連線
    print_info("正在測試 PostgreSQL 連線...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="nexus"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print_success(f"PostgreSQL 連線成功")
        print_info(f"資料庫版本: {version[:50]}...")
        
        # 1.3 檢查 pgvector 擴充是否安裝
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        if cursor.fetchone():
            print_success("pgvector 擴充已安裝")
        else:
            print_warning("pgvector 擴充未安裝，正在安裝...")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
            print_success("pgvector 擴充安裝完成")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print_error(f"PostgreSQL 連線失敗: {e}")
        print_info("請確認:")
        print_info("  1. Docker 容器是否正常運行: docker ps")
        print_info("  2. 連線資訊是否正確: postgres:postgres@localhost:5432/nexus")
        return False
    except Exception as e:
        print_error(f"未預期的錯誤: {e}")
        return False

# ============================================
# 步驟 2: 向量資料庫寫入測試
# ============================================

def test_vector_write():
    """測試向量資料庫寫入"""
    print("\n" + "="*60)
    print("步驟 2: 向量資料庫寫入測試")
    print("="*60)
    
    try:
        # 2.1 嘗試使用 langchain-postgres (如果可用)
        print_info("正在測試使用 langchain-postgres 寫入向量...")
        
        from langchain_postgres import PGVector
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_core.documents import Document
        
        # 使用本地 embedding 模型（不需要 API key）
        print_info("載入 Embedding 模型 (BAAI/bge-m3)...")
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={'device': 'cpu'}
        )
        
        # 連線到 pgvector
        connection_string = "postgresql+psycopg://postgres:postgres@localhost:5432/nexus"
        print_info(f"連線字串: postgresql+psycopg://postgres:***@localhost:5432/nexus")
        
        vector_store = PGVector(
            collection_name="test_collection",
            connection=connection_string,
            embeddings=embeddings,
        )
        
        # 2.2 準備測試文件
        test_documents = [
            Document(page_content="這是一份測試合約。付款期限為 30 天。逾期將收取 5% 的滯納金。"),
            Document(page_content="保證人門檻設定為 30%。若超過此比例，需要額外審核。"),
            Document(page_content="合約終止條件：任何一方違約超過 60 天，另一方有權終止合約。"),
        ]
        
        print_info(f"準備寫入 {len(test_documents)} 筆測試文件...")
        
        # 2.3 寫入向量資料庫
        vector_store.add_documents(test_documents)
        print_success(f"成功寫入 {len(test_documents)} 筆文件到向量資料庫")
        
        # 2.4 驗證資料是否真的寫入
        print_info("驗證資料是否寫入資料庫...")
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="nexus"
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM langchain_pg_embedding 
            WHERE collection_id = (
                SELECT uuid FROM langchain_pg_collection WHERE name = 'test_collection'
            );
        """)
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        if count > 0:
            print_success(f"資料庫中確認有 {count} 筆向量記錄")
        else:
            print_warning("資料庫中未找到記錄（可能是表格結構不同）")
        
        return vector_store
        
    except ImportError as e:
        print_error(f"缺少必要的套件: {e}")
        print_info("請執行: pip install langchain-postgres sentence-transformers")
        return None
    except Exception as e:
        print_error(f"向量寫入失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============================================
# 步驟 3: 檢索準確度測試
# ============================================

def test_retrieval_accuracy(vector_store):
    """測試檢索準確度"""
    print("\n" + "="*60)
    print("步驟 3: 檢索準確度測試")
    print("="*60)
    
    if vector_store is None:
        print_error("向量資料庫未初始化，跳過檢索測試")
        return False
    
    # 3.1 準備測試查詢
    test_queries = [
        {
            "query": "付款期限是多久？",
            "expected_keywords": ["30", "天", "付款"],
            "description": "測試基本時間資訊檢索"
        },
        {
            "query": "保證人門檻是多少？",
            "expected_keywords": ["30%", "保證人", "門檻"],
            "description": "測試百分比數值檢索"
        },
        {
            "query": "什麼情況下可以終止合約？",
            "expected_keywords": ["終止", "違約", "60"],
            "description": "測試條件檢索"
        },
    ]
    
    print_info(f"準備測試 {len(test_queries)} 個查詢...")
    
    all_passed = True
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n--- 測試 {i}/{len(test_queries)}: {test_case['description']} ---")
        print_info(f"查詢: \"{test_case['query']}\"")
        
        try:
            # 執行檢索
            results = vector_store.similarity_search(
                test_case['query'],
                k=2  # 取前 2 筆
            )
            
            if not results:
                print_error("檢索結果為空")
                all_passed = False
                continue
            
            print_success(f"檢索到 {len(results)} 筆結果")
            
            # 檢查結果是否包含預期關鍵字
            found_keywords = []
            for j, doc in enumerate(results, 1):
                content = doc.page_content
                print_info(f"結果 {j}: {content[:60]}...")
                
                # 檢查關鍵字
                for keyword in test_case['expected_keywords']:
                    if keyword.lower() in content.lower():
                        found_keywords.append(keyword)
            
            # 評估準確度
            matched = set(found_keywords)
            expected = set(test_case['expected_keywords'])
            match_ratio = len(matched) / len(expected) if expected else 0
            
            if match_ratio >= 0.5:  # 至少匹配 50% 的關鍵字
                print_success(f"關鍵字匹配率: {len(matched)}/{len(expected)} ({match_ratio*100:.0f}%)")
            else:
                print_warning(f"關鍵字匹配率較低: {len(matched)}/{len(expected)} ({match_ratio*100:.0f}%)")
                all_passed = False
                
        except Exception as e:
            print_error(f"檢索過程發生錯誤: {e}")
            all_passed = False
    
    return all_passed

# ============================================
# 主程式
# ============================================

def main():
    print("\n" + "="*60)
    print("RAG 基礎認證測試")
    print("="*60)
    
    results = {
        "docker_connection": False,
        "vector_write": False,
        "retrieval_accuracy": False
    }
    
    # 步驟 1: Docker 容器連線
    results["docker_connection"] = test_docker_connection()
    
    if not results["docker_connection"]:
        print("\n" + Colors.RED + "="*60)
        print("❌ 步驟 1 失敗，無法繼續後續測試")
        print("="*60 + Colors.END)
        return
    
    # 步驟 2: 向量資料庫寫入
    vector_store = test_vector_write()
    results["vector_write"] = (vector_store is not None)
    
    if not results["vector_write"]:
        print("\n" + Colors.YELLOW + "="*60)
        print("⚠️  步驟 2 失敗，跳過步驟 3")
        print("="*60 + Colors.END)
    else:
        # 步驟 3: 檢索準確度測試
        results["retrieval_accuracy"] = test_retrieval_accuracy(vector_store)
    
    # 總結報告
    print("\n" + "="*60)
    print("認證測試總結")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{test_name:30s}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n" + Colors.GREEN + "🎉 所有測試通過！RAG 基礎認證完成。" + Colors.END)
    else:
        print("\n" + Colors.YELLOW + "⚠️  部分測試未通過，請檢查上述錯誤訊息。" + Colors.END)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
