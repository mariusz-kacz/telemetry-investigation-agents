from pathlib import Path

from pydantic import BaseModel


class AzureEvaluationConfig(BaseModel):
    endpoint: str
    deployment_name: str
    eval_data_root: Path
