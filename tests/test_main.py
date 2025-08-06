import pytest
from fastapi.testclient import TestClient
from main import app
import os
import shutil

# Fixture to clean up the test database before and after tests
@pytest.fixture(scope="module", autouse=True)
def cleanup_db():
    db_path = "./test_chroma_db_main"
    # Set the env var for the service to use the test db
    os.environ["CHROMA_DB_PATH"] = db_path
    if os.path.exists(db_path):
        shutil.rmtree(db_path)

    yield

    if os.path.exists(db_path):
        shutil.rmtree(db_path)
    # Unset the env var
    del os.environ["CHROMA_DB_PATH"]

client = TestClient(app)

def test_ingest_and_query_api_with_collection():
    """
    Tests the /ingest/ and /query/ endpoints with a specific collection name.
    This test will fail initially.
    """
    # A dummy token for the auth dependency
    headers = {"Authorization": "Bearer dummytoken"}

    # 1. Ingest a document into a specific collection
    collection_name = "api_test_collection"
    file_content = "This is a test document for the API."
    files = {"file": ("test_api.txt", file_content, "text/plain")}

    # This will fail because the endpoint doesn't take collection_name
    response_ingest = client.post(
        f"/ingest/?collection_name={collection_name}",
        files=files,
        headers=headers
    )
    assert response_ingest.status_code == 200
    assert response_ingest.json() == {"message": "'test_api.txt' を登録しました。"}

    # 2. Query the same collection
    query_text = "API test"
    response_query = client.get(
        f"/query/?query={query_text}&collection_name={collection_name}"
    )

    assert response_query.status_code == 200
    response_data = response_query.json()
    assert response_data["query"] == query_text
    assert len(response_data["results"]) > 0
    result_item = response_data["results"][0]
    assert "test document for the API" in result_item["text"]
    assert "distance" in result_item
    assert isinstance(result_item["distance"], float)

    # 3. Query a different collection to ensure isolation
    response_query_empty = client.get(
        f"/query/?query={query_text}&collection_name=other_collection"
    )
    assert response_query_empty.status_code == 200
    assert len(response_query_empty.json()["results"]) == 0

def test_healthcheck():
    """
    Tests the /healthcheck endpoint.
    """
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
