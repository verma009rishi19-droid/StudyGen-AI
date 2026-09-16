def test_create_and_list_documents(client, auth_headers):
    # Create project first
    p_resp = client.post(
        "/api/projects",
        json={"name": "Computer Networks", "subject": "CS", "description": "OSI & TCP/IP models"},
        headers=auth_headers
    )
    project_id = p_resp.json()["id"]

    # Add text document
    sample_text = (
        "The Open Systems Interconnection (OSI) model is a conceptual framework "
        "that describes the functions of a networking system. It characterizes computing "
        "functions into a universal set of rules and requirements in order to support "
        "interoperability between different products and software. The seven layers are "
        "Physical, Data Link, Network, Transport, Session, Presentation, and Application."
    )
    doc_payload = {
        "project_id": project_id,
        "filename": "OSI_Model_Notes.txt",
        "content": sample_text
    }
    doc_resp = client.post("/api/documents", json=doc_payload, headers=auth_headers)
    assert doc_resp.status_code == 201
    doc_data = doc_resp.json()
    assert doc_data["filename"] == "OSI_Model_Notes.txt"
    assert doc_data["char_count"] == len(sample_text)
    doc_id = doc_data["id"]

    # List documents
    list_docs = client.get(f"/api/documents/project/{project_id}", headers=auth_headers)
    assert list_docs.status_code == 200
    docs = list_docs.json()
    assert len(docs) >= 1
    assert any(d["id"] == doc_id for d in docs)

    # Get single document
    get_doc = client.get(f"/api/documents/{doc_id}", headers=auth_headers)
    assert get_doc.status_code == 200
    assert get_doc.json()["id"] == doc_id

def test_upload_pdf_document(client, auth_headers):
    # 1. Create project
    p_resp = client.post(
        "/api/projects",
        json={"name": "Operating Systems", "subject": "CS", "description": "Kernel and Process Scheduling"},
        headers=auth_headers
    )
    project_id = p_resp.json()["id"]

    # 2. Build minimal valid PDF
    pdf_text = "Operating Systems and Kernel Architecture Notes with Process Scheduling"
    content = f"BT /F1 12 Tf 50 250 Td ({pdf_text}) Tj ET"
    stream_len = len(content)
    pdf_str = f"""%PDF-1.4
1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj
2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj
3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>>>> endobj
4 0 obj <</Length {stream_len}>> stream
{content}
endstream endobj
5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000330 00000 n 
trailer <</Size 6 /Root 1 0 R>>
startxref
408
%%EOF"""
    pdf_bytes = pdf_str.encode("latin-1")

    # 3. Upload PDF via multipart form
    files = {"file": ("OS_Chapter1.pdf", pdf_bytes, "application/pdf")}
    data = {"project_id": project_id}

    resp = client.post("/api/documents/upload", data=data, files=files, headers=auth_headers)
    assert resp.status_code == 201
    doc = resp.json()
    assert doc["filename"] == "OS_Chapter1.pdf"
    assert doc["file_type"] == "file/pdf"
    assert "Operating Systems and Kernel Architecture" in doc["content"]
    assert doc["char_count"] > 20
