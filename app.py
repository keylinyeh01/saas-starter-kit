# --- 修正後的 app.py 開頭 import 區 ---
import os
import json
from datetime import datetime
import streamlit as st
import PyPDF2
from docx import Document as DocxDocument
from typing import List

# 因為檔案都在同一層了，直接這樣寫最穩：
from retrieval import VectorStoreManager
from generation import ContractAnalyst

# ------------------------------------

# --- 1. 核心工具：讀取與解析 ---

def extract_text_from_file(uploaded_file):
    """讀取檔案並回傳文字，增加基礎除錯資訊"""
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = DocxDocument(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        st.error(f"❌ 檔案讀取失敗: {e}")
        return ""
    
    # TDD 檢查點：確保真的有讀到東西
    if len(text.strip()) == 0:
        st.error("⚠️ 警告：檔案讀取後內容為空！請檢查 PDF 是否為純圖片。")
    return text


def split_text_fallback(text: str, *, chunk_size: int, chunk_overlap: int) -> List[str]:
    """
    Fallback chunker (no external deps).

    Strategy:
    - First split by blank lines (paragraphs)
    - Then pack paragraphs into chunks up to `chunk_size`
    - Add a simple character overlap between chunks
    """
    raw = (text or "").strip()
    if not raw:
        return []

    paras = [p.strip() for p in raw.split("\n\n") if p.strip()]
    chunks: List[str] = []
    buf = ""

    for p in paras:
        if not buf:
            buf = p
            continue

        if len(buf) + 2 + len(p) <= chunk_size:
            buf = buf + "\n\n" + p
        else:
            chunks.append(buf)
            buf = p

    if buf:
        chunks.append(buf)

    if chunk_overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped: List[str] = []
    prev_tail = ""
    for i, c in enumerate(chunks):
        if i == 0:
            overlapped.append(c)
            prev_tail = c[-chunk_overlap:]
            continue
        overlapped.append(prev_tail + "\n" + c)
        prev_tail = c[-chunk_overlap:]
    return overlapped


def extract_keyword_evidence(raw_text: str, query: str, *, max_snippets: int = 4) -> List[str]:
    """
    Keyword-based evidence extraction (fallback safety net).
    
    IMPORTANT: This function uses NO hardcoded keywords. It dynamically extracts
    keywords from the query itself, making it suitable for global random companies
    and random documents.
    
    This intentionally bypasses vector search to avoid "答非所問" when:
    - the vector index misses a clause
    - the clause uses different wording
    
    Strategy:
    - Extract meaningful tokens from the query (words, numbers, CJK characters)
    - Search for these tokens in the raw text
    - Return paragraphs containing the most matches
    """
    text = (raw_text or "").strip()
    q = (query or "").strip()
    if not text or not q:
        return []

    # Line/paragraph level scan (docx often comes as single-newline paragraphs)
    # Keep both: split on blank lines first; if that yields 1 giant block, fall back to lines.
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paras) <= 1:
        paras = [p.strip() for p in text.split("\n") if p.strip()]

    # DYNAMIC keyword extraction from query (NO hardcoded keywords)
    # Extract all meaningful tokens from the query
    import re
    
    # Extract words (alphanumeric sequences, including numbers and percentages)
    query_words = set(re.findall(r'\b[a-z0-9%\-]+\b', q.lower()))
    
    # Extract CJK characters and bigrams
    cjk_chars = re.findall(r'[\u4e00-\u9fff]', q)
    for ch in cjk_chars:
        query_words.add(ch)
    # Add CJK bigrams for better matching
    for i in range(len(cjk_chars) - 1):
        query_words.add(cjk_chars[i] + cjk_chars[i + 1])
    
    # Extract numbers and percentages (e.g., "30%", "60 days", "1000")
    numbers = re.findall(r'\d+(?:\.\d+)?%?', q)
    for num in numbers:
        query_words.add(num.lower())
    
    # Remove very short tokens (single characters, unless CJK)
    keywords = {w for w in query_words if len(w) >= 2 or (len(w) == 1 and re.match(r'[\u4e00-\u9fff]', w))}
    
    if not keywords:
        return []

    # Score paragraphs by keyword matches
    scored: List[tuple[int, int]] = []
    for i, p in enumerate(paras):
        pl = p.lower()
        # Count keyword matches (weight longer keywords more)
        score = sum(2 if len(k) >= 2 else 1 for k in keywords if k in pl)
        if score > 0:
            scored.append((score, i))

    if not scored:
        return []

    # Pick top indices and include neighbors to preserve clause continuity.
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = []
    for _score, idx in scored[:max_snippets]:
        for j in [idx - 2, idx - 1, idx, idx + 1, idx + 2]:
            if 0 <= j < len(paras):
                picked.append(j)
    # stable unique
    uniq: List[int] = []
    seen_i = set()
    for j in picked:
        if j not in seen_i:
            uniq.append(j)
            seen_i.add(j)
    uniq.sort()

    snippets: List[str] = []
    for j in uniq:
        s = paras[j].strip()
        if s:
            # keep snippet bounded
            snippets.append(s[:1200])
    return snippets[: max_snippets * 5]

def parse_report(text):
    """
    強固型解析器：容忍格式誤差 (Fail-Safe Mode)
    如果 AI 沒按格式寫，直接把全文當作「現況」顯示，確保使用者看得到東西。
    """
    # 1. 初始化預設值 (Default Fallback)
    result = {
        "現況": text if text else "⚠️ AI 未產生文字，請檢查終端機日誌。", 
        "風險": "請參閱證據原文", 
        "建議": "請諮詢專業意見"
    }
    
    # 2. 定義標籤
    tag_status = "[現況]"
    tag_risk = "[風險]"
    tag_suggestion = "[建議]"
    
    # 3. 嘗試解析 (Try Parsing)
    try:
        if tag_status in text and tag_risk in text and tag_suggestion in text:
            # 移除冒號與多餘空白，確保乾淨分割
            # 使用 split 的技巧來鎖定內容
            parts = text.split(tag_risk)
            s_part = parts[0].split(tag_status)[1].strip(": \n")
            
            parts2 = parts[1].split(tag_suggestion)
            r_part = parts2[0].strip(": \n")
            g_part = parts2[1].strip(": \n")
            
            # 只有當解析出內容不為空時，才覆蓋預設值
            if s_part: result["現況"] = s_part
            if r_part: result["風險"] = r_part
            if g_part: result["建議"] = g_part
    except Exception as e:
        # 如果解析過程炸了，至少我們還有預設值 (result["現況"] = text)
        print(f"解析錯誤: {e}") # 這裡可以留給後端看 Log
        
    return result

# --- 2. 系統初始化 ---

st.set_page_config(page_title="企業合約守門員", page_icon="🛡️", layout="wide")
st.title("🛡️ 企業合約守門員 (TDD 驗證版)")

# --- DEMO 可靠性：明確顯示目前 LLM / VectorStore backend，避免誤用 dummy ---
llm_backend = os.getenv("ECS_LLM_BACKEND", "dummy")
vs_backend = os.getenv("ECS_VECTORSTORE_BACKEND", "naive")
with st.sidebar:
    st.caption("⚙️ DEMO Backend 狀態")
    st.code(
        f"ECS_LLM_BACKEND={llm_backend}\n"
        f"ECS_OLLAMA_MODEL={os.getenv('ECS_OLLAMA_MODEL', '')}\n"
        f"ECS_VECTORSTORE_BACKEND={vs_backend}"
    )

# 使用 session_state 來管理核心引擎，方便我們強制重置
if "engine" not in st.session_state:
    with st.spinner("⚙️ 正在啟動 AI 核心..."):
        st.session_state.engine = {
            "vector_store": VectorStoreManager(),
            "analyst": ContractAnalyst()
        }

vector_store = st.session_state.engine["vector_store"]
analyst = st.session_state.engine["analyst"]

# --- 3. 側邊欄：文件控制中心 ---

with st.sidebar:
    st.header("📂 文件控制")
    
    # A. 強制重置按鈕 (解決幻覺的關鍵)
    if st.button("🔄 清除所有記憶 (重置系統)"):
        st.cache_resource.clear()
        st.session_state.clear()
        st.rerun() # 重新整理網頁

    # B. 上傳區
    uploaded_file = st.file_uploader("上傳合約 (PDF/DOCX)", type=["pdf", "docx"])
    
    if uploaded_file:
        st.success(f"已載入: {uploaded_file.name}")
        
        # C. 索引觸發
        if st.button("🚀 開始索引 (讀取文件)"):
            with st.spinner("正在建立向量索引..."):
                raw_text = extract_text_from_file(uploaded_file)
                
                # TDD 驗證 1: 顯示讀到的字數，確認不是 0
                st.info(f"📊 讀取字數: {len(raw_text)} 字")
                
                if raw_text:
                    # 增加 Chunk Size 以確保條文完整性
                    chunk_size = 600
                    chunk_overlap = 100

                    # DEMO/強固性：避免 import-time 牽動 transformers/torch
                    try:
                        from langchain_text_splitters import RecursiveCharacterTextSplitter

                        text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                        )
                        chunks = text_splitter.split_text(raw_text)
                    except Exception:
                        chunks = split_text_fallback(
                            raw_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
                        )
                    
                    # 關鍵：加入前先清除舊索引 (如果 VectorStore 有這功能最好，沒有則依賴重置)
                    # vector_store.clear() # 如果你的 class 有這個方法請取消註解
                    vector_store.add_documents(chunks)
                    
                    st.success(f"✅ 索引完成！共切分 {len(chunks)} 個區塊")
                    st.session_state.file_processed = True
                    # 保留全文，給「關鍵字證據」保命（避免向量檢索 miss）
                    st.session_state.raw_text = raw_text
                else:
                    st.error("無法處理空文件。")

        # D. TDD 除錯視窗 (預覽內容)
        with st.expander("👀 預覽讀取到的內容 (除錯用)"):
             if 'raw_text' in locals() and raw_text:
                 st.caption(raw_text[:500] + "...")

# --- 4. 對話區域 ---

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "你好！請上傳文件並點擊「開始索引」，我才能為您分析。"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- 5. 提問與分析邏輯 ---

if user_query := st.chat_input("請輸入問題，例如：保證人的門檻是多少？"):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.write(user_query)

    with st.chat_message("assistant"):
        # 檢查是否已索引
        if not st.session_state.get("file_processed"):
            st.warning("⚠️ 請先在側邊欄上傳文件並點擊「開始索引」按鈕！")
            response_content = "請先索引文件。"
        else:
            # A. 檢索 (Retrieval)
            with st.status("🔍 檢索合約證據中...", expanded=False) as status:
                # 這裡把 k 設大一點，避免漏掉
                results = vector_store.search(user_query, k=6)
                vector_context = "\n\n".join([doc.page_content for doc in results])

                # Demo safety net: keyword evidence from full text
                keyword_snippets = extract_keyword_evidence(
                    st.session_state.get("raw_text", ""), user_query, max_snippets=4
                )
                keyword_context = "\n\n".join(keyword_snippets)

                # Merge contexts (avoid empty / keep vector first)
                # For demo accuracy: prioritize keyword evidence when present (penalty clauses are often lexical).
                if keyword_context.strip():
                    context_text = "\n\n".join([c for c in [keyword_context, vector_context] if c.strip()])
                else:
                    context_text = vector_context
                status.update(label="✅ 檢索完成", state="complete")

            # TDD 驗證 2: 如果檢索不到東西，直接在這裡擋下來
            if not context_text.strip():
                st.error("❌ 系統在文件中找不到相關片段。請確認文件內容是否正確讀取。")
                response_content = "找不到相關資料。"
            else:
                # 顯示 evidence 來源（讓 demo 更可信）
                with st.expander("🔎 本次用到的證據來源（向量檢索 + 關鍵字保命）", expanded=False):
                    st.markdown("**向量檢索（top-k）**")
                    st.code(vector_context or "(空)")
                    st.markdown("**關鍵字命中（全文掃描）**")
                    st.code(keyword_context or "(空)")

                # B. 生成 (Generation)
                # 請確認你的 analyze 參數順序是 (query, context)
                ai_result = analyst.analyze(user_query, context_text)
                response_content = ai_result["content"]
                
                if ai_result.get("status") == "REPORT":
                    # 顯示紅綠燈
                    if ai_result.get("risk") == "HIGH_RISK":
                        st.error("### 🔴 高風險判定")
                    else:
                        st.success("### 🟢 合規判定")
                    
                    # 顯示分頁報告
                    report = parse_report(response_content)
                    t1, t2, t3, t4 = st.tabs(["📋 現況", "⚠️ 風險", "💡 建議", "📄 證據原文(Debug)"])
                    
                    with t1: st.info(report["現況"])
                    with t2: st.warning(report["風險"])
                    with t3: st.success(report["建議"])
                    with t4: 
                        st.markdown("**AI 看到的證據片段：**")
                        st.code(context_text) # 使用 code block 確保格式清晰

                    # --- 匯出（DEMO/交付超重要）：一鍵下載 Markdown / JSON ---
                    st.divider()
                    st.subheader("📤 匯出本次分析（可交付）")

                    now = datetime.now().strftime("%Y%m%d-%H%M%S")
                    export_md = (
                        f"# 合約分析報告\n\n"
                        f"- 時間：{now}\n"
                        f"- 問題：{user_query}\n"
                        f"- 風險：{ai_result.get('risk')}\n\n"
                        f"## 現況\n{report['現況']}\n\n"
                        f"## 風險\n{report['風險']}\n\n"
                        f"## 建議\n{report['建議']}\n\n"
                        f"## 證據片段\n```\n{context_text}\n```\n"
                    )

                    export_json = {
                        "timestamp": now,
                        "question": user_query,
                        "status": ai_result.get("status"),
                        "risk": ai_result.get("risk"),
                        "report": report,
                        "evidence": context_text,
                    }

                    c1, c2 = st.columns(2)
                    with c1:
                        st.download_button(
                            label="⬇️ 下載 Markdown 報告",
                            data=export_md,
                            file_name=f"contract-report-{now}.md",
                            mime="text/markdown",
                        )
                    with c2:
                        st.download_button(
                            label="⬇️ 下載 JSON（系統對接用）",
                            data=json.dumps(export_json, ensure_ascii=False, indent=2),
                            file_name=f"contract-report-{now}.json",
                            mime="application/json",
                        )
                else:
                    st.write(response_content)

    st.session_state.messages.append({"role": "assistant", "content": response_content})