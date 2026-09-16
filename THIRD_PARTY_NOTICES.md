# Third-party notices

- HTMX 2.0.8 is vendored under the Zero-Clause BSD license. See `src/policytime/delivery/static/vendor/HTMX-LICENSE.txt`. Source: https://github.com/bigskysoftware/htmx/tree/v2.0.8. Vendored script SHA-256: `22283ef68cb7545914f0a88a1bdedc7256a703d1d580c1d255217d0a50d31313`.
- Embedding weights: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 (Apache-2.0 model card).
- Reranker weights: https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2 (Apache-2.0 model card).
- Model revisions are pinned in `models.lock.json`; weights are downloaded during image construction, not committed to Git.
- Python dependencies retain their respective licenses. Exact versions are recorded in `uv.lock`.
- Mistral is accessed as a hosted service; model weights are not distributed here.

The fictional Northstar Works policy corpus and interface assets were authored for this project. They do not represent an actual employer's policies.
