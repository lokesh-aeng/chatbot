from fastapi import FastAPI,HTTPException
import uvicorn
import os
import time
import uuid
from typing import List,Tuple
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from pydantic import BaseModel
from AI_ChatBot.pipeline.queryprocessing import QueryProcessingPipeline
from AI_ChatBot.pipeline.cache import CacheTrainingPipeline
from AI_ChatBot.components.rag import RAG
from supabase import create_client, Client

load_dotenv()
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

app = FastAPI()
cache_pipeline = CacheTrainingPipeline()
cache = cache_pipeline.main()

origins = [
    "http://localhost:3000",  # Vite dev server
    "https://react-frontend-cr23.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str
    cached: bool
    elapsed_time: float

queryProcessing = QueryProcessingPipeline()
query_processor = queryProcessing.main()

rag = RAG(query_processor)
graph = rag.build_graph()


@app.get('/',tags=["authentication"])
async def index():
    return RedirectResponse(url='/docs')

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    start_ts = time.time()

    session_id = req.session_id or str(uuid.uuid4())
    user = req.message

    # fetch & sort history
    history = []
    try:
        resp = supabase.table("chat_history") \
            .select("role,content,timestamp") \
            .eq("session_id", session_id) \
            .execute()
        rows = resp.data or []
        rows.sort(key=lambda r: r["timestamp"])
        for r in rows:
            history.append({"role": r["role"], "content": r["content"]})
    except Exception:
        history = []

    # history.append({"role": "user", "content": user})

    history_pairs: List[Tuple[str,str]] = []
    # pair up user→assistant where possible
    for i in range(len(history)-1):
        if history[i]["role"] == "user" and history[i+1]["role"] == "assistant":
            history_pairs.append((history[i]["content"], history[i+1]["content"]))
    supabase.table("chat_history").insert({
        "session_id": session_id,
        "role": "user",
        "content": user
    }).execute()
    cache_hit = cache.get_response(user, history_pairs)
    if cache_hit:
        supabase.table("chat_history").insert({
            "session_id": session_id,
            "role": "assistant",
            "content": cache_hit["response_text"]
        }).execute()

        elapsed = time.time() - start_ts
        return ChatResponse(
            session_id=session_id,
            response=cache_hit["response_text"],
            cached=True,
            elapsed_time=round(elapsed, 4)
        )
    try:
        supabase.table("chat_history").insert({
            "session_id": session_id,
            "role": "user",
            "content": user
        }).execute()
    except Exception:
        pass
    
    flat_history = history + [{"role": "user", "content": user}]
    # invoke graph
    try:
        result = graph.invoke({"messages": flat_history})
        bot = result["messages"][-1].content
    except Exception:
        raise HTTPException(500, "Internal error")

    try:
        supabase.table("chat_history").insert({
            "session_id": session_id,
            "role": "assistant",
            "content": bot
        }).execute()
    except Exception:
        pass

    # # persist new turns
    # try:
    #     supabase.table("chat_history").insert([
    #         {"session_id": session_id, "role": "user", "content": user},
    #         {"session_id": session_id, "role": "assistant", "content": bot},
    #     ]).execute()
    # except Exception:
    #     pass
    artifacts = []
    for m in reversed(result["messages"]):
        if getattr(m, "type", None) == "tool" and hasattr(m, "artifact"):
            artifacts = m.artifact
            break
    cache.set_response(
        user,
        history_pairs,
        response_text=bot,
        source_chunks=artifacts,
        model=result.get("model", ""),
        is_fallback=result.get("is_fallback", False),
        latency=result.get("latency", 0.0)
    )
    elapsed = time.time() - start_ts
    return ChatResponse(
        session_id=session_id,
        response=bot,
        cached=False,
        elapsed_time=round(elapsed, 4)
    )

    # return ChatResponse(session_id=session_id, response=bot)

if  __name__ == "__main__":
    uvicorn.run(app,host='localhost',port = 8000)
