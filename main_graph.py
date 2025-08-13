import os, json, uuid, yaml, subprocess, importlib.util, pathlib, time, random
from typing import TypedDict, List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

MODEL=os.getenv("MODEL","openai:gpt-4o-mini")
M = yaml.safe_load(open("manifesto.yaml"))

class State(TypedDict):
    goal: str
    context: List[Dict[str,Any]]
    decision: Dict[str,Any]
    log: List[Dict[str,Any]]

# Retrieval setup

# For Heroku, use in-memory Qdrant client; lazy init to avoid boot timeouts
q: QdrantClient | None = None
emb: SentenceTransformer | None = None
COLL="jarvis"

def _ensure_retrieval_ready() -> None:
    global q, emb
    if q is None:
        qdrant_url = os.getenv("QDRANT_URL", "").strip()
        qdrant_key = os.getenv("QDRANT_API_KEY", "").strip()
        if qdrant_url:
            q = QdrantClient(url=qdrant_url, api_key=qdrant_key or None, prefer_grpc=False)
        else:
            q = QdrantClient(":memory:")
    if emb is None:
        emb = SentenceTransformer("BAAI/bge-small-en-v1.5")
    try:
        have=[c.name for c in q.get_collections().collections]  # type: ignore[attr-defined]
        if COLL not in have:
            q.recreate_collection(
                COLL,
                vectors_config=VectorParams(
                    size=emb.get_sentence_embedding_dimension(),  # type: ignore[union-attr]
                    distance=Distance.COSINE,
                ),
            )
    except Exception as e:
        print(f"Creating collection: {e}")
        q.recreate_collection(  # type: ignore[union-attr]
            COLL,
            vectors_config=VectorParams(
                size=emb.get_sentence_embedding_dimension(),  # type: ignore[union-attr]
                distance=Distance.COSINE,
            ),
        )

def ingest(txt: str, src: str = "adhoc", meta: Optional[Dict[str, Any]] = None) -> None:
    _ensure_retrieval_ready()
    chunks=[txt[i:i+1200] for i in range(0,len(txt),1200)]
    vecs=emb.encode(chunks, normalize_embeddings=True)  # type: ignore[union-attr]
    pts=[]
    for i in range(len(chunks)):
        payload = {"chunk": chunks[i], "source": src}
        if meta:
            # Shallow merge of metadata
            payload.update(meta)
        pts.append(PointStruct(id=str(uuid.uuid4()), vector=vecs[i].tolist(), payload=payload))
    q.upsert(collection_name=COLL, points=pts)  # type: ignore[union-attr]

def topk(qry: str, k: int = 5):
    _ensure_retrieval_ready()
    v=emb.encode([qry], normalize_embeddings=True)[0].tolist()  # type: ignore[union-attr]
    hits=q.search(collection_name=COLL, query_vector=v, limit=k)  # type: ignore[union-attr]
    return [{"text":h.payload["chunk"],"score":float(h.score)} for h in hits]

# LLM shim (OpenAI SDK JSON)

def _get_openai_client():
    # Support proxies via env; avoid passing unsupported args to httpx/OpenAI
    from openai import OpenAI
    proxy = os.getenv("OPENAI_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    if proxy:
        os.environ.setdefault("HTTPS_PROXY", proxy)
        os.environ.setdefault("HTTP_PROXY", proxy)
    return OpenAI()

def call_llm_json(prompt: str) -> Dict[str,Any]:
    # bounded retries with jitter; simple circuit breaker via env flag
    if os.getenv("LLM_CIRCUIT_OPEN", "false").lower() == "true":
        return {"type":"FINAL","answer":"LLM temporarily unavailable; please try again shortly."}
    last_err = None
    for attempt in range(3):
        try:
            cli = _get_openai_client()
            rsp = cli.chat.completions.create(
                model=MODEL.split(":",1)[1] if ":" in MODEL else MODEL,
                messages=[
                    {"role":"system","content": "You are Jarvis, a Christ-pattern mentor-builder. Use ONLY provided context and obey manifesto guardrails."},
                    {"role":"user","content": prompt}],
                temperature=0.2)
            txt = rsp.choices[0].message.content.strip()
            try:
                return json.loads(txt)
            except:
                return {"type":"FINAL","answer": txt}
        except Exception as e:
            last_err = e
            time.sleep(0.5 + random.random())
    return {"type":"FINAL","answer": f"LLM error: {last_err}"}

def load_tool(modname:str):
    module_stub = modname.split(".", 1)[0]
    p = pathlib.Path("tools")/f"{module_stub}.py"
    spec = importlib.util.spec_from_file_location(modname, str(p))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)  # type: ignore
    return mod

def policy_ok(decision: Dict[str,Any]) -> tuple[bool,str]:
    t = decision.get("type","").upper()
    if t=="ACT":
        if decision.get("tool") not in M["guardrails"]["allowed_actions"]:
            return False,"tool_not_allowed"
    if t=="SELF_UPGRADE":
        import yaml as _y
        patch = _y.safe_load(decision.get("patch_yaml","{}")) or {}
        allowed = set(M["guardrails"]["allowed_compose_keys"])
        if not set(patch.keys()).issubset(allowed):
            return False,"compose_keys_forbidden"
    return True,"ok"

def mentor_header():
    return ("Teacher-counsel to a servant-king: act only to increase freedom, truth, and mercy; "
            "cite sources; if unsure, stop and ask for light.\n")

def plan_node(state: State) -> State:
    prompt = mentor_header()+f"Plan JSON for GOAL:\n{state['goal']}\nReturn JSON: {{'steps':[...]}}"
    plan = call_llm_json(prompt)
    return {**state, "decision": {"type":"PLAN","plan":plan}}

def retrieve_node(state: State) -> State:
    qtext = state["goal"]
    hits = topk(qtext, k=5)
    return {**state, "context": hits}

PROMPT = """{header}
Manifesto (excerpt): mission={mission}; principles={principles}; guardrails={guardrails}

Context:
{ctx}

GOAL: {goal}

Decide ONE; return STRICT JSON:

* FINAL{{"answer": "..."}}
* ACT{{"tool": one of [{allowed_tools}], "args":{{...}}}}
* SELF_UPGRADE{{"patch_yaml":"<yaml fragment>"}}
"""

def decide_node(state: State) -> State:
    ctx = "\n---\n".join([h["text"] for h in state["context"]])
    allowed_tools = ", ".join([f'"{t}"' for t in M["guardrails"]["allowed_actions"] if "." in t])
    p = PROMPT.format(
        header=mentor_header(),
        mission=M["mission"],
        principles=", ".join(M["principles"]),
        guardrails=str(M["guardrails"]),
        ctx=ctx, goal=state["goal"], allowed_tools=allowed_tools
    )
    decision = call_llm_json(p)
    return {**state, "decision": decision}

def act_node(state: State) -> State:
    d = state["decision"]; mod = load_tool(d["tool"]); res = mod.run(d.get("args",{}))
    ingest(json.dumps({"tool":d,"res":res}), "tool-log")
    return {**state, "log": state["log"]+[{"tool":d,"res":res}]}

def self_upgrade_node(state: State) -> State:
    d = state["decision"]; mod = load_tool("compose.apply"); res = mod.run({"patch": d["patch_yaml"]})
    ingest(json.dumps({"upgrade":res}), "tool-log")
    return {**state, "log": state["log"]+[{"upgrade":res}]}

def final_node(state: State) -> State:
    return state

def route_after_decide(state: State) -> str:
    ok,msg = policy_ok(state["decision"])
    if not ok: return "FINAL"
    t = state["decision"].get("type","").upper()
    if t=="FINAL": return "FINAL"
    if t=="ACT": return "ACT"
    if t=="SELF_UPGRADE": return "SELF_UPGRADE"
    return "FINAL"

graph = StateGraph(State)
graph.add_node("PLAN", plan_node)
graph.add_node("RETRIEVE", retrieve_node)
graph.add_node("DECIDE", decide_node)
graph.add_node("ACT", act_node)
graph.add_node("SELF_UPGRADE", self_upgrade_node)
graph.add_node("FINAL", final_node)
graph.set_entry_point("PLAN")
graph.add_edge("PLAN","RETRIEVE")
graph.add_edge("RETRIEVE","DECIDE")
graph.add_conditional_edges("DECIDE", route_after_decide, {
    "FINAL":"FINAL","ACT":"ACT","SELF_UPGRADE":"SELF_UPGRADE"
})
graph.add_edge("ACT","FINAL")
graph.add_edge("SELF_UPGRADE","FINAL")
app = graph.compile(checkpointer=MemorySaver())

if __name__=="__main__":
    while True:
        goal=input("\nGoal> ").strip()
        if not goal: continue
        state: State = {"goal": goal, "context": [], "decision": {}, "log": []}
        out = app.invoke(state, config={"configurable": {"thread_id": "cli-session"}})
        print(json.dumps({"decision": out.get("decision",{}), "log": out.get("log",[])}, indent=2))