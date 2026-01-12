import os

from certification.gherkin import run_feature, step


@step(r"使用 dummy backends（LLM=dummy, VectorStore=naive）")
def _given_dummy_backends(ctx):
    os.environ["ECS_LLM_BACKEND"] = "dummy"
    os.environ["ECS_VECTORSTORE_BACKEND"] = "naive"
    ctx["docs"] = [
        "準則A [付款條件]: 所有供應商發票應在收到後 60 天內支付 (Net 60)。",
        "準則B [保密期限]: 保密義務在合約終止後應持續有效 5 年。",
    ]
    ctx["question"] = "我們通常多久要把錢給對方？"


@step(r"建立 VectorStoreManager")
def _when_create_vector_store(ctx):
    from EnterpriseContractSentinel.retrieval import VectorStoreManager

    ctx["vs"] = VectorStoreManager(persist_directory="./.tmp_test_chroma_db")


@step(r"我把文件加入向量庫")
def _when_add_docs(ctx):
    ctx["vs"].add_documents(ctx["docs"])


@step(r"我能用問題檢索到相關片段")
def _then_can_retrieve(ctx):
    results = ctx["vs"].search(ctx["question"], k=1)
    assert results, "檢索結果為空"
    top = results[0].page_content
    assert "Net 60" in top, "應該命中付款條件（Net 60）"
    ctx["context"] = top


@step(r"我用 ContractAnalyst 分析問題與片段")
def _when_analyze(ctx):
    from EnterpriseContractSentinel.generation import ContractAnalyst

    analyst = ContractAnalyst()
    ctx["result"] = analyst.analyze(ctx["question"], ctx["context"])


@step(r"回傳必須是結構化報告（含 status/content，且 status 不可為 ERROR）")
def _then_structured_report(ctx):
    res = ctx["result"]
    assert isinstance(res, dict)
    assert "status" in res and "content" in res
    assert res["status"] in {"REPORT", "CONSULT"}, f"unexpected status: {res['status']}"
    assert isinstance(res["content"], str) and res["content"].strip()


def test_phase01_feature():
    run_feature("certification/features/phase01_smoke.feature")

