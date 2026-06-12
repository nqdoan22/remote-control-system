from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, machines, modules

app = FastAPI(title="Remote Control System - Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(machines.router, prefix="/api/machines", tags=["Machines"])
app.include_router(modules.router, prefix="/api/modules", tags=["Modules"])

@app.get("/")
def root():
    return {"message": "Remote Control System API"}
