from EnterpriseContractSentinel.ingestion import load_document

def test_docx_loading():
    file_path = "sample_rule.docx"
    
    # 呼叫我們剛升級的函數
    content = load_document(file_path)
    
    if content:
        print("\n📄 讀取到的內容預覽:")
        print("-" * 30)
        print(content[:200]) # 只印出前200個字
        print("-" * 30)
        print("🎉 測試成功！你的系統現在看得懂 Word 檔了！")
    else:
        print("🔴 測試失敗，請檢查檔案路徑或套件安裝。")

if __name__ == "__main__":
    test_docx_loading()