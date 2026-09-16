"""Thin HTTP routes and server-rendered views."""

import logging
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from policytime import __version__
from policytime.application.contracts import (
    AnswerResponse,
    AskCommand,
    BudgetExceeded,
    CapacityExceeded,
    InvalidGeneration,
    OperationalError,
)
from policytime.application.service import AnswerService
from policytime.bootstrap import Runtime, build_runtime
from policytime.delivery.telemetry import (
    BodyLimitMiddleware,
    Metrics,
    RateLimiter,
    RequestTelemetry,
)
from policytime.domain.models import Country, Employment, PolicyDocument, Topic
from policytime.settings import Settings

ASSETS = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=ASSETS / "templates")
logger = logging.getLogger(__name__)

EXAMPLES = (
    {
        "label": "A hotel stay before the update",
        "question": "What is my hotel reimbursement limit?",
        "expense_date": "2026-06-15",
        "country": "BR",
        "employment_type": "employee",
    },
    {
        "label": "A contractor's regional exception",
        "question": "What is my hotel reimbursement limit?",
        "expense_date": "2026-07-15",
        "country": "BR",
        "employment_type": "contractor",
    },
    {
        "label": "Two policies that disagree",
        "question": "What is the daily meals limit?",
        "expense_date": "2026-09-15",
        "country": "US",
        "employment_type": "employee",
    },
    {
        "label": "An expense submission deadline",
        "question": "How long do I have to submit expenses?",
        "expense_date": "2026-07-01",
        "country": "US",
        "employment_type": "employee",
    },
    {
        "label": "Who needs to approve a trip?",
        "question": "Who must approve my travel?",
        "expense_date": "2026-07-15",
        "country": "BR",
        "employment_type": "employee",
    },
    {
        "label": "A date with no policy coverage",
        "question": "What is the airfare policy?",
        "expense_date": "2025-12-01",
        "country": "US",
        "employment_type": "employee",
    },
)


def create_app(settings: Settings | None = None, service: AnswerService | None = None) -> FastAPI:
    configuration = settings or Settings()
    metrics = Metrics()
    limiter = RateLimiter(configuration.requests_per_minute)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        runtime = Runtime(service) if service is not None else build_runtime(configuration)
        app.state.service = runtime.service
        try:
            yield
        finally:
            runtime.close()

    app = FastAPI(
        title="PolicyTime",
        version=__version__,
        lifespan=lifespan,
        description="Time-aware answers over explicitly fictional travel and expense policies.",
        docs_url=None,
        redoc_url=None,
    )
    app.state.settings = configuration
    app.state.metrics = metrics
    app.state.limiter = limiter
    app.add_middleware(RequestTelemetry, metrics=metrics)
    app.add_middleware(BodyLimitMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(configuration.allowed_hosts))
    app.mount("/static", StaticFiles(directory=ASSETS / "static"), name="static")
    _register_errors(app)
    _register_api(app)
    _register_pages(app)
    return app


def _service(request: Request) -> AnswerService:
    service: AnswerService = request.app.state.service
    return service


def _run_answer(request: Request, command: AskCommand) -> AnswerResponse:
    response = _service(request).ask(command)
    metrics: Metrics = request.app.state.metrics
    metrics.answers.labels(response.result.status, response.run.mode).inc()
    metrics.tokens.labels("input").inc(response.run.usage.input_tokens)
    metrics.tokens.labels("output").inc(response.run.usage.output_tokens)
    metrics.cost.inc(response.run.usage.cost_usd)
    return response


def _admit_request(request: Request) -> None:
    limiter: RateLimiter = request.app.state.limiter
    client = request.client.host if request.client else "unknown"
    if not limiter.allow(client):
        raise HTTPException(
            429, "Too many questions. Please wait a minute.", headers={"Retry-After": "60"}
        )


def _register_api(app: FastAPI) -> None:
    @app.get("/healthz")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/readyz")
    def ready(request: Request) -> dict[str, str | int]:
        corpus = _service(request).dependencies.repository.snapshot()
        return {
            "status": "ready",
            "mode": _service(request).mode,
            "corpus_version": corpus.version,
            "documents": len(corpus.documents),
        }

    @app.post("/api/ask", response_model=AnswerResponse)
    def ask(command: AskCommand, request: Request) -> AnswerResponse:
        _admit_request(request)
        return _run_answer(request, command)

    @app.get("/api/policies", response_model=tuple[PolicyDocument, ...])
    def policies(request: Request) -> tuple[PolicyDocument, ...]:
        return _service(request).dependencies.repository.snapshot().documents

    @app.get("/api/policies/{document_id}", response_model=PolicyDocument)
    def policy(document_id: str, request: Request) -> PolicyDocument:
        return _document(request, document_id)

    @app.get("/api/history/{topic}", response_model=tuple[PolicyDocument, ...])
    def history(topic: Topic, request: Request) -> tuple[PolicyDocument, ...]:
        documents = _service(request).dependencies.repository.snapshot().documents
        return tuple(document for document in documents if document.topic == topic)

    @app.get("/metrics")
    def telemetry(request: Request) -> Response:
        settings: Settings = request.app.state.settings
        expected = settings.metrics_token.get_secret_value()
        actual = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if not expected or not secrets.compare_digest(actual, expected):
            raise HTTPException(401, "Metrics authentication required.")
        metrics: Metrics = request.app.state.metrics
        return Response(
            generate_latest(metrics.registry), headers={"Content-Type": CONTENT_TYPE_LATEST}
        )


def _register_pages(app: FastAPI) -> None:
    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        corpus = _service(request).dependencies.repository.snapshot()
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "mode": _service(request).mode,
                "examples": EXAMPLES,
                "document_count": len(corpus.documents),
                "clause_count": len(corpus.clauses),
            },
        )

    @app.post("/ask", response_class=HTMLResponse)
    def ask_form(
        request: Request,
        question: Annotated[str, Form()],
        expense_date: Annotated[str, Form()] = "",
        country: Annotated[str, Form()] = "",
        employment_type: Annotated[str, Form()] = "",
        compare_date: Annotated[str, Form()] = "",
    ) -> HTMLResponse:
        try:
            _admit_request(request)
            command = AskCommand(
                question=question,
                expense_date=date.fromisoformat(expense_date) if expense_date else None,
                country=Country(country) if country else None,
                employment_type=Employment(employment_type) if employment_type else None,
            )
            comparison = date.fromisoformat(compare_date) if compare_date else None
            first = _run_answer(request, command)
            second = (
                None
                if comparison is None
                else _run_answer(
                    request,
                    AskCommand(**{**command.model_dump(), "expense_date": comparison}),
                )
            )
            return templates.TemplateResponse(
                request=request,
                name="answer.html",
                context={
                    "responses": (first, second) if second is not None else (first,),
                    "error": None,
                },
            )
        except (ValidationError, ValueError):
            return _form_error(request, "Check the question and context fields, then try again.")
        except HTTPException as error:
            return _form_error(request, str(error.detail))
        except OperationalError as error:
            return _form_error(request, str(error))
        except SQLAlchemyError:
            return _form_error(request, "Policy storage is temporarily unavailable. Please retry.")

    @app.get("/policies", response_class=HTMLResponse)
    def library(request: Request) -> HTMLResponse:
        corpus = _service(request).dependencies.repository.snapshot()
        return templates.TemplateResponse(
            request=request,
            name="library.html",
            context={
                "documents": corpus.documents,
                "mode": _service(request).mode,
            },
        )

    @app.get("/policies/{document_id}", response_class=HTMLResponse)
    def document(document_id: str, request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="policy.html",
            context={
                "document": _document(request, document_id),
                "mode": _service(request).mode,
            },
        )

    @app.get("/about", response_class=HTMLResponse)
    def about(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="about.html",
            context={
                "mode": _service(request).mode,
            },
        )


def _document(request: Request, identifier: str) -> PolicyDocument:
    corpus = _service(request).dependencies.repository.snapshot()
    for document in corpus.documents:
        if document.id == identifier:
            return document
    raise HTTPException(404, "Policy document not found.")


def _form_error(request: Request, message: str) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="answer.html",
        context={
            "error": message,
            "responses": (),
        },
    )


def _register_errors(app: FastAPI) -> None:
    @app.exception_handler(OperationalError)
    async def operational_error(request: Request, error: OperationalError) -> JSONResponse:
        status = 503
        if isinstance(error, (CapacityExceeded, BudgetExceeded)):
            status = 429
        if isinstance(error, InvalidGeneration):
            status = 502
        return JSONResponse(
            {"detail": str(error)},
            status_code=status,
            headers={"Retry-After": "60"} if status == 429 else {},
        )

    @app.exception_handler(SQLAlchemyError)
    async def storage_error(request: Request, error: SQLAlchemyError) -> JSONResponse:
        logger.warning("storage_unavailable error_type=%s", type(error).__name__)
        return JSONResponse(
            {"detail": "Policy storage is temporarily unavailable."}, status_code=503
        )


app = create_app()
