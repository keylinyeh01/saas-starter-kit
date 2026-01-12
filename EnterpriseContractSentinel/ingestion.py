"""
Ingestion utilities.

Phase 1 constraint:
- Avoid importing heavyweight optional deps at import time (langchain -> transformers/torch).
- Keep the function usable even when optional loaders aren't installed.
"""

import os

def load_document(file_path):
    """
    全能文件讀取器：根據副檔名自動選擇對應的讀取工具
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    text = ""
    
    try:
        print(f"🔍 正在解析檔案: {file_path} (格式: {file_ext})")
        
        if file_ext == ".pdf":
            from langchain_community.document_loaders import PyPDFLoader

            loader = PyPDFLoader(file_path)
            pages = loader.load()
            text = "".join([p.page_content for p in pages])
            
        elif file_ext == ".docx":
            from langchain_community.document_loaders import Docx2txtLoader

            loader = Docx2txtLoader(file_path)
            pages = loader.load()
            text = "".join([p.page_content for p in pages])
            
        elif file_ext in [".xlsx", ".xls"]:
            # Excel 比較特殊，我們通常希望把每一列讀成文字
            # 這裡簡單處理，實際商業案可能需要更細緻的 CSV 轉換
            import pandas as pd
            df = pd.read_excel(file_path)
            text = df.to_string()
            
        elif file_ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                
        else:
            print(f"⚠️ 尚未支援此格式: {file_ext}")
            return None

        print(f"✅ 解析完成！共讀取了 {len(text)} 個字元。")
        return text

    except Exception as e:
        print(f"🔴 讀取失敗: {e}")
        return None

# 如果直接執行此檔案，進行簡單測試
if __name__ == "__main__":
    # 你可以自己放一個 docx 檔案來測試
    print("請由 test_ingestion.py 或 setup_database.py 呼叫使用。")