# Four-week release scope

| Week | Implemented artifacts | Remaining external work |
|---|---|---|
| 1 | Repository, corpus, fixtures, baseline API and UI | Public preview |
| 2 | Eligibility, graph precedence, neural retrieval/reranking, conflict UI | Observe real VM resource use |
| 3 | Four-way benchmark, preserved failure, judge calibration tooling | Author ratings, hosted run, judge agreement |
| 4 | Budget controls, metrics, container, migrations, backup/rollback tooling, walkthrough | Provision VM, recovery drill on VM, uptime observation, production release |

Budget target: approximately $24 compute + $4.80 weekly backup option + $10 model use + $11.20 reserve = $50/month. Verify current regional DigitalOcean pricing before provisioning; taxes, transfer overages, domain purchase and offsite storage may change the total. The model ledger caps application model calls, not the cloud bill. Configure provider billing alerts separately.

No accounts, uploads, reimbursement execution or multi-agent orchestration in v1. Distillation remains a separate follow-up project.
