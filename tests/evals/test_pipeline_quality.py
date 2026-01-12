import pytest

# Note: This file is intentionally WIP.
# It is excluded by default via pytest.ini (marker: wip/slow).

@pytest.mark.slow
@pytest.mark.wip
def test_rag_pipeline_quality_metrics():
    pytest.skip("WIP: 之後會用 RAGAS / golden set 做品質閾值驗證", allow_module_level=False)