import re
from typing import Dict, Any, List
import numpy as np
import os
import torch
from AI_ChatBot.entity import QueryConfig
from AI_ChatBot.logging import logger
from supabase import create_client, Client
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface.embeddings.huggingface_endpoint import HuggingFaceEndpointEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

class QueryProcessor:
    """
    Processes user queries: preprocessing, intent analysis, embedding.
    """
    def __init__(self,params:QueryConfig):
        self.params = params
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.api_key = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        self.api = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            logger.info("Using Huggingface embeddings")
            self.embedding_model = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            task="feature-extraction",          # required for embedding models
            huggingfacehub_api_token=self.api_key
        )
        elif self.api:
            logger.info("Using OpenAI embeddings")
            self.embedding_model = OpenAIEmbeddings(api_key=self.api,model="text-embedding-3-small")
        else:
            logger.error("No Embedding Model")
        self.supabase_url =  os.getenv("SUPABASE_URL") 
        self.supabase_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.table_name = "chunks"

    def preprocess_query(self, query: str) -> str:
        # Normalize whitespace
        q = re.sub(r'\s+', ' ', query.strip())
        # Remove special chars except ?.,
        q = re.sub(r'[^\w\s?.,-]', '', q)
        # Ensure question mark if starts with interrogative
        if re.match(r'^(?:what|when|where|who|why|how|is|are|can|could|would|should|do|does|did)\b', q, re.I):
              if not q.endswith("?"):
                  q += "?"
        return q

    def analyze_intent(self, query: str) -> Dict[str, Any]:
        # Simple heuristic: detect question type
        ql = query.lower()
        if ql.startswith("what is") or ql.startswith("define"):
            qtype = "definition"
        elif "compare" in ql or "vs" in ql:
            qtype = "comparison"
        elif ql.startswith("how") or ql.startswith("explain"):
            qtype = "explanation"
        else:
            qtype = "general"
        # You may extend with keyword/entity extraction via spaCy or simple splitting
        return {"question_type": qtype}

    def _normalize(self, vec: List[float]) -> List[float]:
        """
        L2-normalize a vector so cosine similarity can be done via Euclidean <-> if needed.
        pgvector `<=>` operator computes cosine distance directly, so normalization is optional.
        But normalizing ensures Euclidean `<->` works as cosine if pgvector version uses `<->`.
        """
        arr = np.array(vec, dtype="float32")
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr /= norm
        return arr.tolist()
    def search_similar_chunks(self,query:str)->List[Dict]:
        if hasattr(self.embedding_model, "embed_query"):
            vec = self.embedding_model.embed_query(query)
        else:
            # Some embedder only has embed_documents
            vec = self.embedding_model.embed_documents([query])[0]
        emb = self._normalize(vec)
        try:
          resp = self.supabase.rpc("match_chunks",{
              "query_embedding":emb,
              "match_count":self.params.top_k
          }).execute()
        except Exception as e:
          print("Supabase RPC error:", e)
          return []
        data = getattr(resp,"data",None) or []
        results = []
        for row in data:
          score = row.get("similarity",0.0)
          if score < self.params.similarity_threshold:
            continue
          results.append({
              'score':score,
              "text": row.get("text",""),
              "metadata": row.get("metadata",{})
          })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def process(self, raw_query: str) -> Dict[str, Any]:
        """
        Full pipeline up to retrieval. Returns intent, preprocessed query, and retrieved chunks.
        """
        pre_q = self.preprocess_query(raw_query)
        intent = self.analyze_intent(pre_q)
        retrieved = self.search_similar_chunks(pre_q)
        # Attach intent and preprocessed query to results
        return {
            "preprocessed_query": pre_q,
            "intent": intent,
            "retrieved_chunks": retrieved
        }
    
