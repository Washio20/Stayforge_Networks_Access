from fastapi import FastAPI

from documents import load_master_doc
from router import router

app = FastAPI(
    title="Stayforge Networks Access API",
    redoc_url="/docs",
    docs_url="/docs/swagger",
    version="1.1.0",
    description=load_master_doc(),
)

app.include_router(router)
