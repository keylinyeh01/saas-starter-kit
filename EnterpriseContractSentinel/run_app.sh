#!/bin/bash

# --- 修正開始：加入 Homebrew 路徑 (針對 Mac M1/M2/M3/M4) ---
export PATH="$PATH:/opt/homebrew/bin"
# -------------------------------------------------------

# 1. 確保腳本在正確的目錄執行
cd "$(dirname "$0")"

echo "=========================================="
echo "🕵️‍♂️ 正在啟動企業合約守門員..."
echo "=========================================="

# 2. 檢查是否已經安裝了 Ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ 錯誤: 找不到 Ollama。請確認 '/opt/homebrew/bin' 在你的 PATH 中。"
    exit 1
fi

# 3. 啟動 Ollama 服務 (如果還沒跑)
if ! pgrep -x "ollama" > /dev/null; then
    echo "⚙️ 正在啟動 Ollama 服務..."
    ollama serve &
    # 等待幾秒讓服務完全啟動
    sleep 5
else
    echo "✅ Ollama 服務已在運行中。"
fi

# 4. 啟動 Streamlit 網頁介面
echo "🚀 正在開啟網頁介面..."
echo "請稍候，瀏覽器將自動開啟..."
echo "------------------------------------------"

# 啟動網頁
streamlit run app.py