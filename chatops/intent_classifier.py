"""
Intent Classifier for Smart Query Routing

Implements hybrid classification:
1. Fast keyword-based heuristics (first pass)
2. LLM-based classification for ambiguous queries (fallback)
"""

from enum import Enum
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from config.settings import settings


class Intent(Enum):
    """Query intent types"""
    KNOWLEDGE = "knowledge"  # Query documentation, SOPs, guides
    DATA = "data"            # Real-time metrics, status, live data
    HYBRID = "hybrid"        # Both knowledge and data
    GENERAL = "general"      # Casual chat, explanations without data


class IntentClassifier:
    """Hybrid intent classifier using keyword heuristics + LLM fallback"""

    # Keyword patterns for fast classification
    KNOWLEDGE_KEYWORDS = [
        "how to", "how do i", "deploy", "deployment", "configure", "configuration",
        "architecture", "documentation", "playbook", "sop", "guide", "tutorial",
        "setup", "install", "integration", "pipeline", "workflow", "procedure",
        "manual", "reference", "best practice", "design", "structure"
    ]

    DATA_KEYWORDS = [
        "current", "status", "metric", "volume", "latency", "cpu", "memory",
        "trade", "match count", "health", "performance", "uptime", "throughput",
        "monitor", "alert", "error rate", "response time", "load", "capacity",
        "live", "real-time", "real time", "today", "now", "running"
    ]

    GENERAL_KEYWORDS = [
        "hello", "hi", "hey", "thank", "thanks", "explain", "what is",
        "tell me about", "summarize", "describe", "compare", "difference",
        "why", "can you", "could you", "help me", "meaning", "definition"
    ]

    def __init__(self, llm=None):
        """
        Initialize Intent Classifier

        Args:
            llm: Optional LLM instance for fallback classification
        """
        self.llm = llm or self._create_llm()

    def classify(self, query: str, chat_history: str = "") -> Intent:
        """
        Classify query intent using hybrid approach

        Args:
            query: User query string
            chat_history: Optional chat history context

        Returns:
            Intent enum value
        """
        # Step 1: Try fast keyword-based classification
        if settings.USE_KEYWORD_ROUTING:
            intent = self._keyword_classify(query)
            if intent is not None:
                return intent

        # Step 2: Fall back to LLM classification for ambiguous queries
        return self._llm_classify(query, chat_history)

    def _keyword_classify(self, query: str) -> Optional[Intent]:
        """
        Fast keyword-based classification

        Args:
            query: User query string

        Returns:
            Intent if confident match, None otherwise
        """
        query_lower = query.lower()

        # Count keyword matches
        knowledge_matches = sum(1 for kw in self.KNOWLEDGE_KEYWORDS if kw in query_lower)
        data_matches = sum(1 for kw in self.DATA_KEYWORDS if kw in query_lower)
        general_matches = sum(1 for kw in self.GENERAL_KEYWORDS if kw in query_lower)

        total_matches = knowledge_matches + data_matches + general_matches

        # No keywords matched - needs LLM
        if total_matches == 0:
            return None

        # Calculate confidence
        max_matches = max(knowledge_matches, data_matches, general_matches)
        confidence = max_matches / total_matches

        # Return intent only if confidence exceeds threshold
        if confidence >= settings.ROUTING_CONFIDENCE_THRESHOLD:
            if knowledge_matches == max_matches:
                return Intent.KNOWLEDGE
            elif data_matches == max_matches:
                return Intent.DATA
            elif general_matches == max_matches:
                return Intent.GENERAL

        # Ambiguous - needs LLM classification
        return None

    def _llm_classify(self, query: str, chat_history: str = "") -> Intent:
        """
        LLM-based classification for ambiguous queries

        Args:
            query: User query string
            chat_history: Optional chat history context

        Returns:
            Intent enum value
        """
        classification_prompt = f"""Classify this query into ONE of these categories: KNOWLEDGE, DATA, HYBRID, GENERAL

Query: {query}

Context from conversation:
{chat_history if chat_history else "(New conversation)"}

Classification Rules:
- KNOWLEDGE: Questions about documentation, procedures, deployment guides, configuration, architecture, or how-to instructions
- DATA: Questions about real-time metrics, current status, live system data, performance, or monitoring
- HYBRID: Questions that require BOTH documentation AND current data (e.g., comparing current status to guidelines)
- GENERAL: Casual conversation, greetings, explanations without specific data needs, or general questions

IMPORTANT: Respond with ONLY the classification name (KNOWLEDGE, DATA, HYBRID, or GENERAL). Nothing else."""

        try:
            # Use LLM for classification
            response = self.llm.invoke(classification_prompt)

            # Extract content from response (handles both ChatOpenAI and ChatOllama)
            result = str(response.content).strip().upper() if hasattr(response, 'content') else str(response).strip().upper()

            # Parse response
            if "KNOWLEDGE" in result:
                return Intent.KNOWLEDGE
            elif "DATA" in result:
                return Intent.DATA
            elif "HYBRID" in result:
                return Intent.HYBRID
            elif "GENERAL" in result:
                return Intent.GENERAL
            else:
                # Default to HYBRID if unclear
                return Intent.HYBRID

        except Exception as e:
            # Silent fallback - don't print errors in production
            # Default to HYBRID on error (safest option - runs all agents)
            return Intent.HYBRID

    def _create_llm(self):
        """Create LLM instance for classification"""
        if settings.USE_LOCAL_LLM:
            return ChatOllama(
                model=settings.OLLAMA_MODEL_NAME,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0  # Low temperature for consistent classification
            )
        else:
            return ChatOpenAI(
                model=settings.OPENAI_MODEL_NAME,
                api_key=settings.OPENAI_API_KEY,
                temperature=0  # Low temperature for consistent classification
            )
