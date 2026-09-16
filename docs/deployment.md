# Deployment and recovery

## Status

The container builds locally. PostgreSQL backup/restore was verified on 2026-09-16 in a separate database: 53 clauses and fingerprint `82d154e1ccd254e05376ef9c281fc7c8fbb787b8169ae8febdc8e67d58c0efe2` survived restoration. This is a local recovery drill, not a claim of production uptime or a VM recovery test.

Production needs a 4 GiB Linux VM with Docker Compose, a domain pointing to it, a Mistral key, and an operator's SSH access. Keep the $50 monthly ceiling; verify regional pricing before purchase. No cloud resources have been provisioned.

## First deployment

1. Provision the approved VM and DNS. Allow inbound SSH only from operator addresses, and public TCP 80/443 plus UDP 443. PostgreSQL has no host port in production.
2. Clone this repository under `/opt/policytime`. Install Docker and the Compose plugin. Keep a non-root SSH operator with controlled Docker access.
3. Copy `deploy/production.env.example` to `deploy/production.env`; `chmod 600` it. Fill domain, ACME email, distinct random **hex** database passwords, Mistral key and a metrics token of at least 24 characters. Secrets stay on the server; hex passwords avoid URL interpolation issues.
4. Publish a version tag only after CI passes. CI builds `ghcr.io/vinimundel/policytime:vX.Y.Z`. Set package visibility/public access or authenticate the VM. Never reuse a released version tag.
5. Set `POLICYTIME_IMAGE` in the env file, then run `python3 deploy/release.py ghcr.io/vinimundel/policytime:v0.1.0`.
6. Check `https://YOUR_DOMAIN/readyz`, the browser's six examples, date comparison, and a real hosted answer. Verify source quotations. Read `/metrics` with `Authorization: Bearer YOUR_METRICS_TOKEN` from the monitoring system.
7. Run the hosted benchmark and two-concurrent-request load check. Keep beta labeling until quality and latency targets pass. Observe memory with `docker stats`; the 4 GiB sizing remains a deployment hypothesis until measured on the target VM.

The deployment workflow requires GitHub environment secrets described in `.github/workflows/deploy.yml`. It expects the reviewed checkout and env file already on the VM. External HTTPS verification remains an operator step.

## Budget and observability

The SQL ledger atomically reserves worst-case cost before each model call, settles known usage, and conservatively charges the reservation when usage is unknown. Unsettled reservations survive crashes. `policytime budget` reports monthly totals. Do not manually clear reservations without reconciling provider usage. The $10 ceiling covers calls through this application; it cannot constrain other API-key consumers or cloud bills.

Prometheus metrics expose request duration, request failures and provider token/cost totals. The endpoint is bearer-protected. Operational logs omit raw questions; cached answers persist for up to 24 hours and may contain user-provided text. Avoid sensitive visitor input. Configure an external uptime service for `/readyz`, alert on sustained 5xx/readiness failures and budget exhaustion, and retain rotated logs. The repository's scheduled uptime workflow activates when `POLICYTIME_PUBLIC_URL` is configured; it is a basic check, not a full monitoring service.

Use one application worker: in-process concurrency and rate limits are per worker. App concurrency is two; the provider timeout is 20 seconds. The API body limit is 8 KiB. TLS terminates at Caddy; only its fixed private IP is trusted for forwarded client addresses.

## Backups and verified restoration

```sh
sh deploy/backup.sh
sh deploy/restore-check.sh backups/ACTUAL_BACKUP.dump
```

The restore script creates `policytime_restore_test`; it refuses to overwrite an existing database. Verify the printed corpus fingerprint and clause count against the source, plus migration revision and spending ledger. Remove that disposable database only after review. Automate daily dumps with a systemd timer or cron and copy them to encrypted offsite storage with retention. Weekly VM backups supplement database dumps. Include offsite storage in the operating ceiling.

For disaster recovery: provision a replacement VM, recreate the application role with `deploy/init-db.sh`, restore a chosen dump into an empty database, deploy the matching image, verify readiness and corpus fingerprint, and only then switch DNS. Document the actual recovery time and data-loss window after the VM drill. Never test a restore over the running database.

## Rollback

`release.py` records the prior image and corpus fingerprint. If candidate application readiness fails, it restores the prior active corpus pointer and application image. Migrations must remain backward compatible; the script deliberately does not downgrade schemas. Test migrations against a restored copy before release. A failed migration aborts publication.

For manual rollback, select the recorded previous image, restore the recorded corpus pointer after checking it exists in `corpora`, and run Compose `up -d --wait app` with the previous image. Verify `/readyz` and known policy examples. Preserve incident evidence before changing the ledger or cache. Initial deployment has no prior image to roll back to.

## Release evidence still required

- Public URL and external HTTPS check
- Real Mistral answer and provider billing reconciliation
- Author-reviewed development ratings and held-out judge agreement
- Warm p95 below 15 seconds at two concurrent requests
- VM-level restore drill and uptime observation
