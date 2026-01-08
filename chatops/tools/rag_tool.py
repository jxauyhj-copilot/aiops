from crewai.tools import BaseTool
from knowledge_base.retriever import KnowledgeRetriever
from pydantic import BaseModel, Field

class SearchKnowledgeBaseInput(BaseModel):
    search_query: str = Field(..., description="The text string to search for. Example: 'how to deploy'")

class SearchKnowledgeBaseTool(BaseTool):
    name: str = "Search Knowledge Base"
    description: str = "Search the static knowledge base (Wiki, SOPs, Jira) for relevant information."
    args_schema: type[BaseModel] = SearchKnowledgeBaseInput

    def _run(self, search_query: str) -> str:
        try:
            # Handle if search_query is passed as dict (CrewAI sometimes does this)
            if isinstance(search_query, dict):
                if 'search_query' in search_query:
                    search_query = search_query['search_query']
                elif 'description' in search_query:
                    search_query = search_query['description']
                elif 'query' in search_query:
                    search_query = search_query['query']
                else:
                    # Fallback: extract the first string value
                    for v in search_query.values():
                        if isinstance(v, str):
                            search_query = v
                            break

            # Ensure search_query is a string
            search_query = str(search_query) if search_query else ""

            retriever = KnowledgeRetriever()
            results = retriever.search(search_query)
            if not results:
                return "No relevant documents found."
            return "\n\n".join(results)
        except Exception as e:
            return f"Error searching knowledge base: {e}"

search_knowledge_base = SearchKnowledgeBaseTool()
