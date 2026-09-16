def test_generate_summary_topics_and_paper(client, auth_headers):
    # Setup project & document
    p_resp = client.post(
        "/api/projects",
        json={"name": "Database Systems", "subject": "CS", "description": "ACID and Relational Models"},
        headers=auth_headers
    )
    project_id = p_resp.json()["id"]

    study_material = (
        "Relational database management systems organize data into tables consisting of rows and columns. "
        "Transactions adhere to ACID properties: Atomicity guarantees all-or-nothing execution; "
        "Consistency preserves database invariants; Isolation ensures transactions do not interfere; "
        "Durability guarantees committed data persists even during hardware failures. "
        "Indexing using B-Trees dramatically accelerates query performance for range and point lookups."
    )
    doc_resp = client.post(
        "/api/documents",
        json={"project_id": project_id, "filename": "db_notes.txt", "content": study_material},
        headers=auth_headers
    )
    doc_id = doc_resp.json()["id"]

    # 1. Test Summary Generation
    sum_resp = client.post("/api/summaries/generate", json={"document_id": doc_id}, headers=auth_headers)
    assert sum_resp.status_code == 200
    sum_data = sum_resp.json()
    assert "summary" in sum_data and len(sum_data["summary"]) > 0
    assert "key_concepts" in sum_data and len(sum_data["key_concepts"]) > 0
    assert "important_topics" in sum_data
    assert "quick_revision" in sum_data and len(sum_data["quick_revision"]) > 0

    # 2. Test Topics Generation
    top_resp = client.post("/api/topics/generate", json={"document_id": doc_id}, headers=auth_headers)
    assert top_resp.status_code == 200
    topics = top_resp.json()
    assert isinstance(topics, list)
    assert len(topics) > 0
    first_topic = topics[0]
    assert "topic" in first_topic
    assert "explanation" in first_topic
    assert "importance" in first_topic

    # 3. Test Question Paper Generation
    qp_config = {
        "project_id": project_id,
        "document_id": doc_id,
        "title": "Database Midterm Exam",
        "num_questions": 4,
        "total_marks": 20,
        "difficulty": "Medium",
        "question_type": "Mixed",
        "duration": 45
    }
    qp_resp = client.post("/api/question-papers/generate", json=qp_config, headers=auth_headers)
    assert qp_resp.status_code == 201
    qp_data = qp_resp.json()
    assert qp_data["title"] == "Database Midterm Exam"
    assert len(qp_data["questions"]) == 4
    for q in qp_data["questions"]:
        assert "question_text" in q
        assert "correct_answer" in q
        assert "marks" in q
        assert q["marks"] > 0
