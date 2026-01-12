from EnterpriseContractSentinel.retrieval import VectorStoreManager


def test_naive_retrieval_cjk_and_synonyms_hit_expected_rules():
    """
    確保 fallback（naive）檢索在中文情境仍具備基本可用性：
    - CJK token/bigram 可命中
    - 少量同義詞擴充可降低「答非所問」
    """
    vs = VectorStoreManager(backend="naive")
    vs.add_documents(
        [
            "準則A [付款條件]: 所有供應商發票應在收到後 60 天內支付 (Net 60)。若逾期未付，將按每日 0.05% 計算滯納金。",
            "準則B [保密期限]: 保密義務在合約終止後應持續有效 5 年。",
            "準則C [管轄法院]: 雙方同意以新加坡國際仲裁中心為第一管轄機構。",
        ]
    )

    cases = [
        ("我們通常多久要把錢給對方？", "準則A [付款條件]"),
        ("逾期付款會怎樣", "準則A [付款條件]"),
        ("保密期限多久", "準則B [保密期限]"),
        ("管轄法院是哪裡", "準則C [管轄法院]"),
    ]

    for query, expected_prefix in cases:
        top = vs.search(query, k=1)[0].page_content
        assert expected_prefix in top, f"query={query} expected={expected_prefix} got={top}"

