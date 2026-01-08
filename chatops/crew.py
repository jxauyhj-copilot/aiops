from crewai import Crew, Task, Process
from .agents import ChatOpsAgents
from .intent_classifier import IntentClassifier, Intent

class ChatOpsCrew:
    def __init__(self):
        agents = ChatOpsAgents()
        self.knowledge_agent = agents.knowledge_retriever_agent()
        self.data_agent = agents.data_analyst_agent()
        self.responder_agent = agents.responder_agent()
        self.intent_classifier = IntentClassifier()

    def run(self, user_question: str, chat_history: str = ""):
        """
        Backward-compatible entry point. Uses smart routing.

        Args:
            user_question: User's query
            chat_history: Optional conversation history

        Returns:
            Agent response
        """
        return self.run_with_routing(user_question, chat_history)

    def run_with_routing(self, user_question: str, chat_history: str = ""):
        """
        Main entry point with smart routing.

        Args:
            user_question: User's query
            chat_history: Optional conversation history

        Returns:
            Agent response
        """
        # Step 1: Classify intent
        intent = self._classify_intent(user_question, chat_history)

        # Step 2: Route to appropriate flow
        if intent == Intent.KNOWLEDGE:
            return self._knowledge_only_flow(user_question, chat_history)
        elif intent == Intent.DATA:
            return self._data_only_flow(user_question, chat_history)
        elif intent == Intent.GENERAL:
            return self._general_flow(user_question, chat_history)
        else:  # HYBRID or fallback
            return self._hybrid_flow(user_question, chat_history)

    def _classify_intent(self, query: str, chat_history: str) -> Intent:
        """Classify query intent"""
        return self.intent_classifier.classify(query, chat_history)

    def _knowledge_only_flow(self, user_question: str, chat_history: str):
        """
        Optimized flow for knowledge-only queries.
        Skips data agent entirely.

        Args:
            user_question: User's query
            chat_history: Optional conversation history

        Returns:
            Agent response
        """
        task_retrieve_knowledge = Task(
            description=f"Search the knowledge base for information to answer this question: {user_question}",
            agent=self.knowledge_agent,
            expected_output="Relevant text chunks from documentation with their sources."
        )

        task_synthesize = Task(
            description=f"""Answer the user's question: '{user_question}' using the knowledge base information provided.

            Context from previous conversation:
            {chat_history}

            Instructions:
            1. Use ONLY the information from the Knowledge Base search results.
            2. You MUST cite the source (e.g., 'According to [Source Name]...').
            3. Provide a clear, helpful response.""",
            agent=self.responder_agent,
            context=[task_retrieve_knowledge],
            expected_output="A final natural language response to the user with clear source citations."
        )

        crew = Crew(
            agents=[self.knowledge_agent, self.responder_agent],
            tasks=[task_retrieve_knowledge, task_synthesize],
            verbose=True,
            process=Process.sequential
        )

        result = crew.kickoff()
        return result

    def _data_only_flow(self, user_question: str, chat_history: str):
        """
        Optimized flow for data-only queries.
        Skips knowledge base search.

        Args:
            user_question: User's query
            chat_history: Optional conversation history

        Returns:
            Agent response
        """
        task_fetch_data = Task(
            description=f"Fetch real-time data for: '{user_question}'. Query the appropriate tools to get current metrics or status.",
            agent=self.data_agent,
            expected_output="JSON data of requested metrics."
        )

        task_synthesize = Task(
            description=f"""Answer the user's question: '{user_question}' using the real-time data provided.

            Context from previous conversation:
            {chat_history}

            Instructions:
            1. Use ONLY the real-time data from the Data Analyst.
            2. Mention that this is live system data.
            3. Provide a clear, helpful response.""",
            agent=self.responder_agent,
            context=[task_fetch_data],
            expected_output="A final natural language response to the user with clear data attribution."
        )

        crew = Crew(
            agents=[self.data_agent, self.responder_agent],
            tasks=[task_fetch_data, task_synthesize],
            verbose=True,
            process=Process.sequential
        )

        result = crew.kickoff()
        return result

    def _general_flow(self, user_question: str, chat_history: str):
        """
        Optimized flow for general queries.
        Uses only responder agent (no tool calls).

        Args:
            user_question: User's query
            chat_history: Optional conversation history

        Returns:
            Agent response
        """
        task_respond = Task(
            description=f"""Provide a helpful response to the user's question: '{user_question}'

            Context from previous conversation:
            {chat_history}

            Instructions:
            1. This is a general query that doesn't require knowledge base or real-time data.
            2. Provide a friendly, helpful conversational response.
            3. Use your general knowledge to assist the user.""",
            agent=self.responder_agent,
            expected_output="A helpful natural language response to the user."
        )

        crew = Crew(
            agents=[self.responder_agent],
            tasks=[task_respond],
            verbose=False,  # Less verbose for simple queries
            process=Process.sequential
        )

        result = crew.kickoff()
        return result

    def _hybrid_flow(self, user_question: str, chat_history: str):
        """
        Full hybrid flow for complex queries.
        Uses all three agents (original behavior).

        Args:
            user_question: User's query
            chat_history: Optional conversation history

        Returns:
            Agent response
        """
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
