from fastapi import APIRouter, HTTPException, status
from app.application.query_handler import EmailQueryHandler
from typing import List
import uuid

router = APIRouter(prefix="/emails", tags=["Email Queries"])

query_handler = EmailQueryHandler()

@router.get("/document/{file_name}/canonical-id", response_model=uuid.UUID)
async def get_canonical_id_by_document(file_name: str):
    cano_id = await query_handler.get_canonical_id_by_document_async(file_name)
    if not cano_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Document '{file_name}' not found."
        )
    return cano_id

@router.get("/canonical-thread/{cano_id}/documents", response_model=List[str])
async def get_documents_by_canonical_thread(cano_id: uuid.UUID):
    documents = await query_handler.get_documents_by_thread_async(cano_id)
    return documents

@router.get("/canonical-thread/{cano_id}/children", response_model=List[uuid.UUID])
async def get_children_by_cano_id(cano_id: uuid.UUID):
    children = await query_handler.get_child_threads_async(cano_id)
    if not children:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Children not found for given canonical thread: '{cano_id}'."
        )
    return children

@router.get("/canonical-thread/{cano_id}/parent", response_model=uuid.UUID)
async def get_parent_by_cano_id(cano_id: uuid.UUID):
    parent = await query_handler.get_parent_thread_async(cano_id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Parent not found for given canonical thread: '{cano_id}'."
        )
    return parent

@router.get("/canonical-thread/{cano_id}/upstream", response_model=str)
async def get_upstream_chain_by_cano_id(cano_id: uuid.UUID):
    chain = await query_handler.get_hierarchy_async(cano_id)
    return chain