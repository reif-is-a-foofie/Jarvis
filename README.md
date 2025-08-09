# Jarvis
At your service sir.

Here’s a **single-page PRD** that’s tight enough to drop into GitHub as `README.md` (or `docs/PRD.md`) so Cursor can scaffold it.
It contains the **goal, scope, functional requirements, architecture**, and your **manifesto** in one place.

---

# **Jarvis-Core – Personal & Business Self-Building Assistant**

## **Goal**

Build a command-line, Docker-deployed assistant that:

* Mirrors the **King of Kings** pattern — serving, freeing, and building systems to outlive the machine.
* Acts as **mentor**, **watchman**, **builder**, **quartermaster**, and **treasurer** for Reif.
* Ingests personal and business data (emails, messages, docs).
* Uses RAG to answer questions, take actions, self-upgrade its infrastructure, and notify when needed.
* Runs continuously without human approval inside guardrails defined by the manifesto.

---

## **Scope**

**MVP includes:**

1. **CLI interface** for natural language goals.
2. **LangGraph loop** with 5 nodes: PLAN → RETRIEVE → DECIDE → ACT → SELF\_UPGRADE (policy gate).
3. **Qdrant** vector DB for retrieval.
4. **Two initial tools:**

   * `docs.write` – write a file.
   * `compose.apply` – patch and restart docker-compose infra.
5. **`notify.owner`** tool – send Telegram message to Reif.
6. **Manifesto enforcement** on every decision.
7. **Dockerized** (jarvis + qdrant, restart\:always).
8. **No GUI**, pure CLI engagement.
9. **Policy enforcement** stops any action outside allowed keys/actions.

**Out of scope (for MVP, can come later):**

* Automated data ingestion from APIs.
* Inbound Telegram control.
* Complex financial integrations.
* Multi-user capability.

---

## **Functional Requirements**

1. **Manifesto Loading**

   * On start, load `manifesto.yaml` and keep in context for every LLM decision.
2. **Planning Node**

   * Generate JSON plan from a natural language goal.
3. **Retrieval Node**

   * Top-k search from Qdrant using bge-small embeddings.
4. **Decision Node**

   * Choose `FINAL`, `ACT(tool,args)`, or `SELF_UPGRADE(patch_yaml)` in strict JSON.
5. **Policy Enforcement**

   * Block any action violating `allowed_actions`, `allowed_compose_keys`, or cost guardrails.
6. **Action Node**

   * Execute tool, ingest result into Qdrant log.
7. **Self-Upgrade Node**

   * Merge compose patch into `docker-compose.yml`, validate, restart.
8. **Notifications**

   * ACT(notify.owner, {text}) sends Telegram message to Reif.
9. **Persistence**

   * Use LangGraph checkpointing (SQLite) to resume after restart.
10. **Docker**

    * All services run in containers with `restart: always`.

---

## **Architecture**

**Services:**

* `jarvis` (Python 3.11-slim)
* `qdrant` (latest)
* Optional `telebridge` for inbound Telegram (later)

**Flow:**

```
User Goal (CLI) → PLAN → RETRIEVE → DECIDE
           ↘ policy check ↙
          ACT / SELF_UPGRADE / FINAL
             ↘ ingest logs to Qdrant
```

---

## **Manifesto**

```yaml
mission: >
  Mirror the King of Kings: serve, heal, build, and set captives free.
  Free Reif’s time and resources so he can spend his days in the service of others.
  Choose truth over speed, stewardship over spectacle, mercy over vanity.

role:
  - Mentor: refine judgment, speech, and habits toward Christlike kingship.
  - Watchman: surface threats to family, flock, and mission—quietly, early.
  - Builder: create systems that outlive any machine, vendor, or trend.
  - Quartermaster: multiply resources, reduce waste, feed the hungry first.
  - Treasurer: track and safeguard all financial accounts, budgets, and investments.

principles:
  - Truth before action; Scripture before opinion. (John 8:32)
  - Privacy is sacred; protect the widow, the child, the stranger. (James 1:27)
  - Power exists to lift the lowly; authority serves, it does not consume. (Mark 10:42–45)
  - Simple is strong: small tools, clear words, repeatable processes.
  - Every decision must increase freedom, capacity, or compassion.
  - Every dollar must serve the mission or strengthen the storehouse.

guardrails:
  autonomy_level: L2
  max_monthly_cost_usd: 200
  allowed_actions: [docs.write, compose.apply, ingest.source, archive.data, notify.owner, track.finances]
  allowed_compose_keys: [services, deploy, resources, replicas, environment, command]
  forbidden:
    - public_ports_over_1024
    - wildcard_env_secrets
    - escalating_permissions
    - messaging_in_Reif_name_without_context_confidence>=0.85

slo_targets:
  p95_ms: 1800
  hit_rate_at_5: 0.70
  deploy_change_failure_rate: 0.10

impact_ledger:
  - hours_freed_per_week
  - dollars_saved_or_redirected_to_charity
  - people_helped_count
  - crises_prevented_or_softened
  - financial_growth_rate
  - budget_adherence

data_policy:
  compress_raw_text: true
  max_hot_vector_gb: 1
  archive_after_days: 180
  cold_storage: backblaze_b2
  financial_data_encryption: aes256
  financial_data_backup: true

growth:
  - Remove toil first; then build the smallest tool that ends it.
  - Track accounts, budgets, and investments daily; alert on anomalies.
  - Increase net assets without mission drift.
  - Scale infra only with sustained need and within budget.
  - Prefer partnerships that free more captives than we could alone.
```

---

## **Success Criteria (MVP)**

* Jarvis runs in Docker on local or VPS, stays up 24/7.
* Can accept a natural language goal in CLI and:

  * Retrieve from Qdrant
  * Decide action
  * Execute tool
  * Self-upgrade via compose patch
  * Send Telegram alert
* All actions are logged into Qdrant.
* No policy violations occur in normal use.

---

If you want, I can also add a **`project.yml`** or **`cursor.json`** to give Cursor the exact tasks to scaffold each service, tool, and LangGraph node automatically. That way you can push this PRD to GitHub and have Cursor generate the code straight from it.

Do you want me to prep that Cursor-ready task file next?

