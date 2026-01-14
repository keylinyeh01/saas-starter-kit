"""
多代理工作流自動化模組。

實作複雜任務自動化，如自動發票比對、合約審查等工作流。
"""

from __future__ import annotations

import os
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class AgentFramework(Enum):
    """支援的代理框架"""
    CREWAI = "crewai"
    AUTOGEN = "autogen"


@dataclass
class AgentTask:
    """代理任務定義"""
    name: str
    description: str
    expected_output: str
    agent_role: str
    tools: List[str] | None = None


@dataclass
class WorkflowResult:
    """工作流執行結果"""
    success: bool
    output: Any
    steps: List[Dict[str, Any]]
    error: str | None = None


class AgentWorkflow:
    """
    多代理工作流基類。
    
    支援 CrewAI 和 AutoGen 兩種框架。
    """
    
    def __init__(
        self,
        framework: AgentFramework = AgentFramework.CREWAI,
        llm_backend: str = "ollama",
        model_name: str = "qwen2.5:14b"
    ):
        """
        Args:
            framework: 使用的代理框架
            llm_backend: LLM 後端（ollama, openai, etc.）
            model_name: 模型名稱
        """
        self.framework = framework
        self.llm_backend = llm_backend
        self.model_name = model_name
        self.crew = None
        self.agents = []
        
    def _init_crewai(self):
        """初始化 CrewAI"""
        try:
            from crewai import Agent, Task, Crew, LLM
            CREWAI_AVAILABLE = True
        except ImportError:
            CREWAI_AVAILABLE = False
            raise ImportError(
                "CrewAI 未安裝。請執行: pip install crewai"
            )
        
        # 設定 LLM
        if self.llm_backend == "ollama":
            llm = LLM(
                model=f"ollama/{self.model_name}",
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            )
        elif self.llm_backend == "openai":
            llm = LLM(model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
        else:
            llm = LLM(model=self.model_name)
        
        return llm
    
    def _init_autogen(self):
        """初始化 AutoGen"""
        try:
            import autogen
            AUTOGEN_AVAILABLE = True
        except ImportError:
            AUTOGEN_AVAILABLE = False
            raise ImportError(
                "AutoGen 未安裝。請執行: pip install pyautogen"
            )
        
        # 設定 LLM 配置
        if self.llm_backend == "ollama":
            config_list = [{
                "model": self.model_name,
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                "api_type": "open_ai",
                "api_key": "ollama"
            }]
        elif self.llm_backend == "openai":
            config_list = [{
                "model": "gpt-4",
                "api_key": os.getenv("OPENAI_API_KEY")
            }]
        else:
            config_list = [{"model": self.model_name}]
        
        return config_list
    
    def create_agent(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: List[Callable] | None = None
    ):
        """
        創建代理。
        
        Args:
            role: 代理角色
            goal: 代理目標
            backstory: 代理背景故事
            tools: 代理工具列表
        """
        if self.framework == AgentFramework.CREWAI:
            from crewai import Agent
            
            agent = Agent(
                role=role,
                goal=goal,
                backstory=backstory,
                tools=tools or [],
                verbose=True,
                allow_delegation=False
            )
            self.agents.append(agent)
            return agent
        
        elif self.framework == AgentFramework.AUTOGEN:
            import autogen
            
            config_list = self._init_autogen()
            
            agent = autogen.AssistantAgent(
                name=role,
                system_message=f"{backstory}\n\n目標: {goal}",
                llm_config={"config_list": config_list}
            )
            self.agents.append(agent)
            return agent
    
    def create_task(
        self,
        description: str,
        agent: Any,
        expected_output: str
    ):
        """
        創建任務。
        
        Args:
            description: 任務描述
            agent: 執行任務的代理
            expected_output: 預期輸出
        """
        if self.framework == AgentFramework.CREWAI:
            from crewai import Task
            
            return Task(
                description=description,
                agent=agent,
                expected_output=expected_output
            )
        
        elif self.framework == AgentFramework.AUTOGEN:
            # AutoGen 使用不同的任務模式
            return {
                "description": description,
                "agent": agent,
                "expected_output": expected_output
            }
    
    def execute(self, tasks: List[Any]) -> WorkflowResult:
        """
        執行工作流。
        
        Args:
            tasks: 任務列表
        """
        steps = []
        
        try:
            if self.framework == AgentFramework.CREWAI:
                from crewai import Crew
                
                llm = self._init_crewai()
                crew = Crew(
                    agents=self.agents,
                    tasks=tasks,
                    verbose=True,
                    process="sequential"
                )
                
                result = crew.kickoff()
                steps.append({
                    "step": "crew_execution",
                    "status": "success",
                    "output": str(result)
                })
                
                return WorkflowResult(
                    success=True,
                    output=result,
                    steps=steps
                )
            
            elif self.framework == AgentFramework.AUTOGEN:
                import autogen
                
                config_list = self._init_autogen()
                
                # AutoGen 使用不同的執行模式
                # 這裡簡化為順序執行
                final_output = None
                for i, task in enumerate(tasks):
                    step_result = task["agent"].generate_reply(
                        messages=[{"role": "user", "content": task["description"]}]
                    )
                    steps.append({
                        "step": f"task_{i+1}",
                        "status": "success",
                        "output": step_result
                    })
                    final_output = step_result
                
                return WorkflowResult(
                    success=True,
                    output=final_output,
                    steps=steps
                )
        
        except Exception as e:
            steps.append({
                "step": "execution",
                "status": "error",
                "error": str(e)
            })
            return WorkflowResult(
                success=False,
                output=None,
                steps=steps,
                error=str(e)
            )


class InvoiceMatchingWorkflow(AgentWorkflow):
    """
    自動發票比對工作流。
    
    實作複雜的發票比對任務：
    1. 發票提取代理：從發票文件中提取關鍵資訊
    2. 合約比對代理：將發票資訊與合約條款比對
    3. 驗證代理：驗證比對結果並生成報告
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_agents()
    
    def _setup_agents(self):
        """設定發票比對相關代理"""
        
        # 1. 發票提取代理
        invoice_extractor = self.create_agent(
            role="發票資訊提取專家",
            goal="從發票文件中準確提取所有關鍵資訊，包括金額、日期、供應商資訊等",
            backstory="你是一位經驗豐富的財務分析師，專門處理各種格式的發票文件。"
        )
        
        # 2. 合約比對代理
        contract_matcher = self.create_agent(
            role="合約條款比對專家",
            goal="將發票資訊與合約條款進行比對，確認是否符合合約約定",
            backstory="你是一位專業的合約審查律師，擅長比對文件並找出不一致之處。"
        )
        
        # 3. 驗證代理
        validator = self.create_agent(
            role="驗證與報告專家",
            goal="驗證比對結果的準確性，並生成清晰的驗證報告",
            backstory="你是一位嚴謹的審計專家，確保所有比對結果準確無誤。"
        )
    
    def match_invoice(
        self,
        invoice_text: str,
        contract_text: str
    ) -> WorkflowResult:
        """
        執行發票比對工作流。
        
        Args:
            invoice_text: 發票文字內容
            contract_text: 合約文字內容
        """
        # 創建任務
        tasks = []
        
        if self.framework == AgentFramework.CREWAI:
            from crewai import Task
            
            # 任務 1: 提取發票資訊
            extract_task = Task(
                description=f"請從以下發票內容中提取關鍵資訊：\n{invoice_text}",
                agent=self.agents[0],
                expected_output="結構化的發票資訊（JSON 格式），包含金額、日期、供應商等"
            )
            
            # 任務 2: 比對合約條款
            match_task = Task(
                description=f"請將提取的發票資訊與以下合約條款進行比對：\n{contract_text}",
                agent=self.agents[1],
                expected_output="比對結果，標註符合或不符合的項目"
            )
            
            # 任務 3: 生成驗證報告
            validate_task = Task(
                description="請驗證比對結果並生成最終報告",
                agent=self.agents[2],
                expected_output="完整的驗證報告，包含比對摘要、風險評估和建議"
            )
            
            tasks = [extract_task, match_task, validate_task]
        
        elif self.framework == AgentFramework.AUTOGEN:
            # AutoGen 任務格式
            tasks = [
                self.create_task(
                    description=f"請從以下發票內容中提取關鍵資訊：\n{invoice_text}",
                    agent=self.agents[0],
                    expected_output="結構化的發票資訊"
                ),
                self.create_task(
                    description=f"請將提取的發票資訊與以下合約條款進行比對：\n{contract_text}",
                    agent=self.agents[1],
                    expected_output="比對結果"
                ),
                self.create_task(
                    description="請驗證比對結果並生成最終報告",
                    agent=self.agents[2],
                    expected_output="完整的驗證報告"
                )
            ]
        
        # 執行工作流
        return self.execute(tasks)
