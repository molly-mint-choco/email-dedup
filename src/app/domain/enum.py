from enum import Enum

class Resource(Enum):
    DB = "db"
    KAFKA = "kafka"
    EMAIL_QUERY_API = "email_query_api"
    FILE = "file"

class Action(Enum):
    CREATE = "create"
    INSERT = "insert"
    UPDATE = "update"
    PRODUCE = "produce"
    CONSUME = "consume"
    READ = "read"
