from EnterpriseContractSentinel.app import extract_keyword_evidence


def test_extract_keyword_evidence_finds_late_payment_interest_and_termination():
    """
    TDD: 逾期付款的罰則條款通常是 lexical（interest/prime/terminate/notice）。
    我們要確保「關鍵字保命」在 docx 這種單行段落輸出下也能抓到關鍵句。
    """
    raw_text = "\n".join(
        [
            "10.2 Late Payment. If any Royalties or other amounts due hereunder are not paid when due, interest shall accrue.",
            "The interest rate shall be the prime interest rate published in The Wall Street Journal on the due date plus one percent (1%).",
            "Payment of interest shall not preclude Licensor from exercising any other rights.",
            "11.1 Default. If any payment is overdue for more than sixty (60) days, it shall constitute a default.",
            "11.2 Termination. Licensor may terminate this Agreement upon thirty (30) days' notice unless all outstanding amounts and interest are paid within such period.",
        ]
    )
    q = "逾期付款會怎樣？沒有罰則嗎？"

    snippets = extract_keyword_evidence(raw_text, q, max_snippets=4)
    joined = "\n".join(snippets).lower()

    assert "interest" in joined
    assert "prime" in joined
    assert "terminate" in joined or "termination" in joined
    assert "60" in joined or "sixty" in joined
    assert "30" in joined or "thirty" in joined

