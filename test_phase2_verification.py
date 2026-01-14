"""
Phase 2 功能認證測試腳本

驗證項目：
1. 開源模型微調服務 (Fine-Tuning Service)
   - 驗證資料處理器 (LegalDatasetProcessor) 邏輯
   - 驗證訓練器 (FineTuningTrainer) 流程 (Mock)
2. 多代理工作流 (Multi-Agent Workflow)
   - 驗證工作流基類 (AgentWorkflow) 邏輯 (Mock)
   - 驗證發票比對工作流 (InvoiceMatchingWorkflow) 結構
"""

import sys
import unittest
from unittest.mock import MagicMock, patch
import json
import os
import shutil

# ==========================================
# 1. Mock 外部重型依賴 (在 import app 之前)
# ==========================================

# Mock transformers & peft & datasets
sys.modules["transformers"] = MagicMock()
sys.modules["peft"] = MagicMock()
sys.modules["datasets"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["bitsandbytes"] = MagicMock()

# Mock crewai & autogen
sys.modules["crewai"] = MagicMock()
sys.modules["autogen"] = MagicMock()

# 設定 Mock 的具體行為，讓 import 不會報錯
sys.modules["transformers"].AutoModelForCausalLM.from_pretrained = MagicMock()
sys.modules["transformers"].AutoTokenizer.from_pretrained = MagicMock()

# ==========================================
# 2. Import 專案模組
# ==========================================

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.finetuning import LegalDatasetProcessor, FineTuningTrainer
from app.agents import AgentWorkflow, InvoiceMatchingWorkflow, AgentFramework

# ==========================================
# 3. 測試類別
# ==========================================

class TestPhase2Features(unittest.TestCase):
    
    def setUp(self):
        self.test_data_dir = "./test_data_tmp"
        os.makedirs(self.test_data_dir, exist_ok=True)
        
    def tearDown(self):
        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)

    # --- 驗證微調服務 ---

    def test_legal_dataset_processor(self):
        """驗證資料處理器邏輯 (真實邏輯)"""
        print("\n正在驗證 LegalDatasetProcessor...")
        processor = LegalDatasetProcessor(data_dir=self.test_data_dir)
        
        # 1. 測試 JSONL 讀寫
        examples = [
            {"instruction": "Inst 1", "input": "In 1", "output": "Out 1"},
            {"instruction": "Inst 2", "input": "In 2", "output": "Out 2"}
        ]
        jsonl_path = os.path.join(self.test_data_dir, "train.jsonl")
        
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for ex in examples:
                f.write(json.dumps(ex) + '\n')
                
        loaded_examples = processor.load_from_jsonl(jsonl_path)
        self.assertEqual(len(loaded_examples), 2)
        self.assertEqual(loaded_examples[0].instruction, "Inst 1")
        print("✅ JSONL 讀寫測試通過")
        
        # 2. 測試 Llama 格式化
        formatted = processor.format_for_llama(loaded_examples[0])
        self.assertIn("<|start_header_id|>user<|end_header_id|>", formatted)
        self.assertIn("Inst 1", formatted)
        print("✅ Llama 格式化測試通過")

    def test_finetuning_trainer_flow(self):
        """驗證微調訓練器流程 (Mock)"""
        print("\n正在驗證 FineTuningTrainer 流程...")
        
        # 初始化訓練器
        trainer = FineTuningTrainer(
            base_model="Test/Model",
            output_dir=self.test_data_dir
        )
        
        # 驗證 load_model 是否正確呼叫 transformers
        trainer.load_model()
        sys.modules["transformers"].AutoTokenizer.from_pretrained.assert_called_with("Test/Model")
        sys.modules["transformers"].AutoModelForCausalLM.from_pretrained.assert_called()
        print("✅ 模型載入流程驗證通過")
        
        # 驗證 setup_lora 是否正確呼叫 peft
        trainer.setup_lora()
        sys.modules["peft"].get_peft_model.assert_called()
        print("✅ LoRA 設定流程驗證通過")

    # --- 驗證多代理工作流 ---

    def test_agent_workflow_initialization(self):
        """驗證代理工作流初始化"""
        print("\n正在驗證 AgentWorkflow...")
        
        # 測試 CrewAI 模式
        workflow = AgentWorkflow(framework=AgentFramework.CREWAI)
        self.assertEqual(workflow.framework, AgentFramework.CREWAI)
        
        # 測試代理創建 (Mock)
        agent = workflow.create_agent("Role", "Goal", "Backstory")
        self.assertTrue(len(workflow.agents) > 0)
        # 驗證是否呼叫了 crewai.Agent
        sys.modules["crewai"].Agent.assert_called() 
        print("✅ CrewAI 代理創建驗證通過")

    def test_invoice_matching_workflow_structure(self):
        """驗證發票比對工作流結構"""
        print("\n正在驗證 InvoiceMatchingWorkflow...")
        
        workflow = InvoiceMatchingWorkflow()
        # 應該自動創建 3 個代理 (Extractor, Matcher, Validator)
        self.assertEqual(len(workflow.agents), 3)
        print("✅ 發票比對代理初始化驗證通過 (3 Agents)")
        
        # 驗證 match_invoice 邏輯流程
        # Mock execute 方法以避免真實執行
        with patch.object(AgentWorkflow, 'execute') as mock_execute:
            mock_execute.return_value = MagicMock(success=True)
            
            workflow.match_invoice("Invoice Text", "Contract Text")
            
            # 驗證是否創建了 3 個任務
            # 由於我們 mock 了 crewai.Task，這裡主要驗證流程是否跑到 execute
            mock_execute.assert_called_once()
            tasks_arg = mock_execute.call_args[0][0]
            self.assertEqual(len(tasks_arg), 3)
            print("✅ 發票比對任務創建流程驗證通過")

if __name__ == '__main__':
    print("="*60)
    print("開始執行 Phase 2 功能認證")
    print("="*60)
    unittest.main(verbosity=2)
