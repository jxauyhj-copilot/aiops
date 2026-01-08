import os
from dotenv import load_dotenv

# Force load .env from the project root (one directory up from config/)
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

class Settings:
    # Local LLM Settings
    USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "llama3")

    # OpenAI Settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY and USE_LOCAL_LLM:
        # Set dummy key to satisfy CrewAI/LiteLLM validation when using Local LLM
        OPENAI_API_KEY = "NA"
        os.environ["OPENAI_API_KEY"] = "NA"
        
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4-turbo-preview")
    
    # Vector DB Paths
    VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), "../knowledge_base/faiss_index")

    # Mock Data Settings
    SIMULATE_ALERTS = True

    # Session Management
    SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "../sessions")
    MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "50"))
    SESSION_TITLE_MAX_LENGTH = int(os.getenv("SESSION_TITLE_MAX_LENGTH", "50"))

    # Intent Classification
    ROUTING_CONFIDENCE_THRESHOLD = float(os.getenv("ROUTING_CONFIDENCE_THRESHOLD", "0.8"))
    USE_KEYWORD_ROUTING = os.getenv("USE_KEYWORD_ROUTING", "true").lower() == "true"

settings = Settings()
