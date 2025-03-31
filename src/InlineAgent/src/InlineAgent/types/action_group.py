from enum import Enum
from typing import Dict, Literal, Optional
from pydantic import BaseModel


class Executor(Enum):
    RETURN_CONTROL = "RETURN_CONTROL"
    LAMBDA = "LAMBDA"
    INBUILT_TOOL = "INBUILT_TOOL"


class Parameter(BaseModel):
    class Config:
        extra = "forbid"

    type: str
    description: str
    required: bool


class FunctionDefination(BaseModel):
    class Config:
        extra = "forbid"

    name: str
    description: str
    parameters: Dict[str, Parameter]
    requireConfirmation: Literal["ENABLED", "DISABLED"] = "DISABLED"


class S3(BaseModel):
    class Config:
        extra = "forbid"

    s3BucketName: str
    s3ObjectKey: str


class APISchema(BaseModel):
    class Config:
        extra = "forbid"
        arbitrary_types_allowed = True

    payload: Optional[str] = None
    s3: Optional[S3] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.payload is not None and self.s3 is not None:
            raise ValueError("Only one of 'payload' or 's3' should be defined")
        if self.payload is None and self.s3 is None:
            raise ValueError("Either 'payload' or 's3' must be defined")
