from sentence_transformers import SentenceTransformer
import psycopg2
import faiss
import numpy as np
import os
import pickle
import tempfile
import json
from typing import List, Dict, Any

class MultiTableEmbeddingSearch:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L12-v2')
        self.index = None
        self.metadata = []
        self.index_path = os.path.join(os.path.dirname(__file__), "faiss.index")
        self.metadata_path = os.path.join(os.path.dirname(__file__), "metadata.pkl")

    def load_from_cache(self) -> bool:
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, "rb") as f:
                    self.metadata = pickle.load(f)
                return True
            except Exception:
                try:
                    os.remove(self.index_path)
                    os.remove(self.metadata_path)
                except OSError:
                    pass
        return False

    def save_to_cache(self):
        try:
            tmp_index = self.index_path + ".tmp"
            faiss.write_index(self.index, tmp_index)
            os.replace(tmp_index, self.index_path)

            dir_name = os.path.dirname(os.path.abspath(self.metadata_path)) or "."
            fd, tmp_meta_path = tempfile.mkstemp(dir=dir_name, prefix="meta_", suffix=".tmp")
            try:
                with os.fdopen(fd, "wb") as tmpf:
                    pickle.dump(self.metadata, tmpf, protocol=pickle.HIGHEST_PROTOCOL)
                os.replace(tmp_meta_path, self.metadata_path)
            finally:
                if os.path.exists(tmp_meta_path):
                    try:
                        os.remove(tmp_meta_path)
                    except OSError:
                        pass
        except Exception as e:
            print(f"Cache save failed: {e}")

    def load_all_embeddings(self):
        if self.load_from_cache():
            return

        DB_CONFIG = {
            'dbname': 'dataware_test',
            'user': 'postgres',
            'password': 'bath123',
            'host': 'localhost',
            'port': 5433
        }

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            SELECT table_name
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
              AND EXISTS (
                  SELECT 1 FROM information_schema.columns c
                  WHERE c.table_schema = 'public' 
                    AND c.table_name = t.table_name 
                    AND c.column_name = 'embedding'
              )
        """)

        tables = [row[0] for row in cur.fetchall()]
        all_embeddings = []

        for table in tables:
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                  AND table_name = %s 
                  AND column_name != 'embedding'
                ORDER BY ordinal_position
            """, (table,))
            columns = [row[0] for row in cur.fetchall()]

            if not columns:
                continue

            select_cols = ", ".join(columns)
            cur.execute(f"""
                SELECT {select_cols}, embedding 
                FROM public.{table} 
                WHERE embedding IS NOT NULL
            """)

            rows = cur.fetchall()
            for row in rows:
                try:
                    embedding_str = row[-1]
                    data = row[:-1]

                    if isinstance(embedding_str, str):
                        embedding_str = embedding_str.strip('[]')
                        embedding_list = [float(x.strip()) for x in embedding_str.split(',')]
                    elif isinstance(embedding_str, list):
                        embedding_list = embedding_str
                    else:
                        continue

                    row_data = {}
                    for col_name, val in zip(columns, data):
                        row_data[col_name] = val

                    self.metadata.append({
                        'table_name': table,
                        'row_data': row_data
                    })

                    all_embeddings.append(embedding_list)

                except Exception:
                    continue

        cur.close()
        conn.close()

        if not all_embeddings:
            raise ValueError("No valid embeddings found!")

        embeddings_array = np.array(all_embeddings, dtype=np.float32)
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)

        self.save_to_cache()

    def search(self, query_text: str, top_k: int = 10):
        if self.index is None:
            raise ValueError("Index not built. Call load_all_embeddings() first.")

        query_embedding = self.model.encode([query_text]).astype(np.float32)
        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                metadata = self.metadata[idx]
                similarity_score = 1 / (1 + distance)
                
                results.append({
                    'similarity_score': round(similarity_score, 4),
                    'data': metadata['row_data']
                })
        
        return json.dumps(results, indent=2, default=str)

    def search_multiple_terms(self, terms: List[str], top_k: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        if self.index is None:
            raise ValueError("Index not built. Call load_all_embeddings() first.")
        
        results = {}
        
        for term in terms:
            if term and len(term.strip()) >= 3:
                query_embedding = self.model.encode([term]).astype(np.float32)
                distances, indices = self.index.search(query_embedding, top_k)
                
                term_results = []
                for distance, idx in zip(distances[0], indices[0]):
                    if idx < len(self.metadata):
                        metadata = self.metadata[idx]
                        similarity_score = 1 / (1 + distance)
                        
                        term_results.append({
                            'similarity_score': round(similarity_score, 4),
                            'data': metadata['row_data']
                        })
                
                if term_results:
                    results[term] = term_results
        
        return results