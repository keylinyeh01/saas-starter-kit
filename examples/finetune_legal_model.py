"""
法律領域模型微調範例腳本。

使用範例：
    python examples/finetune_legal_model.py --model Qwen/Qwen2.5-7B --data data/legal/train.jsonl
"""

import argparse
import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.finetuning import FineTuningTrainer, LegalDatasetProcessor


def main():
    parser = argparse.ArgumentParser(description="法律領域模型微調")
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen2.5-7B",
        help="基礎模型名稱（HuggingFace model ID）"
    )
    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="訓練資料路徑（JSONL 或 JSON 格式）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./models/finetuned_legal",
        help="輸出目錄"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="訓練輪數"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="批次大小"
    )
    parser.add_argument(
        "--use-quantization",
        action="store_true",
        help="使用 QLoRA 量化（節省記憶體）"
    )
    parser.add_argument(
        "--quantization-bits",
        type=int,
        default=4,
        choices=[4, 8],
        help="量化位數（4 或 8）"
    )
    
    args = parser.parse_args()
    
    # 1. 載入資料集
    print("正在載入資料集...")
    processor = LegalDatasetProcessor()
    
    data_path = Path(args.data)
    if data_path.suffix == ".jsonl":
        examples = processor.load_from_jsonl(str(data_path))
    elif data_path.suffix == ".json":
        examples = processor.load_from_json(str(data_path))
    else:
        raise ValueError(f"不支援的檔案格式: {data_path.suffix}")
    
    print(f"載入 {len(examples)} 筆訓練範例")
    
    # 2. 初始化訓練器
    print("正在初始化訓練器...")
    trainer = FineTuningTrainer(
        base_model=args.model,
        use_quantization=args.use_quantization,
        quantization_bits=args.quantization_bits,
        output_dir=args.output
    )
    
    # 3. 載入模型
    trainer.load_model()
    trainer.setup_lora()
    
    # 4. 準備資料集
    print("正在準備資料集...")
    # 格式化為 Llama 格式（可根據模型調整）
    formatted_examples = [
        processor.format_for_llama(ex) for ex in examples
    ]
    train_dataset = trainer.prepare_dataset(formatted_examples)
    
    # 5. 開始訓練
    print("開始訓練...")
    trainer.train(
        train_dataset=train_dataset,
        num_epochs=args.epochs,
        batch_size=args.batch_size
    )
    
    print("訓練完成！")
    print(f"微調後的模型已儲存至: {args.output}")


if __name__ == "__main__":
    main()
