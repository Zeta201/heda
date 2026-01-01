from pydantic import BaseModel

class CreateExperimentRequest(BaseModel):
    name: str

class CreateExperimentResponse(BaseModel):
    experiment_id: str
    repo_url: str

class RunRequest(BaseModel):
    repo_url: str
    commit_sha: str


class RunResponse(BaseModel):
    run_id: str
    status: str
