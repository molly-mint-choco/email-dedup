from app.infrastructure.database import Database
from app.infrastructure.repo import EmailRepository
from app.domain.enum import Action, Resource

class AuditRecorder:
    def __init__(self) -> None:
        self.db = Database()
        