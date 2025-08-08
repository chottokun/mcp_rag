import pytest
import os
import shutil
from app.rag_service import RAGService

from fpdf import FPDF

# Define a fixture to create and clean up a RAGService instance for tests
@pytest.fixture(scope="module")
def rag_service():
    db_path = "./test_chroma_db"
    # Clean up the test database before and after the test
    if os.path.exists(db_path):
        shutil.rmtree(db_path)

    service = RAGService(db_path=db_path)

    yield service

    # Teardown: clean up the database directory after tests are done
    if os.path.exists(db_path):
        shutil.rmtree(db_path)

@pytest.fixture(scope="module")
def sample_pdf_file():
    """Creates a dummy PDF file for testing and cleans it up afterward."""
    pdf_path = "test_files/sample.pdf"
    if not os.path.exists("test_files"):
        os.makedirs("test_files")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="This is a test PDF document.", ln=True, align='C')
    pdf.output(pdf_path)

    yield pdf_path

    os.remove(pdf_path)


def test_add_and_query_multiple_collections(rag_service: RAGService):
    """
    Tests the ability to add documents to and query from separate, named collections.
    """
    # Document for the 'tech_docs' collection
    tech_doc_content = "This is a document about FastAPI and web development.".encode('utf-8')
    tech_doc_filename = "tech.txt"

    # Document for the 'legal_docs' collection
    legal_doc_content = "This is a document about contract law.".encode('utf-8')
    legal_doc_filename = "legal.txt"

    # Add documents to their respective collections
    rag_service.add_document(tech_doc_content, tech_doc_filename, collection_name="tech_docs")
    rag_service.add_document(legal_doc_content, legal_doc_filename, collection_name="legal_docs")

    # Query the 'tech_docs' collection
    tech_results = rag_service.query_rag("web development", collection_name="tech_docs")

    # Query the 'legal_docs' collection
    legal_results = rag_service.query_rag("contracts", collection_name="legal_docs")

    # Assert that the correct document is found in the 'tech_docs' collection
    assert len(tech_results["results"]) > 0
    assert "FastAPI" in tech_results["results"][0]["text"]
    assert "distance" in tech_results["results"][0]

    # Assert that the correct document is found in the 'legal_docs' collection
    assert len(legal_results["results"]) > 0
    assert "contract law" in legal_results["results"][0]["text"]
    assert "distance" in legal_results["results"][0]

    # Assert that a query to one collection does not return results from the other
    cross_query_results = rag_service.query_rag("contract law", collection_name="tech_docs")
    assert len(cross_query_results["results"]) == 0


def test_delete_document(rag_service: RAGService):
    """
    Tests the ability to delete a document from a collection.
    """
    collection_name = "deletion_test"
    doc_content = "This is a document to be deleted.".encode('utf-8')
    doc_filename = "to_be_deleted.txt"

    # Add a document and verify it's there
    rag_service.add_document(doc_content, doc_filename, collection_name=collection_name)
    results_before_delete = rag_service.query_rag("document to be deleted", collection_name=collection_name)
    assert len(results_before_delete["results"]) > 0
    assert results_before_delete["results"][0]["metadata"]["source"] == doc_filename

    # Delete the document
    rag_service.delete_document(filename=doc_filename, collection_name=collection_name)

    # Verify the document is gone
    results_after_delete = rag_service.query_rag("document to be deleted", collection_name=collection_name)
    assert len(results_after_delete["results"]) == 0


def test_delete_non_existent_document(rag_service: RAGService):
    """
    Tests that attempting to delete a non-existent document does not raise an error.
    """
    collection_name = "deletion_test_non_existent"
    # Ensure the collection is clean for this test
    # Note: The fixture already provides a clean DB, but this makes the test's intent clearer.

    # Attempt to delete a document that was never added
    try:
        rag_service.delete_document(filename="non_existent.txt", collection_name=collection_name)
    except Exception as e:
        pytest.fail(f"Deleting a non-existent document raised an exception: {e}")


def test_add_markdown_file(rag_service: RAGService):
    """
    Tests adding a markdown file to the RAG service.
    """
    collection_name = "markdown_test"
    file_path = "test_files/test.md"
    with open(file_path, "rb") as f:
        content = f.read()

    rag_service.add_document(content, os.path.basename(file_path), collection_name=collection_name)

    # Query the collection
    results = rag_service.query_rag("list item", collection_name=collection_name)
    assert len(results["results"]) > 0
    assert "list item 1" in results["results"][0]["text"]

def test_add_pdf_file(rag_service: RAGService, sample_pdf_file):
    """
    Tests adding a PDF file to the RAG service.
    """
    collection_name = "pdf_test"
    with open(sample_pdf_file, "rb") as f:
        content = f.read()

    rag_service.add_document(content, os.path.basename(sample_pdf_file), collection_name=collection_name)

    # Query the collection
    results = rag_service.query_rag("test PDF", collection_name=collection_name)
    assert len(results["results"]) > 0
    assert "This is a test PDF document." in results["results"][0]["text"]
