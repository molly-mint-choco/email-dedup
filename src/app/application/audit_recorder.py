from app.infrastructure.database import Database
from app.infrastructure.repo import EmailRepository
from app.domain.enum import Action, Resource
from app.domain.data_model import AuditLog
import orjson

class AuditRecorder:
    def __init__(self) -> None:
        self.db = Database()
    
    async def write_async(self, resource: Resource, action: Action, content: str, description: str, actor: str):
        new_audit_log = AuditLog(
            resource = resource.name,
            action = action.name,
            content = orjson.dumps(content),
            description = description,
            actor = actor
        )
        async for session in self.db.get_session_async():
            repo = EmailRepository(session)
            repo.insert_audit_log(new_audit_log)