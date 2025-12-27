from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import socket
import json

@dataclass
class KafkaPayload:
    file_name: str
    source_node: str = field(default_factory=socket.gethostname)
    retry_count: int = field(default=0)
    ingested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'KafkaPayload':
        data = json.loads(json_str)
        return cls(**data)