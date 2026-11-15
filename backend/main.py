from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.documents import router as documents_router
from api.chat import router as chat_router
from vectorstore.store import load_vector_store
from api.workspaces import router as workspaces_router

@asynccontextmanager
async def lifespan(app: FastAPI):

    load_vector_store()

    yield


app = FastAPI(
    title="InterviewPrep RAG API",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(workspaces_router)


@app.get("/")
def root():
    return {
        "message": "InterviewPrep RAG API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }