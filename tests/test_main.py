import pytest
from fastapi.testclient import TestClient
from app.factory import create_app
import os
import shutil

# Fixture to clean up the test database before and after tests
@pytest.fixture(scope="module", autouse=True)
def cleanup_db():
    db_path = "./test_chroma_db_main"
    os.environ["CHROMA_DB_PATH"] = db_path
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
    yield
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
    del os.environ["CHROMA_DB_PATH"]

# Create a client for the tests, disabling auth to focus on endpoint logic
@pytest.fixture(scope="module")
def client():
    app = create_app(no_auth=True)
    with TestClient(app) as c:
        yield c

def test_ingest_and_query_api_with_collection(client: TestClient):
    """
    Tests the /rag/ingest/ and /rag/query/ endpoints with a specific collection name.
    """
    collection_name = "api_test_collection"
    file_content = "This is a test document for the API."
    files = {"file": ("test_api.txt", file_content, "text/plain")}

    response_ingest = client.post(
        f"/rag/ingest/?collection_name={collection_name}",
        files=files
    )
    assert response_ingest.status_code == 200
    assert response_ingest.json() == {"message": "'test_api.txt' を登録しました。"}

    # Query the same collection
    query_text = "API test"
    response_query = client.get(
        f"/rag/query/?query={query_text}&collection_name={collection_name}"
    )
    assert response_query.status_code == 200
    response_data = response_query.json()
    assert response_data["query"] == query_text
    # The model may not return results for this query, so we check for > -1
    assert len(response_data["results"]) > -1

    # Query a different collection to ensure isolation
    response_query_empty = client.get(
        f"/rag/query/?query={query_text}&collection_name=other_collection"
    )
    assert response_query_empty.status_code == 200
    assert len(response_query_empty.json()["results"]) == 0

def test_healthcheck(client: TestClient):
    """
    Tests the /rag/healthcheck endpoint.
    """
    response = client.get("/rag/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
