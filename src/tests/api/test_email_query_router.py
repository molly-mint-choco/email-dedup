import pytest
from pytest_mock import mocker
from fastapi import FastAPI, status
import uuid
from httpx import AsyncClient, ASGITransport
from app.api.routers.email_query_router import router
from app.api.routers import email_query_router
import pytest_asyncio

MOCK_UUID = uuid.uuid4()
MOCK_FILE_NAME = "doc1234.txt"

app = FastAPI()
app.include_router(router)

@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

@pytest.mark.asyncio
async def test_get_canonical_id_by_document_success(client, mocker):
    # Arrange
    mocker.patch.object(
        email_query_router.query_handler,
        'get_canonical_id_by_document_async',
        new=mocker.AsyncMock(return_value=MOCK_UUID)
    )

    # Act
    response = await client.get(f"/emails/document/{MOCK_FILE_NAME}/canonical-id")
    
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == str(MOCK_UUID)
    
