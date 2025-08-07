import pytest
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.factory import create_app

def test_create_app():
    """
    Tests that the create_app factory returns a FastAPI instance.
    """
    app = create_app()
    assert isinstance(app, FastAPI)

def test_app_includes_rag_router():
    """
    Tests that the create_app factory includes the RAG router
    under the /rag prefix.
    """
    app = create_app()
    client = TestClient(app)

    # This endpoint is defined in the RAG router
    response = client.get("/rag/healthcheck")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_auth_enabled_by_default():
    """
    Tests that authentication is enabled when API_KEY is set.
    """
    # Set a dummy API key in the environment
    os.environ["API_KEY"] = "test-key"

    app = create_app()
    client = TestClient(app)

    # The /rag/ingest/ endpoint requires auth
    # This call is missing the Authorization header
    response = client.post(
        "/rag/ingest/?collection_name=test",
        files={"file": ("test.txt", "content", "text/plain")}
    )

    # Expect unauthorized access.
    assert response.status_code == 401

    # Clean up the environment variable
    del os.environ["API_KEY"]

def test_auth_disabled_with_flag():
    """
    Tests that authentication can be disabled with the no_auth flag,
    even if the API_KEY is set.
    """
    os.environ["API_KEY"] = "test-key"

    app = create_app(no_auth=True)
    client = TestClient(app)

    response = client.post(
        "/rag/ingest/?collection_name=test",
        files={"file": ("test.txt", "content", "text/plain")}
    )

    # Expect the call to succeed because auth is disabled
    assert response.status_code == 200
    assert response.json()["message"] == "'test.txt' を登録しました。"

    del os.environ["API_KEY"]

def test_load_additional_module():
    """
    Tests that the factory can load an additional router module.
    """
    app = create_app(additional_modules=["dummy_module.main"])
    client = TestClient(app)

    response = client.get("/dummy/ping")

    assert response.status_code == 200
    assert response.json() == {"ping": "pong"}
