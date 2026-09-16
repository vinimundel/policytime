"""Pure evidence selection and citation checks."""

from policytime.application.contracts import DraftAnswer, InvalidGeneration
from policytime.domain.models import Citation, Clause, Corpus


def citation_for(clause: Clause, corpus: Corpus, quote: str | None = None) -> Citation:
    document = next(item for item in corpus.documents if item.id == clause.document_id)
    return Citation(
        clause_id=clause.id,
        document_id=document.id,
        document_title=document.title,
        quote=quote or clause.text,
        effective_period=clause.period,
    )


def validate_citations(
    draft: DraftAnswer,
    evidence: tuple[Clause, ...],
    corpus: Corpus,
) -> tuple[Citation, ...]:
    allowed = {clause.id: clause for clause in evidence}
    citations: list[Citation] = []
    seen: set[str] = set()
    for item in draft.citations:
        clause = allowed.get(item.clause_id)
        if clause is None:
            raise InvalidGeneration("The model cited evidence outside the selected policy set.")
        if item.quote not in clause.text:
            raise InvalidGeneration("A model quotation did not match its source passage.")
        if item.clause_id in seen:
            continue
        seen.add(item.clause_id)
        citations.append(citation_for(clause, corpus, item.quote))
    return tuple(citations)
