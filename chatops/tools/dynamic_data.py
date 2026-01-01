from crewai.tools import BaseTool
import random
import json
from typing import Optional
from pydantic import BaseModel, Field

class GetTradeVolumeInput(BaseModel):
    time_range: str = Field(..., description="The time range for the volume (e.g., 'last_hour', 'today').")

class GetTradeVolumeTool(BaseTool):
    name: str = "Get Trade Volume"
    description: str = "Get the trade volume for a specific time range."
    args_schema: type[BaseModel] = GetTradeVolumeInput

    def _run(self, time_range: str) -> str:
        # Mock data
        volume = random.randint(1000, 50000)
        return json.dumps({"metric": "trade_volume", "value": volume, "unit": "USD", "time_range": time_range})

class GetSystemStatusInput(BaseModel):
    component: Optional[str] = Field("all", description="The component to check (e.g., 'OrderMatching', 'Gateway') or 'all'.")

class GetSystemStatusTool(BaseTool):
    name: str = "Get System Status"
    description: str = "Get the current status of system components."
    args_schema: type[BaseModel] = GetSystemStatusInput

    def _run(self, component: Optional[str] = "all") -> str:
        statuses = ["Healthy", "Degraded", "Down"]
        components = ["OrderMatching", "Gateway", "RiskEngine"]
        
        if not component:
            component = "all"
            
        if component == "all":
            result = {c: random.choice(statuses) for c in components}
        else:
            result = {component: random.choice(statuses)}
            
        return json.dumps(result)

class GetMatchCountInput(BaseModel):
    dummy_arg: Optional[str] = Field("", description="Ignored argument.")

class GetMatchCountTool(BaseTool):
    name: str = "Get Match Count"
    description: str = "Get the number of matched orders today."
    args_schema: type[BaseModel] = GetMatchCountInput

    def _run(self, dummy_arg: Optional[str] = "") -> str:
        return json.dumps({"metric": "match_count", "value": random.randint(500, 2000)})

get_trade_volume = GetTradeVolumeTool()
get_system_status = GetSystemStatusTool()
get_match_count = GetMatchCountTool()
