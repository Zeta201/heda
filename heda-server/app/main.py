from datetime import datetime
import uuid
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from app.schemas import CreateExperimentRequest, CreateExperimentResponse, RunRequest, RunResponse
from app.db import get_connection, init_db
from app.github import create_repo, protect_main_branch
from app.gitops_init import initialize_gitops_repo
from app.argo import submit_workflow, websocket_stream_workflow_run


app = FastAPI(title="HEDA API")


@app.on_event("startup")
def startup():
    init_db()
    
@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.post("/experiments", response_model=CreateExperimentResponse)
def create_experiment(req: CreateExperimentRequest):
    exp_id = f"exp_{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow().isoformat()

    try:
        repo_url = create_repo(exp_id)
        initialize_gitops_repo(repo_url)
        protect_main_branch(repo_url)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create GitHub repo: {e}",
        )

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO experiments (id, name, status, repo_url, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (exp_id, req.name, "CREATED", repo_url, now),
        )

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}",
        )

    return CreateExperimentResponse(
        experiment_id=exp_id,
        repo_url=repo_url,
    )


@app.post("/run", response_model=RunResponse)
def run_experiment(req: RunRequest):
    try:
        run_id = submit_workflow(
            repo_url=req.repo_url,
            commit_sha=req.commit_sha,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return RunResponse(
        run_id=run_id,
        status="queued",
    )
    

@app.websocket("/ws/workflows/{workflow_run_id}/logs")
async def websocket_workflow_logs(websocket: WebSocket, workflow_run_id: str):
    await websocket_stream_workflow_run(websocket, workflow_run_id)
