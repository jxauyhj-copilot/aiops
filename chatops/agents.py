from crewai import Agent, LLM
from .tools.dynamic_data import get_trade_volume, get_system_status, get_match_count
from .tools.rag_tool import search_knowledge_base
from langchain_openai import ChatOpenAI
from config.settings import settings

class ChatOpsAgents:
    def __init__(self):
        if settings.USE_LOCAL_LLM:
            self.llm = LLM(
                model=f"ollama/{settings.OLLAMA_MODEL_NAME}",
                base_url=settings.OLLAMA_BASE_URL
            )
        else:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL_NAME, 
                api_key=settings.OPENAI_API_KEY
            )

    def knowledge_retriever_agent(self):
        return Agent(
            role='Knowledge Specialist',
            goal='Retrieve accurate information from the static knowledge base.',
            backstory='You are an expert in the company\'s documentation, SOPs, and Wiki. You know where to find answers to static questions.',
            tools=[search_knowledge_base],
            llm=self.llm,
            verbose=True
        )

    def data_analyst_agent(self):
        return Agent(
            role='Data Analyst',
            goal='Fetch and interpret real-time system data and metrics.',
            backstory='You have access to all live production metrics. You can query trade volumes, system status, and other dynamic data.',
            tools=[
                get_trade_volume,
                get_system_status,
                get_match_count
            ],
            llm=self.llm,
            verbose=True
        )

    def responder_agent(self):
        return Agent(
            role='ChatOps Responder',
            goal='Synthesize information from knowledge and data agents to provide a comprehensive answer to the user.',
            backstory='You are the interface to the user. You take raw data and documentation chunks and formulate a helpful, human-readable response.',
            llm=self.llm,
            verbose=True
        )
