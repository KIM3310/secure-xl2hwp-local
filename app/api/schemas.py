from typing import Optional

from pydantic import BaseModel, Field


class ProcessPathRequest(BaseModel):
    input_path: str = Field(..., description="Absolute or relative path to xlsx file")
    output_dir: str = Field("examples/output", description="Directory for output artifacts")
    contract_name: str = "default"
    profile_name: str = "default"
    template_name: str = "default"
    template_path: Optional[str] = None


class ProcessResponse(BaseModel):
    success: bool
    outcome: dict
