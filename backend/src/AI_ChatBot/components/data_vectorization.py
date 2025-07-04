import os
import torch
import numpy as np
from datetime import datetime
from typing import List
from dotenv import load_dotenv
from collections import defaultdict
from supabase import create_client, Client
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from AI_ChatBot.logging import logger

class DataVectorization:
    def __init__(self, params):
        """
        Initialize the vectorization pipeline.
        """
        load_dotenv()

        self.supabase_url =  os.getenv("SUPABASE_URL") 
        self.supabase_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found")

        self.params = params

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.api = os.getenv("OPENAI_API_KEY")

        if self.api:
            logger.info("Using OpenAI embeddings")
            self.model = OpenAIEmbeddings(api_key=self.api)
        else:
            logger.info('Using HuggingFaceEmbeddings')
            self.model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': device}
            )

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

    def get_unique_fields(self,chunks: List[Document]) -> List[str]:
        """
        Extract a set of unique filenames from a list of document chunks.

        Args:
            chunks (List[Document]): List of Document objects.

        Returns:
            Set[str]: Set of unique filenames.
        """
        return list(set(
            chunk.metadata.get("filename", "unknown") for chunk in chunks
        ))

    def upsert_document_details(self,chunks: List[Document]):
        """
        Upsert document details in Supabase.
        """
        unique_filenames = self.get_unique_fields(chunks)
        mp = defaultdict(str)
        unique_pairs = {
            (
                chunk.metadata.get("filename", "unknown"),
                chunk.metadata.get("content_hash", "unknown")
            )
            for chunk in chunks
        }
        for fname,hash in unique_pairs:
          mp[fname] = hash
        doc_id = {}
        for filename in unique_filenames:
          resp = self.supabase.table(self.params.docs).select("id","version").eq("title",filename).execute()
          data = resp.data
          if data:
            doc = data[0]
            document_id = doc["id"]
            new_version = doc["version"] + 1
            update_resp = self.supabase.table(self.params.docs).update({
                "version": new_version,
                "updated_at": datetime.now().isoformat()
            }).eq("id", document_id).execute()
            doc_id[filename] = document_id
          else:
              # Insert new document row
              ext = filename.split('.')[-1]
              insert_resp = self.supabase.table(self.params.docs).insert({
                  "id": mp[filename],
                  "title": filename,
                  "file_type": filename.split('.')[-1],
                  "version": 1,
                  "updated_at": datetime.now().isoformat()

              }).execute()
              new_doc = insert_resp.data[0]
              doc_id[filename] = new_doc["id"]
        return doc_id

    def batch_embed(self, texts: List[str], batch_size: int):
        """Create embeddings in batches to avoid memory issues."""
        logger.info("Batch embedding along with normalization has started")
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeds = self.model.embed_documents(batch)
            for emb in batch_embeds:
              arr = np.array(emb, dtype="float32")
              norm = np.linalg.norm(arr)
              if norm > 0:
                  arr /= norm
              all_embeddings.append(arr.tolist())
        logger.info("Batch embedding along with normalization has completed")
        return all_embeddings
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
    def ingest_chunks(self,chunks:List[Document]):
        logger.info("Document details Upsertion Started")
        doc_ids = self.upsert_document_details(chunks)
        logger.info("Document details upserted")
        records = []
        text = [doc.page_content for doc in chunks]
        embeddings = self.batch_embed(text, self.params.batch_embed)
        logger.info("Records generation Started")
        for doc,emb in zip(chunks,embeddings):
            meta_data = {
                "source": doc.metadata.get("source", "unknown"),
                "filename": doc.metadata.get("filename", "unknown"),
                'languages': doc.metadata.get('languages', 'unknown'),
                'category': doc.metadata.get('category', 'unknown'),
                'content_hash': doc.metadata.get('content_hash', 'unknown'),
                'page_number': doc.metadata.get('page_number')
            }
        #   if hasattr(self.model, "embed_documents"):
        #       vec = self.model.embed_documents([doc.page_content])[0]
        #   else:
        #       vec = self.model.embed_query(doc.page_content)
        #   emb = self._normalize(vec)
            records.append({
                    "id": doc.metadata.get("chunk_id", "unknown"),
                    "document_id": doc_ids[doc.metadata.get("filename", "unknown")],
                    "chunk_index": doc.metadata.get("chunk_idx", "unknown"),
                    "text": doc.page_content,
                    "embedding": emb,
                    "metadata": meta_data or {},
                    "updated_at": datetime.now().isoformat()
                })
        logger.info("Records generation Ended")
        batch_size = self.params.batch_table
        for i in range(0,len(records),batch_size):
            batch = records[i:i+batch_size]
            response = self.supabase.table(self.params.chunks).upsert(
                batch,
                on_conflict="id"
            ).execute()
            logger.info(f"Upserted chunks in the batch {i}–{i + len(batch)}")
            if not response.data:
                raise Exception(f"Supabase insert failed: {response}")