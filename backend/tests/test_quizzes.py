def test_interactive_quiz_evaluation(client, auth_headers):
    # Setup project and question paper
    p_resp = client.post(
        "/api/projects",
        json={"name": "Cybersecurity", "subject": "InfoSec", "description": "Cryptography and Defense"},
        headers=auth_headers
    )
    project_id = p_resp.json()["id"]

    study_material = (
        "Public-key cryptography utilizes asymmetric key pairs consisting of a public key and a private key. "
        "RSA relies on the mathematical difficulty of factoring large composite integers. "
        "Transport Layer Security (TLS) encrypts internet traffic to prevent eavesdropping and tampering."
    )
    doc_resp = client.post(
        "/api/documents",
        json={"project_id": project_id, "filename": "crypto.txt", "content": study_material},
        headers=auth_headers
    )
    doc_id = doc_resp.json()["id"]

    qp_resp = client.post(
        "/api/question-papers/generate",
        json={"project_id": project_id, "document_id": doc_id, "num_questions": 3, "question_type": "MCQ"},
        headers=auth_headers
    )
    paper = qp_resp.json()
    questions = paper["questions"]
    assert len(questions) == 3

    # Answer 2 questions correctly, 1 incorrectly
    answers_payload = [
        {"question_id": questions[0]["id"], "user_answer": questions[0]["correct_answer"]},
        {"question_id": questions[1]["id"], "user_answer": questions[1]["correct_answer"]},
        {"question_id": questions[2]["id"], "user_answer": "Definitely an incorrect answer"}
    ]

    quiz_resp = client.post(
        "/api/quizzes/submit",
        json={"question_paper_id": paper["id"], "answers": answers_payload},
        headers=auth_headers
    )
    assert quiz_resp.status_code == 200
    quiz_data = quiz_resp.json()

    assert quiz_data["total_questions"] == 3
    assert quiz_data["correct_count"] == 2
    assert quiz_data["incorrect_count"] == 1
    assert round(quiz_data["percentage"], 1) == 66.7
    assert len(quiz_data["details"]) == 3
    assert quiz_data["details"][0]["is_correct"] is True
    assert quiz_data["details"][1]["is_correct"] is True
    assert quiz_data["details"][2]["is_correct"] is False
