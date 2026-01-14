"""
模型微調訓練器。

使用 PEFT (Parameter-Efficient Fine-Tuning) 技術進行模型微調。
支援 LoRA 和 QLoRA 兩種微調方式。
"""

from __future__ import annotations

import os
from typing import Optional, Literal
from pathlib import Path

try:
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        Trainer,
        DataCollatorForLanguageModeling
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from datasets import Dataset
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class FineTuningTrainer:
    """
    開源模型微調訓練器。
    
    支援的模型：
    - Llama 3 (meta-llama/Llama-3-8b)
    - Mistral (mistralai/Mistral-7B-v0.1)
    - Qwen (Qwen/Qwen2.5-7B)
    
    微調技術：
    - LoRA (Low-Rank Adaptation)
    - QLoRA (Quantized LoRA)
    """
    
    def __init__(
        self,
        base_model: str = "Qwen/Qwen2.5-7B",
        use_quantization: bool = False,
        quantization_bits: int = 4,
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.1,
        output_dir: str = "./models/finetuned"
    ):
        """
        Args:
            base_model: 基礎模型名稱（HuggingFace model ID）
            use_quantization: 是否使用量化（QLoRA）
            quantization_bits: 量化位數（4 或 8）
            lora_r: LoRA rank
            lora_alpha: LoRA alpha
            lora_dropout: LoRA dropout
            output_dir: 輸出目錄
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "transformers, peft, datasets 套件未安裝。"
                "請執行: pip install transformers peft datasets bitsandbytes"
            )
        
        self.base_model = base_model
        self.use_quantization = use_quantization
        self.quantization_bits = quantization_bits
        self.lora_r = lora_r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        self.output_dir = output_dir
        
        self.model = None
        self.tokenizer = None
        self.peft_model = None
        
        os.makedirs(output_dir, exist_ok=True)
    
    def load_model(self):
        """載入基礎模型和 tokenizer"""
        print(f"正在載入模型: {self.base_model}")
        
        # 載入 tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 載入模型
        if self.use_quantization:
            from transformers import BitsAndBytesConfig
            
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=(self.quantization_bits == 4),
                load_in_8bit=(self.quantization_bits == 8),
                bnb_4bit_compute_dtype="float16",
                bnb_4bit_use_double_quant=True,
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model,
                quantization_config=quantization_config,
                device_map="auto",
                trust_remote_code=True
            )
            
            # 準備模型進行量化訓練
            self.model = prepare_model_for_kbit_training(self.model)
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model,
                device_map="auto",
                trust_remote_code=True
            )
        
        print("模型載入完成")
    
    def setup_lora(self):
        """設定 LoRA 配置"""
        lora_config = LoraConfig(
            r=self.lora_r,
            lora_alpha=self.lora_alpha,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
            lora_dropout=self.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        self.peft_model = get_peft_model(self.model, lora_config)
        self.peft_model.print_trainable_parameters()
    
    def prepare_dataset(
        self,
        examples: list,
        max_length: int = 2048,
        format_fn: Optional[callable] = None
    ) -> Dataset:
        """
        準備訓練資料集。
        
        Args:
            examples: 訓練範例列表（TrainingExample 或字串）
            max_length: 最大序列長度
            format_fn: 格式化函數（可選）
        """
        from datasets import Dataset
        
        # 如果提供了格式化函數，使用它
        if format_fn:
            texts = [format_fn(ex) for ex in examples]
        else:
            # 預設：假設 examples 是字串列表
            texts = [str(ex) for ex in examples]
        
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=max_length,
                padding="max_length"
            )
        
        dataset = Dataset.from_dict({"text": texts})
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=["text"]
        )
        
        return tokenized_dataset
    
    def train(
        self,
        train_dataset: Dataset,
        num_epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 2e-4,
        warmup_steps: int = 100,
        save_steps: int = 500,
        logging_steps: int = 10
    ):
        """
        執行訓練。
        
        Args:
            train_dataset: 訓練資料集
            num_epochs: 訓練輪數
            batch_size: 批次大小
            learning_rate: 學習率
            warmup_steps: Warmup 步數
            save_steps: 儲存間隔步數
            logging_steps: 日誌間隔步數
        """
        if self.peft_model is None:
            self.setup_lora()
        
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            logging_steps=logging_steps,
            save_steps=save_steps,
            save_total_limit=3,
            fp16=True,
            push_to_hub=False,
            report_to="none"
        )
        
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        trainer = Trainer(
            model=self.peft_model,
            args=training_args,
            train_dataset=train_dataset,
            data_collator=data_collator
        )
        
        print("開始訓練...")
        trainer.train()
        
        # 儲存模型
        trainer.save_model()
        self.tokenizer.save_pretrained(self.output_dir)
        print(f"模型已儲存至: {self.output_dir}")
    
    def save_model(self, path: Optional[str] = None):
        """儲存微調後的模型"""
        save_path = path or self.output_dir
        if self.peft_model:
            self.peft_model.save_pretrained(save_path)
        if self.tokenizer:
            self.tokenizer.save_pretrained(save_path)
        print(f"模型已儲存至: {save_path}")
