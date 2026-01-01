
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from chatops.agents import ChatOpsAgents

print("Instantiating ChatOpsAgents...")
try:
    agents = ChatOpsAgents()
    print(f"LLM Base URL: {getattr(agents.llm, 'base_url', 'N/A')}")
    print(f"LLM Model: {getattr(agents.llm, 'model_name', getattr(agents.llm, 'model', 'N/A'))}")
    
    print("Invoking LLM...")
    if hasattr(agents.llm, 'call'):
        response = agents.llm.call("Hello")
        print("Response received:")
        print(response)
    else:
        response = agents.llm.invoke("Hello")
        print("Response received:")
        print(response.content)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
