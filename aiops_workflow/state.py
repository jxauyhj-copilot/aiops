from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    alert_id: str
    alert_type: str
    alert_details: dict
    metrics_data: Optional[dict]
    logs_data: Optional[List[str]]
    recent_changes: Optional[List[str]]
    rca_analysis: Optional[str]
    suggested_action: Optional[str]
    human_approval: Optional[bool]
    final_report: Optional[str]
