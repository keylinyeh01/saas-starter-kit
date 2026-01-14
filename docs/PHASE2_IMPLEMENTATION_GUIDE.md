# 階段二功能實作指南

**日期**: 2026-01-14  
**狀態**: ✅ 已完成實作

---

## 📋 功能概述

階段二包含兩個核心功能模組：

1. **開源模型微調服務** (Fine-Tuning as a Service)
2. **多代理工作流自動化** (AI Agent Workflow Automation)

---

## 🔧 1. 開源模型微調服務

### 模組結構

```
app/finetuning/
├── __init__.py          # 模組初始化
├── dataset.py           # 資料集處理器
└── trainer.py           # 微調訓練器
```

### 主要功能

#### `LegalDatasetProcessor`
- 支援多種資料格式（JSONL、JSON）
- 從合約文件創建訓練範例
- 格式化為不同模型格式（Llama、Mistral）

#### `FineTuningTrainer`
- 使用 PEFT/LoRA/QLoRA 進行參數高效微調
- 支援量化訓練（節省記憶體）
- 支援多種開源模型（Llama 3、Mistral、Qwen）

### 使用範例

#### 1. 準備訓練資料

創建 JSONL 格式的訓練資料 (`data/legal/train.jsonl`):

```jsonl
{"instruction": "你是一位專業的合約審查 AI 律師。", "input": "請分析以下合約條款：付款期限為 30 天", "output": "根據合約條款，付款期限設定為 30 天，逾期將收取滯納金。"}
{"instruction": "你是一位專業的合約審查 AI 律師。", "input": "請分析以下合約條款：保證人門檻為 30%", "output": "根據合約條款，保證人門檻設定為 30%，若超過此比例需重新審核。"}
```

#### 2. 執行微調

```bash
# 基本微調（不使用量化）
python examples/finetune_legal_model.py \
    --model Qwen/Qwen2.5-7B \
    --data data/legal/train.jsonl \
    --output ./models/finetuned_legal \
    --epochs 3 \
    --batch-size 4

# 使用 QLoRA 量化（節省記憶體）
python examples/finetune_legal_model.py \
    --model Qwen/Qwen2.5-7B \
    --data data/legal/train.jsonl \
    --output ./models/finetuned_legal \
    --epochs 3 \
    --batch-size 4 \
    --use-quantization \
    --quantization-bits 4
```

#### 3. 程式化使用

```python
from app.finetuning import FineTuningTrainer, LegalDatasetProcessor

# 載入資料集
processor = LegalDatasetProcessor()
examples = processor.load_from_jsonl("data/legal/train.jsonl")

# 初始化訓練器
trainer = FineTuningTrainer(
    base_model="Qwen/Qwen2.5-7B",
    use_quantization=True,
    output_dir="./models/finetuned_legal"
)

# 載入模型並設定 LoRA
trainer.load_model()
trainer.setup_lora()

# 準備資料集
formatted_examples = [processor.format_for_llama(ex) for ex in examples]
train_dataset = trainer.prepare_dataset(formatted_examples)

# 開始訓練
trainer.train(
    train_dataset=train_dataset,
    num_epochs=3,
    batch_size=4
)
```

### 依賴套件

```bash
pip install transformers peft datasets accelerate bitsandbytes torch
```

---

## 🤖 2. 多代理工作流自動化

### 模組結構

```
app/agents/
├── __init__.py          # 模組初始化
└── workflow.py          # 工作流實作
```

### 主要功能

#### `AgentWorkflow`
- 多代理工作流基類
- 支援 CrewAI 和 AutoGen 兩種框架
- 提供代理創建、任務定義、工作流執行功能

#### `InvoiceMatchingWorkflow`
- 自動發票比對工作流
- 包含三個代理：
  1. **發票提取代理**: 從發票文件中提取關鍵資訊
  2. **合約比對代理**: 將發票資訊與合約條款比對
  3. **驗證代理**: 驗證比對結果並生成報告

### 使用範例

#### 1. 使用 CrewAI 框架

```bash
python examples/invoice_matching_workflow.py \
    --invoice invoice.txt \
    --contract contract.txt \
    --framework crewai \
    --llm-backend ollama \
    --model qwen2.5:14b
```

#### 2. 使用 AutoGen 框架

```bash
python examples/invoice_matching_workflow.py \
    --invoice invoice.txt \
    --contract contract.txt \
    --framework autogen \
    --llm-backend ollama \
    --model qwen2.5:14b
```

#### 3. 程式化使用

```python
from app.agents import InvoiceMatchingWorkflow, AgentFramework

# 讀取文件
invoice_text = Path("invoice.txt").read_text()
contract_text = Path("contract.txt").read_text()

# 初始化工作流（使用 CrewAI）
workflow = InvoiceMatchingWorkflow(
    framework=AgentFramework.CREWAI,
    llm_backend="ollama",
    model_name="qwen2.5:14b"
)

# 執行比對
result = workflow.match_invoice(invoice_text, contract_text)

# 檢查結果
if result.success:
    print("比對成功！")
    print(f"結果: {result.output}")
    for step in result.steps:
        print(f"步驟: {step['step']}, 狀態: {step['status']}")
else:
    print(f"比對失敗: {result.error}")
```

#### 4. 自訂工作流

```python
from app.agents import AgentWorkflow, AgentFramework, AgentTask

# 創建自訂工作流
workflow = AgentWorkflow(
    framework=AgentFramework.CREWAI,
    llm_backend="ollama"
)

# 創建代理
researcher = workflow.create_agent(
    role="研究員",
    goal="研究合約條款",
    backstory="你是一位專業的研究員..."
)

writer = workflow.create_agent(
    role="寫作專家",
    goal="撰寫分析報告",
    backstory="你是一位專業的寫作專家..."
)

# 創建任務
research_task = workflow.create_task(
    description="研究合約中的付款條款",
    agent=researcher,
    expected_output="付款條款分析報告"
)

write_task = workflow.create_task(
    description="根據研究結果撰寫報告",
    agent=writer,
    expected_output="完整的分析報告"
)

# 執行工作流
result = workflow.execute([research_task, write_task])
```

### 依賴套件

```bash
# CrewAI
pip install crewai

# AutoGen
pip install pyautogen
```

---

## 📊 功能對比

| 功能 | 微調服務 | 多代理工作流 |
| :--- | :--- | :--- |
| **主要用途** | 針對特定領域訓練模型 | 自動化複雜任務流程 |
| **技術棧** | PEFT/LoRA/QLoRA | CrewAI/AutoGen |
| **輸入** | 訓練資料集 | 任務描述 + 文件 |
| **輸出** | 微調後的模型 | 工作流執行結果 |
| **適用場景** | 法律領域模型優化 | 發票比對、合約審查等 |

---

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 準備環境變數

```bash
# 如果使用 Ollama
export OLLAMA_BASE_URL=http://localhost:11434

# 如果使用 OpenAI
export OPENAI_API_KEY=your_api_key
```

### 3. 執行範例

**微調範例**:
```bash
# 準備訓練資料
mkdir -p data/legal
# 創建 train.jsonl 檔案（參考上面的格式）

# 執行微調
python examples/finetune_legal_model.py \
    --model Qwen/Qwen2.5-7B \
    --data data/legal/train.jsonl \
    --use-quantization
```

**工作流範例**:
```bash
# 準備測試文件
echo "發票內容..." > invoice.txt
echo "合約內容..." > contract.txt

# 執行比對
python examples/invoice_matching_workflow.py \
    --invoice invoice.txt \
    --contract contract.txt \
    --framework crewai
```

---

## 📝 注意事項

### 微調服務

1. **記憶體需求**: 
   - 不使用量化：需要 16GB+ GPU 記憶體（7B 模型）
   - 使用 QLoRA (4-bit)：需要 6-8GB GPU 記憶體

2. **訓練時間**:
   - 取決於資料集大小和模型大小
   - 建議先在小資料集上測試

3. **模型選擇**:
   - Llama 3: 需要 HuggingFace 授權
   - Qwen: 開源友好
   - Mistral: 商業使用需注意授權

### 多代理工作流

1. **LLM 後端**:
   - Ollama: 需要本地安裝 Ollama 並下載模型
   - OpenAI: 需要 API Key

2. **框架選擇**:
   - CrewAI: 更適合複雜工作流，有內建工具
   - AutoGen: 更靈活，適合研究用途

3. **執行時間**:
   - 取決於任務複雜度和 LLM 響應時間
   - 建議設定適當的超時時間

---

## 🔗 相關文件

- `PHASE_1_AUDIT_REPORT.md`: 專案功能盤點報告
- `examples/finetune_legal_model.py`: 微調範例腳本
- `examples/invoice_matching_workflow.py`: 工作流範例腳本

---

**最後更新**: 2026-01-14
