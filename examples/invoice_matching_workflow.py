"""
自動發票比對工作流範例。

使用範例：
    python examples/invoice_matching_workflow.py --invoice invoice.txt --contract contract.txt
"""

import argparse
import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents import InvoiceMatchingWorkflow, AgentFramework


def main():
    parser = argparse.ArgumentParser(description="自動發票比對工作流")
    parser.add_argument(
        "--invoice",
        type=str,
        required=True,
        help="發票文件路徑"
    )
    parser.add_argument(
        "--contract",
        type=str,
        required=True,
        help="合約文件路徑"
    )
    parser.add_argument(
        "--framework",
        type=str,
        default="crewai",
        choices=["crewai", "autogen"],
        help="使用的代理框架"
    )
    parser.add_argument(
        "--llm-backend",
        type=str,
        default="ollama",
        choices=["ollama", "openai"],
        help="LLM 後端"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen2.5:14b",
        help="模型名稱"
    )
    
    args = parser.parse_args()
    
    # 讀取文件
    invoice_text = Path(args.invoice).read_text(encoding='utf-8')
    contract_text = Path(args.contract).read_text(encoding='utf-8')
    
    # 初始化工作流
    framework = AgentFramework.CREWAI if args.framework == "crewai" else AgentFramework.AUTOGEN
    
    workflow = InvoiceMatchingWorkflow(
        framework=framework,
        llm_backend=args.llm_backend,
        model_name=args.model
    )
    
    # 執行比對
    print("開始執行發票比對工作流...")
    result = workflow.match_invoice(invoice_text, contract_text)
    
    # 輸出結果
    if result.success:
        print("\n✅ 工作流執行成功！")
        print("\n執行步驟：")
        for i, step in enumerate(result.steps, 1):
            print(f"\n步驟 {i}:")
            print(f"  狀態: {step.get('status', 'unknown')}")
            if 'output' in step:
                print(f"  輸出: {step['output'][:200]}...")
        
        print(f"\n最終輸出:\n{result.output}")
    else:
        print(f"\n❌ 工作流執行失敗: {result.error}")
        print("\n執行步驟：")
        for i, step in enumerate(result.steps, 1):
            print(f"\n步驟 {i}:")
            print(f"  狀態: {step.get('status', 'unknown')}")
            if 'error' in step:
                print(f"  錯誤: {step['error']}")


if __name__ == "__main__":
    main()
