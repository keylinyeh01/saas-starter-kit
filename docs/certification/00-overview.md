## 認證系統概覽（Certification Suite）

這個 repo 的「產品完整度」用 **10 階段嚴格認證**來控管，每一階段都會包含：

- **Gherkin `.feature`**：可讀、可教學、可審核的 DSL 規格
- **可執行測試**：以 pytest 驅動，遵循 TDD（先寫規格/測試，再補實作）
- **階段報告**：列出通過項、風險、缺口、下一步

### 怎麼跑

```bash
pytest -q
```

預設會排除：
- `@pytest.mark.wip`（尚未完成的規格/測試）
- `@pytest.mark.slow`（長時間、需要外部資源的測試）

### 為什麼自己寫 Gherkin runner？

Phase 1 先用 `certification/gherkin.py` 實作最小可用的 runner，避免因為安裝外部 BDD 套件（`pytest-bdd/behave`）卡住環境。
後續若要換成 `pytest-bdd`，我們可以保留 `.feature` 不動，只替換 runner/step binding。

