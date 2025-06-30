from fastapi import FastAPI, HTTPException
from starlette.staticfiles import StaticFiles

app = FastAPI()



@app.get("/backend/health")
def health():
    return {"status": "ok"}

@app.get("/backend/connection")
def connection():
    return {"status": "connected"}

app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")