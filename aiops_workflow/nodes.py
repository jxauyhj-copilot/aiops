from .state import AgentState
import random
import json

# Mock Agents/Nodes

def metric_agent(state: AgentState) -> AgentState:
    """Analyzes metrics related to the alert."""
    print(f"--- Metric Agent Processing Alert: {state['alert_type']} ---")
    # Mock logic: fetch metrics
    state['metrics_data'] = {
        "cpu_usage": "95%",
        "memory_usage": "80%",
        "latency_p99": "500ms"
    }
    return state

def log_agent(state: AgentState) -> AgentState:
    """Fetches logs around the time of the alert."""
    print("--- Log Agent Fetching Logs ---")
    # Mock logic
    state['logs_data'] = [
        "Error: Connection timeout to DB",
        "Warning: High latency detected in API Gateway"
    ]
    return state

def change_agent(state: AgentState) -> AgentState:
    """Checks for recent deployments or config changes."""
    print("--- Change Agent Checking History ---")
    # Mock logic
    state['recent_changes'] = [
        "Deployment #1234: Update RiskEngine (20 mins ago)",
        "Config Change: Increased connection pool size"
    ]
    return state

def rca_agent(state: AgentState) -> AgentState:
    """Synthesizes data to find Root Cause."""
    print("--- RCA Agent Analyzing ---")
    
    metrics = state.get('metrics_data')
    logs = state.get('logs_data')
    changes = state.get('recent_changes')
    
    # Simple mock logic
    rca = f"Potential Root Cause: High CPU and Latency correlated with Deployment #1234. Logs indicate DB timeouts."
    suggestion = "Rollback Deployment #1234 immediately."
    
    state['rca_analysis'] = rca
    state['suggested_action'] = suggestion
    return state

def human_approval_node(state: AgentState) -> AgentState:
    """Simulates human approval (in a real app, this would pause/wait)."""
    print("--- Waiting for Human Approval ---")
    print(f"Suggestion: {state['suggested_action']}")
    
    # For demo purposes, we'll simulate approval if not already set
    if state.get('human_approval') is None:
        # In a real UI, we would interrupt here. 
        # For this skeleton, we assume 'True' or handle it in the runner.
        pass 
    
    return state

def execution_agent(state: AgentState) -> AgentState:
    """Executes the action if approved."""
    if state.get('human_approval'):
        print(f"--- Executing: {state['suggested_action']} ---")
        state['final_report'] = f"Action '{state['suggested_action']}' executed successfully. System recovering."
    else:
        print("--- Action Rejected by Human ---")
        state['final_report'] = "Action rejected. Escalating to manual investigation."
    
    return state
