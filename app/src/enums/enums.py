from enum import Enum

class Role(str,Enum):
    ADMIN= "ADMIN"
    CLIENT= "CLIENT"


class Environment(str, Enum):
    DEV = "dev"
    QA = "qa"
    STAGING = "staging"
    PROD = "prod"
