from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import metric_agent, log_agent, change_agent, rca_agent, human_approval_node, execution_agent

def create_aiops_graph():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("metric_agent", metric_agent)
    workflow.add_node("log_agent", log_agent)
    workflow.add_node("change_agent", change_agent)
    workflow.add_node("rca_agent", rca_agent)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("execution_agent", execution_agent)

    # Define Edges
    # Parallel execution of data gathering
    workflow.set_entry_point("metric_agent")
    workflow.add_edge("metric_agent", "log_agent")
    workflow.add_edge("log_agent", "change_agent")
    
    # Then RCA
    workflow.add_edge("change_agent", "rca_agent")
    
    # Then Human Approval
    workflow.add_edge("rca_agent", "human_approval")
    
    # Conditional Edge based on approval
    def check_approval(state):
        if state.get("human_approval"):
            return "execution_agent"
        else:
            return END # Or some other path

    workflow.add_conditional_edges(
        "human_approval",
        check_approval,
        {
            "execution_agent": "execution_agent",
            END: END
        }
    )
    
    workflow.add_edge("execution_agent", END)

    return workflow.compile()
