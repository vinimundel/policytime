from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from policytime.application.contracts import ProviderUnavailable
from policytime.application.service import AnswerService
from policytime.delivery.web import create_app
from policytime.settings import Settings


@pytest.fixture
def client(service):
    settings = Settings(
        mode="demo", metrics_token=SecretStr("test-token"), requests_per_minute=120, _env_file=None
    )
    with TestClient(create_app(settings, service)) as client:
        yield client


def payload(**changes):
    return {
        "question": "What is my hotel reimbursement limit?",
        "expense_date": "2026-07-15",
        "country": "BR",
        "employment_type": "contractor",
        **changes,
    }


def test_health_readiness_and_schema(client):
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").json()["documents"] == 24
    schema = client.get("/openapi.json").json()
    assert "/api/ask" in schema["paths"]


def test_api_answer_and_citation_contract(client):
    response = client.post("/api/ask", json=payload())
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["status"] == "answered"
    assert "BRL 180" in result["answer"]
    assert all(item["clause_id"] != "lodging-br-v2.main" for item in result["citations"])


def test_null_context_and_invalid_input(client):
    assert (
        client.post("/api/ask", json=payload(country=None)).json()["result"]["status"]
        == "needs_context"
    )
    assert client.post("/api/ask", json=payload(country="GB")).status_code == 422
    assert client.post("/api/ask", json=payload(expense_date="2026-02-30")).status_code == 422
    assert client.post("/api/ask", json=payload(question=" " * 10)).status_code == 422


def test_request_size_is_bounded(client):
    assert client.post("/api/ask", content=b"a" * 9000).status_code == 413


def test_policy_library_and_missing_document(client):
    assert len(client.get("/api/policies").json()) == 24
    assert len(client.get("/api/history/lodging").json()) == 4
    assert client.get("/policies/lodging-br-v2").status_code == 200
    assert client.get("/api/policies/not-found").status_code == 404


def test_page_and_comparison(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "offline mode" in response.text.lower()
    assert response.headers["Content-Security-Policy"]
    response = client.post(
        "/ask",
        data={
            **payload(employment_type="employee", expense_date="2026-06-15"),
            "compare_date": "2026-07-15",
        },
    )
    assert response.status_code == 200
    assert response.text.count('data-outcome="answered"') == 2
    assert "BRL 180" in response.text and "BRL 220" in response.text


def test_metrics_require_a_secret_and_do_not_contain_questions(client):
    assert client.get("/metrics").status_code == 401
    client.post("/api/ask", json=payload())
    response = client.get("/metrics", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 200
    assert "policytime_answers_total" in response.text
    assert payload()["question"] not in response.text


def test_rate_limits_are_enforced(service):
    settings = Settings(mode="demo", requests_per_minute=1, _env_file=None)
    with TestClient(create_app(settings, service)) as client:
        assert client.post("/api/ask", json=payload()).status_code == 200
        response = client.post("/api/ask", json=payload())
        assert response.status_code == 429
        assert response.headers["Retry-After"] == "60"


def test_model_failure_returns_503(service):
    class BrokenGenerator:
        identity = "unavailable"

        def generate(self, question, context, clauses):
            raise ProviderUnavailable("Model unavailable")

    changed = AnswerService(replace(service.dependencies, generator=BrokenGenerator()), "demo")
    with TestClient(create_app(Settings(mode="demo", _env_file=None), changed)) as client:
        response = client.post("/api/ask", json=payload())
        assert response.status_code == 503
        assert "result" not in response.json()
