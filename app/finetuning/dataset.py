"""
法律領域資料集處理模組。

提供資料集載入、預處理、格式化等功能，用於模型微調。
"""

from __future__ import annotations

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TrainingExample:
    """單一訓練範例"""
    instruction: str
    input_text: str
    output_text: str
    metadata: Dict[str, Any] | None = None


class LegalDatasetProcessor:
    """
    法律領域資料集處理器。
    
    支援多種資料格式：
    - JSONL (每行一個 JSON 物件)
    - JSON (陣列格式)
    - CSV (特定欄位格式)
    """
    
    def __init__(self, data_dir: str = "./data/legal"):
        """
        Args:
            data_dir: 資料集目錄路徑
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def load_from_jsonl(self, file_path: str) -> List[TrainingExample]:
        """
        從 JSONL 檔案載入資料集。
        
        預期格式：
        {"instruction": "...", "input": "...", "output": "...", "metadata": {...}}
        """
        examples = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    examples.append(TrainingExample(
                        instruction=data.get('instruction', ''),
                        input_text=data.get('input', ''),
                        output_text=data.get('output', ''),
                        metadata=data.get('metadata')
                    ))
        return examples
    
    def load_from_json(self, file_path: str) -> List[TrainingExample]:
        """
        從 JSON 陣列檔案載入資料集。
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
        
        examples = []
        for data in data_list:
            examples.append(TrainingExample(
                instruction=data.get('instruction', ''),
                input_text=data.get('input', ''),
                output_text=data.get('output', ''),
                metadata=data.get('metadata')
            ))
        return examples
    
    def create_from_contracts(
        self,
        contracts: List[Dict[str, str]],
        question_template: str = "請分析以下合約條款：{clause}",
        answer_template: str = "根據合約條款，{analysis}"
    ) -> List[TrainingExample]:
        """
        從合約文件創建訓練範例。
        
        Args:
            contracts: 合約列表，每個合約包含 'clause' 和 'analysis' 欄位
            question_template: 問題模板
            answer_template: 答案模板
        """
        examples = []
        for contract in contracts:
            clause = contract.get('clause', '')
            analysis = contract.get('analysis', '')
            
            if clause and analysis:
                examples.append(TrainingExample(
                    instruction="你是一位專業的合約審查 AI 律師。",
                    input_text=question_template.format(clause=clause),
                    output_text=answer_template.format(analysis=analysis),
                    metadata={
                        'source': contract.get('source', 'unknown'),
                        'category': contract.get('category', 'general')
                    }
                ))
        return examples
    
    def save_to_jsonl(self, examples: List[TrainingExample], file_path: str):
        """將訓練範例儲存為 JSONL 格式"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for ex in examples:
                data = {
                    'instruction': ex.instruction,
                    'input': ex.input_text,
                    'output': ex.output_text,
                }
                if ex.metadata:
                    data['metadata'] = ex.metadata
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    def format_for_llama(
        self,
        example: TrainingExample,
        system_prompt: str = "你是一位專業的合約審查 AI 律師。"
    ) -> str:
        """
        格式化為 Llama 3 訓練格式。
        
        格式：
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        {system_prompt}
        <|eot_id|><|start_header_id|>user<|end_header_id|>
        {instruction}
        {input_text}
        <|eot_id|><|start_header_id|>assistant<|end_header_id|>
        {output_text}
        <|eot_id|><|end_of_text|>
        """
        parts = [
            "<|begin_of_text|>",
            "<|start_header_id|>system<|end_header_id|>",
            system_prompt,
            "<|eot_id|>",
            "<|start_header_id|>user<|end_header_id|>",
            example.instruction,
            example.input_text if example.input_text else "",
            "<|eot_id|>",
            "<|start_header_id|>assistant<|end_header_id|>",
            example.output_text,
            "<|eot_id|>",
            "<|end_of_text|>"
        ]
        return "\n".join(parts)
    
    def format_for_mistral(
        self,
        example: TrainingExample,
        system_prompt: str = "你是一位專業的合約審查 AI 律師。"
    ) -> str:
        """
        格式化為 Mistral 訓練格式。
        """
        # Mistral 使用類似格式，但標籤不同
        parts = [
            "<s>",
            "[INST]",
            f"{system_prompt}\n\n{example.instruction}\n\n{example.input_text}",
            "[/INST]",
            example.output_text,
            "</s>"
        ]
        return "\n".join(parts)
