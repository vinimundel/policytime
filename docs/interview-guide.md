# Interview guide

## Two-minute explanation

“PolicyTime answers fictional travel-policy questions for the date an expense happened. A semantically similar passage can still be the wrong policy. I filter date and audience before retrieval, then use explicit clause relationships to decide authority. The LLM explains selected evidence; it does not decide which version governs. Missing context, conflicts and absent evidence are separate outcomes.”

Demonstrate June versus July hotel limits, a contractor exception, and the conflicting September meals bulletin. Open each source and decision explanation.

## Tradeoffs worth discussing

- **A graph inside PostgreSQL:** clause relationships need transactional consistency with text and embeddings. At this corpus size a separate graph database adds operations without useful scale benefits.
- **Pure decisions:** dates and context are inputs, never clock reads. Unit tests can reproduce a historical answer exactly.
- **Partial overrides:** replacing one monetary clause does not erase receipt obligations. Documents are too coarse a unit for precedence.
- **Explicit conflict representation:** contradictory structured values without an authority edge remain unresolved. Natural-language contradiction detection is outside the deterministic guarantee.
- **Citation validation:** IDs and exact quotes are enforceable; semantic entailment still needs evaluation.
- **Spending reservations:** concurrent requests reserve worst-case cost before calling a provider. Unknown outcomes retain conservative charges. This sacrifices some availability to preserve the ceiling.
- **One service, one database:** understandable operations under a $50 target. Model memory and VM performance must be measured on the actual machine.
- **Negative result:** the reranker added latency without improving this small extractive benchmark. Keep that result; complexity needs evidence.

## Honest résumé wording

“Built a temporal policy RAG portfolio application with FastAPI, PostgreSQL/pgvector, PyTorch and LangChain; implemented explicit policy precedence, citation checks and persistent model-budget reservations. Achieved 39/40 held-out synthetic reference checks with real retrieval models and extractive answers.”

Do not claim production deployment, human-rated LLM accuracy, judge agreement or production latency until those measurements exist.

## Next experiment

Freeze this benchmark and train a smaller reranker with PyTorch as a separate experiment. Compare quality, CPU latency, memory and training cost. Given the current no-reranker tie, first establish a harder development retrieval dataset that actually benefits from reranking.
