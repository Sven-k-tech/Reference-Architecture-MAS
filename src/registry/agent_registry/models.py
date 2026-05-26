from datetime import datetime
import uuid
from pydantic import BaseModel


class AgentInfo(BaseModel):
    agent_id:       str       = ""
    name:           str
    capabilities:   list[str] = []
    llm_config:     dict      = {}
    registered_at:  datetime  = None
    last_seen:      datetime  = None
    status:         str       = "healthy"

    def model_post_init(self, __context):
        if not self.agent_id:
            self.agent_id = str(uuid.uuid4())
        if not self.registered_at:
            self.registered_at = datetime.utcnow()
