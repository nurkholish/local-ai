import logging

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

from local_ai.application.rag.chunker import chunk_text

log = logging.getLogger(__name__)
router = APIRouter()


class UploadOut(BaseModel):
    doc_id: str
    chunks: int


@router.post("/v1/documents", response_model=UploadOut)
async def upload_document(request: Request, file: UploadFile = File(...)):
    try:
        content = (await file.read()).decode("utf-8", errors="ignore")
        doc_id = file.filename or "unknown"
        chunks = chunk_text(content, chunk_size=500, overlap=50)
        texts = [c.text for c in chunks]

        store = request.app.state.vector_store
        embedder = request.app.state.embedder
        if not store or not embedder:
            raise HTTPException(503, "RAG not available")

        embeddings = await embedder.embed(texts)
        await store.insert(doc_id, texts, embeddings, {"filename": doc_id})
        return UploadOut(doc_id=doc_id, chunks=len(chunks))
    except HTTPException:
        raise
    except Exception as e:
        log.exception("upload failed")
        raise HTTPException(500, str(e)) from e