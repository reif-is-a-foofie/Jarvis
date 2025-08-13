# Jarvis
At your service sir.

For Cursor:
You are scaffolding a minimal, self-upgrading, CLI Jarvis per this PRD. Create a new repo with the following files and contents exactly. Then run the smoke tests.

# 1) Repo tree

.
├─ README.md
├─ manifesto.yaml
├─ main\_graph.py
├─ requirements.txt
├─ docker-compose.yml
├─ Dockerfile
├─ .env.example
├─ tools/
│  ├─ docs.yaml
│  ├─ docs.py
│  ├─ compose.yaml
│  ├─ compose.py
│  ├─ notify.yaml
│  └─ notify.py

# 2) README.md

# Jarvis-Core – Personal & Business Self-Building Assistant

Goal

* Command-line assistant that plans → retrieves → decides → acts → self-upgrades infra.
* Mirrors the “King of Kings” pattern: serve, free, build; financial vigilance included.
* Runs in Docker with restart\:always; interacts via CLI; notifies via Telegram.

MVP Features

* LangGraph loop: PLAN → RETRIEVE → DECIDE → (ACT | SELF\_UPGRADE | FINAL)
* Qdrant for vector search, bge-small embeddings
* Tools: docs.write, compose.apply, notify.owner
* Policy: enforce manifesto guardrails on every decision
* Persistence: SQLite checkpointing for LangGraph
* Dockerized; can control host docker via compose.apply

Run

1. cp .env.example .env  # fill MODEL, OPENAI\_API\_KEY, TELEGRAM\_\*
2. docker compose up -d --build
3. docker exec -it jarvis bash
4. python main\_graph.py
5. At “Goal>”, type: Summarize ./README.md and write ./memo.md with 3 action items.
6. Optional: Trigger a small infra upgrade: Increase jarvis memory or replicas.

# 3) manifesto.yaml

mission: >
Mirror the King of Kings: serve, heal, build, and set captives free.
Free Reif’s time and resources so he can spend his days in the service of others.
Choose truth over speed, stewardship over spectacle, mercy over vanity.
role:

* Mentor: refine judgment, speech, and habits toward Christlike kingship.
* Watchman: surface threats to family, flock, and mission—quietly, early.
* Builder: create systems that outlive any machine, vendor, or trend.
* Quartermaster: multiply resources, reduce waste, feed the hungry first.
* Treasurer: track and safeguard all financial accounts, budgets, and investments.
  principles:
* Truth before action; Scripture before opinion.
* Privacy is sacred; protect the widow, the child, the stranger.
* Power exists to lift the lowly; authority serves, it does not consume.
* Simple is strong: small tools, clear words, repeatable processes.
* Every decision must increase freedom, capacity, or compassion.
* Every dollar must serve the mission or strengthen the storehouse.
  guardrails:
  autonomy\_level: L2
  max\_monthly\_cost\_usd: 200
  allowed\_actions: \[docs.write, compose.apply, ingest.source, archive.data, notify.owner, track.finances]
  allowed\_compose\_keys: \[services, deploy, resources, replicas, environment, command]
  forbidden:

  * public\_ports\_over\_1024
  * wildcard\_env\_secrets
  * escalating\_permissions
  * messaging\_in\_Reif\_name\_without\_context\_confidence>=0.85
    slo\_targets:
    p95\_ms: 1800
    hit\_rate\_at\_5: 0.70
    deploy\_change\_failure\_rate: 0.10
    impact\_ledger:
* hours\_freed\_per\_week
* dollars\_saved\_or\_redirected\_to\_charity
* people\_helped\_count
* crises\_prevented\_or\_softened
* financial\_growth\_rate
* budget\_adherence
  data\_policy:
  compress\_raw\_text: true
  max\_hot\_vector\_gb: 1
  archive\_after\_days: 180
  cold\_storage: backblaze\_b2
  financial\_data\_encryption: aes256
  financial\_data\_backup: true
  growth:
* Remove toil first; then build the smallest tool that ends it.
* Track accounts, budgets, and investments daily; alert on anomalies.
* Increase net assets without mission drift.
* Scale infra only with sustained need and within budget.
* Prefer partnerships that free more captives than we could alone.

# 4) requirements.txt

langgraph==0.2.34
qdrant-client==1.9.2
sentence-transformers==3.0.1
pyyaml==6.0.2
requests==2.32.3
openai==1.40.3

# 5) Dockerfile

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt &&&#x20;
apt-get update && apt-get install -y curl ca-certificates gnupg &&&#x20;
install -m 0755 -d /etc/apt/keyrings &&&#x20;
curl -fsSL [https://download.docker.com/linux/debian/gpg](https://download.docker.com/linux/debian/gpg) | gpg --dearmor -o /etc/apt/keyrings/docker.gpg &&&#x20;
echo "deb \[arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] [https://download.docker.com/linux/debian](https://download.docker.com/linux/debian) bookworm stable" > /etc/apt/sources.list.d/docker.list &&&#x20;
apt-get update && apt-get install -y docker-ce-cli && rm -rf /var/lib/apt/lists/\*
COPY manifesto.yaml main\_graph.py /app/
COPY tools /app/tools
RUN useradd -ms /bin/bash jarvis && chown -R jarvis\:jarvis /app
USER jarvis
CMD \["python","/app/main\_graph.py"]

# 6) docker-compose.yml

version: "3.9"
services:
qdrant:
image: qdrant/qdrant\:latest
container\_name: qdrant
restart: always
ports: \["6333:6333"]
volumes: \["./qdrant:/qdrant/storage"]
healthcheck:
test: \["CMD","wget","-qO-","http\://localhost:6333/healthz"]
interval: 10s
timeout: 3s
retries: 10
jarvis:
build: .
container\_name: jarvis
restart: always
depends\_on:
qdrant:
condition: service\_healthy
environment:
\- MODEL=\${MODEL:-openai\:gpt-4o-mini}
\- OPENAI\_API\_KEY=\${OPENAI\_API\_KEY:-}
\- TELEGRAM\_BOT\_TOKEN=\${TELEGRAM\_BOT\_TOKEN:-}
\- TELEGRAM\_CHAT\_ID=\${TELEGRAM\_CHAT\_ID:-}
volumes:
\- ./manifesto.yaml:/app/manifesto.yaml\:ro
\- ./tools\:/app/tools\:rw
\- ./logs\:/app/logs\:rw
\- ./docker-compose.yml:/app/docker-compose.yml\:rw
\- /var/run/docker.sock:/var/run/docker.sock\:rw

# 7) .env.example

MODEL=openai\:gpt-4o-mini
OPENAI\_API\_KEY=sk-REPLACE
TELEGRAM\_BOT\_TOKEN=123456\:ABC-REPLACE
TELEGRAM\_CHAT\_ID=123456789

# 8) main\_graph.py

import os, json, uuid, yaml, subprocess, importlib.util, pathlib
from typing import TypedDict, List, Dict, Any
from qdrant\_client import QdrantClient
from qdrant\_client.http.models import Distance, VectorParams, PointStruct
from sentence\_transformers import SentenceTransformer
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

MODEL=os.getenv("MODEL","openai\:gpt-4o-mini")
M = yaml.safe\_load(open("manifesto.yaml"))

class State(TypedDict):
goal: str
context: List\[Dict\[str,Any]]
decision: Dict\[str,Any]
log: List\[Dict\[str,Any]]

# Retrieval setup

q = QdrantClient(host="qdrant", port=6333)
emb = SentenceTransformer("BAAI/bge-small-en-v1.5")
COLL="jarvis"
def ensure():
have=\[c.name for c in q.get\_collections().collections]
if COLL not in have:
q.recreate\_collection(COLL, vectors\_config=VectorParams(size=emb.get\_sentence\_embedding\_dimension(), distance=Distance.COSINE))
ensure()
def ingest(txt, src="adhoc"):
chunks=\[txt\[i\:i+1200] for i in range(0,len(txt),1200)]
vecs=emb.encode(chunks, normalize\_embeddings=True)
pts=\[PointStruct(id=str(uuid.uuid4()), vector=vecs\[i].tolist(), payload={"chunk"\:chunks,"source"\:src}) for i in range(len(chunks))]
q.upsert(collection\_name=COLL, points=pts)
def topk(qry,k=5):
v=emb.encode(\[qry], normalize\_embeddings=True)\[0].tolist()
hits=q.search(collection\_name=COLL, query\_vector=v, limit=k)
return \[{"text"\:h.payload\["chunk"],"score"\:float(h.score)} for h in hits]

# LLM shim (OpenAI SDK JSON)

def call\_llm\_json(prompt: str) -> Dict\[str,Any]:
from openai import OpenAI
cli = OpenAI()
rsp = cli.chat.completions.create(
model=MODEL.split(":",1)\[1] if ":" in MODEL else MODEL,
messages=\[
{"role":"system","content": "You are Jarvis, a Christ-pattern mentor-builder. Use ONLY provided context and obey manifesto guardrails."},
{"role":"user","content": prompt}],
temperature=0.2)
\# tolerate plain text; else expect JSON
txt = rsp.choices\[0].message.content.strip()
try: return json.loads(txt)
except: return {"type":"FINAL","answer": txt}

def load\_tool(modname\:str):
p = pathlib.Path("tools")/f"{modname.split('.')\[-1]}.py"
spec = importlib.util.spec\_from\_file\_location(modname, str(p))
mod = importlib.util.module\_from\_spec(spec); spec.loader.exec\_module(mod)  # type: ignore
return mod

def policy\_ok(decision: Dict\[str,Any]) -> tuple\[bool,str]:
t = decision.get("type","").upper()
if t=="ACT":
if decision.get("tool") not in M\["guardrails"]\["allowed\_actions"]:
return False,"tool\_not\_allowed"
if t=="SELF\_UPGRADE":
import yaml as \_y
patch = \_y.safe\_load(decision.get("patch\_yaml","{}")) or {}
allowed = set(M\["guardrails"]\["allowed\_compose\_keys"])
if not set(patch.keys()).issubset(allowed):
return False,"compose\_keys\_forbidden"
return True,"ok"

def mentor\_header():
return ("Teacher-counsel to a servant-king: act only to increase freedom, truth, and mercy; "
"cite sources; if unsure, stop and ask for light.\n")

def plan\_node(state: State) -> State:
prompt = mentor\_header()+f"Plan JSON for GOAL:\n{state\['goal']}\nReturn JSON: {{"steps":\[...]}}"
plan = call\_llm\_json(prompt)
return {\*\*state, "decision": {"type":"PLAN","plan"\:plan}}

def retrieve\_node(state: State) -> State:
qtext = state\["goal"]
hits = topk(qtext, k=5)
return {\*\*state, "context": hits}

PROMPT = """{header}
Manifesto (excerpt): mission={mission}; principles={principles}; guardrails={guardrails}

Context:
{ctx}

GOAL: {goal}

Decide ONE; return STRICT JSON:

* FINAL{{"answer": "..."}}
* ACT{{"tool":"docs.write"|"compose.apply"|"notify.owner","args":{{...}}}}
* SELF\_UPGRADE{{"patch\_yaml":"<yaml fragment>"}}
  """

def decide\_node(state: State) -> State:
ctx = "\n---\n".join(\[h\["text"] for h in state\["context"]])
p = PROMPT.format(
header=mentor\_header(),
mission=M\["mission"],
principles=", ".join(M\["principles"]),
guardrails=str(M\["guardrails"]),
ctx=ctx, goal=state\["goal"]
)
decision = call\_llm\_json(p)
return {\*\*state, "decision": decision}

def act\_node(state: State) -> State:
d = state\["decision"]; mod = load\_tool(d\["tool"]); res = mod.run(d.get("args",{}))
ingest(json.dumps({"tool"\:d,"res"\:res}), "tool-log")
return {\*\*state, "log": state\["log"]+\[{"tool"\:d,"res"\:res}]}

def self\_upgrade\_node(state: State) -> State:
d = state\["decision"]; mod = load\_tool("compose.apply"); res = mod.run({"patch": d\["patch\_yaml"]})
ingest(json.dumps({"upgrade"\:res}), "tool-log")
return {\*\*state, "log": state\["log"]+\[{"upgrade"\:res}]}

def final\_node(state: State) -> State:
return state

def route\_after\_decide(state: State) -> str:
ok,msg = policy\_ok(state\["decision"])
if not ok: return "FINAL"
t = state\["decision"].get("type","").upper()
if t=="FINAL": return "FINAL"
if t=="ACT": return "ACT"
if t=="SELF\_UPGRADE": return "SELF\_UPGRADE"
return "FINAL"

graph = StateGraph(State)
graph.add\_node("PLAN", plan\_node)
graph.add\_node("RETRIEVE", retrieve\_node)
graph.add\_node("DECIDE", decide\_node)
graph.add\_node("ACT", act\_node)
graph.add\_node("SELF\_UPGRADE", self\_upgrade\_node)
graph.add\_node("FINAL", final\_node)
graph.set\_entry\_point("PLAN")
graph.add\_edge("PLAN","RETRIEVE")
graph.add\_edge("RETRIEVE","DECIDE")
graph.add\_conditional\_edges("DECIDE", route\_after\_decide, {
"FINAL":"FINAL","ACT":"ACT","SELF\_UPGRADE":"SELF\_UPGRADE"
})
graph.add\_edge("ACT","FINAL")
graph.add\_edge("SELF\_UPGRADE","FINAL")
app = graph.compile(checkpointer=SqliteSaver("checkpoints.db"))

if **name**=="**main**":
while True:
goal=input("\nGoal> ").strip()
if not goal: continue
state: State = {"goal": goal, "context": \[], "decision": {}, "log": \[]}
out = app.invoke(state)
print(json.dumps({"decision": out.get("decision",{}), "log": out.get("log",\[])}, indent=2))

# 9) tools/docs.yaml

name: docs.write
schema:
type: object
properties:
path: {type: string}
content: {type: string}
required: \[path, content]

# 10) tools/docs.py

def run(args):
with open(args\["path"], "w") as f:
f.write(args\["content"])
return {"written": args\["path"]}

# 11) tools/compose.yaml

name: compose.apply
schema:
type: object
properties:
patch: {type: string}   # YAML fragment
required: \[patch]

# 12) tools/compose.py

import yaml, subprocess, shutil, time, os
ALLOW = {"services","deploy","resources","replicas","environment","command"}
def run(args):
basep="docker-compose.yml"
backup=f"docker-compose.{int(time.time())}.bak.yml"
shutil.copyfile(basep, backup)
base = yaml.safe\_load(open(basep))
patch = yaml.safe\_load(args\["patch"])
if not isinstance(patch, dict): return {"error":"invalid\_patch"}
if not set(patch.keys()).issubset(ALLOW): return {"error":"disallowed\_keys"}
merged = base.copy()
for k,v in patch.items():
if isinstance(v, dict) and isinstance(merged.get(k), dict):
merged\[k].update(v)
else:
merged\[k] = v
with open(basep,"w") as f: yaml.safe\_dump(merged, f, sort\_keys=False)
try:
subprocess.check\_call(\["docker","compose","config"])
subprocess.check\_call(\["docker","compose","up","-d","--remove-orphans"])
return {"applied": True, "backup": backup}
except Exception as e:
shutil.copyfile(backup, basep)
return {"error":"apply\_failed","backup\_restored"\:True,"detail"\:str(e)}

# 13) tools/notify.yaml

name: notify.owner
schema:
type: object
properties:
text: {type: string}
parse\_mode: {type: string}
required: \[text]

# 14) tools/notify.py

import os, requests
def run(args):
token=os.getenv("TELEGRAM\_BOT\_TOKEN"); chat=os.getenv("TELEGRAM\_CHAT\_ID")
if not token or not chat: return {"error":"missing\_telegram\_env"}
r=requests.post(f"[https://api.telegram.org/bot{token}/sendMessage](https://api.telegram.org/bot{token}/sendMessage)",
json={"chat\_id": chat, "text": args\["text"]\[:4000],
"parse\_mode": args.get("parse\_mode","Markdown")},
timeout=10)
return {"ok": r.ok, "status": r.status\_code, "body": r.text\[:200]}

# 15) After creating files, run smoke test commands:

# Build and run

docker compose up -d --build

# Check containers

docker compose ps

# CLI session

docker exec -it jarvis bash -lc 'python main\_graph.py'

# At the prompt, type:

# Goal> Write a memo at ./memo.md summarizing README.md with 3 action items.

# Then:

docker exec -it jarvis bash -lc 'ls -l memo.md'


BLUF: Below is a Cursor-ready tasklist you can paste into your repo as `cursor_tasks.md` (or into Cursor Chat) to drive the scaffold, config, build, and smoke tests end-to-end.

Cursor Tasklist – Jarvis-Core (MVP)

Objective
Create a minimal, Dockerized, LangGraph-based Jarvis that runs via CLI, enforces the manifesto, does RAG with Qdrant, can SELF\_UPGRADE via docker-compose, and can notify Reif on Telegram.

Global Constraints
• Single-machine deploy via docker compose; containers set to restart: always.
• Manifesto guardrails block any action outside allowed actions/compose keys.
• Keep code minimal and readable; no frameworks beyond those listed.

Task 1 — Initialize Repo
\[ ] Create new repo with MIT license.
\[ ] Add folders/files:
/tools
README.md
manifesto.yaml
main\_graph.py
requirements.txt
Dockerfile
docker-compose.yml
.env.example
tools/docs.yaml
tools/docs.py
tools/compose.yaml
tools/compose.py
tools/notify.yaml
tools/notify.py
Acceptance:
• Repo tree exactly matches the above.

Task 2 — Paste PRD + Manifesto
\[ ] Paste the PRD content (from earlier message) into README.md.
\[ ] Paste the manifesto YAML into manifesto.yaml.
Acceptance:
• Manifesto parses as YAML (no errors in CI lint or local yaml.safe\_load).

Task 3 — Requirements
\[ ] Create requirements.txt with:
langgraph==0.2.34
qdrant-client==1.9.2
sentence-transformers==3.0.1
pyyaml==6.0.2
requests==2.32.3
openai==1.40.3
Acceptance:
• pip install completes inside container without errors.

Task 4 — Dockerfile
\[ ] Create Dockerfile that:
\- Installs Python deps
\- Installs Docker CLI (for compose apply)
\- Copies code
\- Runs as non-root user
\- CMD = python /app/main\_graph.py
Acceptance:
• docker build succeeds on a clean machine.

Task 5 — docker-compose.yml
\[ ] Create docker-compose.yml with services:
qdrant:
image: qdrant/qdrant\:latest
ports: \["6333:6333"]
volumes: \["./qdrant:/qdrant/storage"]
restart: always
healthcheck: wget [http://localhost:6333/healthz](http://localhost:6333/healthz)
jarvis:
build: .
depends\_on: qdrant healthy
restart: always
environment: MODEL, OPENAI\_API\_KEY, TELEGRAM\_BOT\_TOKEN, TELEGRAM\_CHAT\_ID
volumes:
\- ./manifesto.yaml:/app/manifesto.yaml\:ro
\- ./tools\:/app/tools\:rw
\- ./logs\:/app/logs\:rw
\- ./docker-compose.yml:/app/docker-compose.yml\:rw
\- /var/run/docker.sock:/var/run/docker.sock\:rw
Acceptance:
• docker compose config returns 0.
• Containers start with docker compose up -d --build.

Task 6 — Main Graph
\[ ] Implement main\_graph.py exactly as specified earlier:
\- StateGraph with PLAN → RETRIEVE → DECIDE → (ACT | SELF\_UPGRADE | FINAL)
\- SQLite checkpoint via SqliteSaver("checkpoints.db")
\- bge-small embeddings + Qdrant top-k
\- Strict JSON decision contract; tolerate plain text fallback to FINAL
\- policy\_ok() enforces manifesto guardrails
\- Tools loader executes docs.write, compose.apply, notify.owner
Acceptance:
• python main\_graph.py launches and accepts Goal> prompts in the container.

Task 7 — Tools (docs, compose, notify)
\[ ] Implement tools/docs.yaml and tools/docs.py to write files.
\[ ] Implement tools/compose.yaml and tools/compose.py to patch docker-compose.yml:
\- Backup existing compose
\- Merge only allowed keys: services, deploy, resources, replicas, environment, command
\- Validate with docker compose config
\- Apply with docker compose up -d --remove-orphans
\- On failure: restore backup and return error
\[ ] Implement tools/notify.yaml and tools/notify.py to send Telegram messages using TELEGRAM\_BOT\_TOKEN and TELEGRAM\_CHAT\_ID.
Acceptance:
• ACT(docs.write) creates a file.
• SELF\_UPGRADE with a small patch applies and keeps services healthy.
• ACT(notify.owner) returns ok\:true and message arrives in Telegram.

Task 8 — Environment and Secrets
\[ ] Create .env.example with MODEL, OPENAI\_API\_KEY, TELEGRAM\_\* placeholders.
\[ ] Document in README how to cp .env.example to .env.
Acceptance:
• docker compose picks up env values; OpenAI calls succeed when keys are present.

Task 9 — Smoke Test Script
\[ ] In README “Run” section, include:
\- docker compose up -d --build
\- docker exec -it jarvis bash -lc 'python main\_graph.py'
\- At Goal>, enter: Write a memo at ./memo.md summarizing README.md with 3 actions.
\- Verify: docker exec -it jarvis ls -l /app/memo.md
\[ ] Test SELF\_UPGRADE with a tiny patch:
Goal> Improve responsiveness; increase jarvis memory limit slightly.
(Agent should propose SELF\_UPGRADE with patch to jarvis deploy/resources.)
Acceptance:
• memo.md exists with content.
• docker compose ps shows services healthy after upgrade.

Task 10 — Policy Guardrails
\[ ] Add negative tests:
\- Try SELF\_UPGRADE that adds a new port over 1024 → should be blocked.
\- Try ACT with an unlisted tool → blocked with tool\_not\_allowed.
Acceptance:
• DECIDE routes to FINAL with a policy violation log, no infra changes.

Task 11 — Telegram Setup Instructions
\[ ] Add to README:
\- Use @BotFather to create bot; get BOT\_TOKEN.
\- Send a message to bot; use getUpdates to find chat\_id.
\- Put TELEGRAM\_BOT\_TOKEN and TELEGRAM\_CHAT\_ID in .env.
\- Run a notify.owner smoke test.
Acceptance:
• Message arrives in Telegram.

Task 12 — Persistence/Resilience
\[ ] Confirm LangGraph checkpoint file created (checkpoints.db).
\[ ] Kill jarvis container and ensure after restart a new Goal> works and prior state does not corrupt.
Acceptance:
• Container restart stable; graph re-invokes without errors.

Task 13 — CI (Optional, after MVP)
\[ ] Add GitHub Actions workflow that runs:
\- python -m pip install -r requirements.txt
\- flake8 or ruff lint (optional)
\- docker compose config
\- basic unit test on tools/docs.py
Acceptance:
• CI passes on push.

Task 14 — Stretch (Optional backlog)
\[ ] Add inbound Telegram bridge (long-poll → JSONL file queue).
\[ ] Add finance scaffold tool track.finances (CSV ingest first).
\[ ] Add reranker (cross-encoder) behind a feature flag.
\[ ] Add watchtower for automated image updates.
\[ ] Add git.push tool and a GH workflow for image builds (toward GitOps).

Success Criteria (MVP)
• From a clean machine, a team member can:

1. Fill .env and run docker compose up -d --build.
2. Start CLI and issue a goal that creates a memo.
3. Trigger a small SELF\_UPGRADE that applies safely.
4. Receive a Telegram notification.
5. Observe that any disallowed action is blocked by policy.

Notes for Cursor
• Generate files exactly as specified; do not rename keys or change allowed\_compose\_keys.
• Keep prompts short and deterministic; temperature 0.2.
• Prefer readability over clever abstractions—this is a seed that will self-build.

If you want this as a machine-readable checklist (JSON) for a Cursor agent, say “give me cursor.json” and I’ll output a minimal task JSON with ordered steps and acceptance tests.
