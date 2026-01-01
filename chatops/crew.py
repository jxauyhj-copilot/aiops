from crewai import Crew, Task, Process
from .agents import ChatOpsAgents

class ChatOpsCrew:
    def __init__(self):
        agents = ChatOpsAgents()
        self.knowledge_agent = agents.knowledge_retriever_agent()
        self.data_agent = agents.data_analyst_agent()
        self.responder_agent = agents.responder_agent()

    def run(self, user_question: str, chat_history: str = ""):
        # Define Tasks
        
        # Task 1: Analyze intent and fetch info (Parallelizable ideally, but sequential here for simplicity)
        # We give the question to both agents and let them decide if they can answer.
        
        task_retrieve_knowledge = Task(
            description=f"Search the knowledge base for information related to: '{user_question}'. If the question is purely about real-time data, you might not find anything, which is fine. Always include the 'Source' from the retrieved documents in your output.",
            agent=self.knowledge_agent,
            expected_output="Relevant text chunks from documentation with their sources, or a statement that no info was found."
        )

        task_fetch_data = Task(
            description=f"Check if the question '{user_question}' requires real-time data (metrics, status, volume). If so, query the appropriate tools. If the question is static or does not require real-time data, DO NOT call any tools and simply return 'No data needed'.",
            agent=self.data_agent,
            expected_output="JSON data of requested metrics or a statement that no data was needed."
        )

        task_synthesize = Task(
            description=f"""Combine the information provided by the Knowledge Specialist and Data Analyst to answer the user's question: '{user_question}'. 
            
            Context from previous conversation:
            {chat_history}
            
            Instructions:
            1. Review the outputs from the Knowledge Specialist and Data Analyst.
            2. Determine which information is relevant to the user's question.
            3. IGNORE any data or information that is not directly related to the user's question. For example, if the user asks about "deployment", ignore "trade volume" data.
            4. Construct a natural, helpful response using ONLY the relevant information.
            5. If you used information from the Knowledge Base, you MUST cite the source (e.g., 'According to [Source Name]...').
            6. If the information comes from real-time data, mention that it is live system data.""",
            agent=self.responder_agent,
            context=[task_retrieve_knowledge, task_fetch_data],
            expected_output="A final natural language response to the user with clear source citations where applicable."
        )

        crew = Crew(
            agents=[self.knowledge_agent, self.data_agent, self.responder_agent],
            tasks=[task_retrieve_knowledge, task_fetch_data, task_synthesize],
            verbose=True,
            process=Process.sequential
        )

        result = crew.kickoff()
        return result
