"""
三层记忆存储
  短期：内存字典，保存当前会话最近 5 轮完整对话（user_query + assistant_reply）
  中期：SQLite，保存每轮摘要，按时间排序，用于追问识别
  长期：Chroma 向量库，保存跨会话语义记忆，用于相似话题检索
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict
from collections import deque

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "memory.db"
CHROMA_PATH = str(Path(__file__).parent.parent / "chroma_db")
SHORT_TERM_LIMIT = 5  # 短期记忆保留轮数


# ─────────────────────────────────────────────
# 短期记忆（内存）
# ─────────────────────────────────────────────

_short_term: Dict[str, deque] = {}  # session_id → deque of {user_query, assistant_reply}


def add_short_term(session_id: str, user_query: str, assistant_reply: str):
    if session_id not in _short_term:
        _short_term[session_id] = deque(maxlen=SHORT_TERM_LIMIT)
    _short_term[session_id].append({
        "user_query": user_query,
        "assistant_reply": assistant_reply,
    })


def get_short_term(session_id: str) -> List[dict]:
    """返回最近 N 轮完整对话，按时间升序"""
    return list(_short_term.get(session_id, []))


# ─────────────────────────────────────────────
# 中期记忆（SQLite）
# ─────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_query TEXT NOT NULL,
                summary    TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON memories(session_id)")
        conn.commit()
    logger.info(f"[MemoryDB] SQLite initialized at {DB_PATH}")


def save_mid_term(session_id: str, user_query: str, summary: str):
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO memories (session_id, user_query, summary, created_at) VALUES (?, ?, ?, ?)",
            (session_id, user_query, summary, datetime.utcnow().isoformat())
        )
        conn.commit()


def load_last_mid_term(session_id: str) -> Optional[dict]:
    """取最近一条中期记忆"""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT user_query, summary, created_at FROM memories WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
            (session_id,)
        ).fetchone()
    return dict(row) if row else None


def load_all_mid_term(session_id: str, exclude_last: bool = False) -> List[dict]:
    """取所有中期记忆"""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT user_query, summary, created_at FROM memories WHERE session_id = ? ORDER BY created_at DESC",
            (session_id,)
        ).fetchall()
    result = [dict(r) for r in rows]
    if exclude_last and result:
        result = result[1:]
    return result


# ─────────────────────────────────────────────
# 长期记忆（Chroma 向量库）
# ─────────────────────────────────────────────

_chroma_client = None
_chroma_collection = None


def _get_chroma():
    global _chroma_client, _chroma_collection
    if _chroma_collection is None:
        import chromadb
        from chromadb.utils.embedding_functions import EmbeddingFunction

        class DashscopeEmbedding(EmbeddingFunction):
            """用通义千问 text-embedding-v3 做向量化，不需要本地模型"""
            def __call__(self, input):
                import dashscope
                from dashscope import TextEmbedding
                dashscope.api_key = settings.dashscope_api_key
                results = []
                for text in input:
                    resp = TextEmbedding.call(
                        model="text-embedding-v3",
                        input=text,
                    )
                    if resp.status_code == 200:
                        results.append(resp.output["embeddings"][0]["embedding"])
                    else:
                        results.append([0.0] * 1024)
                return results

        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        # 删掉旧集合避免 embedding 函数冲突
        try:
            _chroma_client.delete_collection("long_term_memory")
        except Exception:
            pass
        _chroma_collection = _chroma_client.get_or_create_collection(
            name="long_term_memory",
            embedding_function=DashscopeEmbedding(),
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"[MemoryDB] Chroma initialized at {CHROMA_PATH}")
    return _chroma_collection


def save_long_term(session_id: str, user_query: str, summary: str, doc_id: str):
    """存入向量库，用 Chroma 内置 embedding（all-MiniLM-L6-v2）"""
    try:
        col = _get_chroma()
        col.upsert(
            ids=[doc_id],
            documents=[f"{user_query} {summary}"],
            metadatas=[{"session_id": session_id, "user_query": user_query,
                        "summary": summary, "created_at": datetime.utcnow().isoformat()}],
        )
    except Exception as e:
        logger.warning(f"[MemoryDB] Chroma save failed: {e}")


def search_long_term(query: str, session_id: str, n_results: int = 3) -> List[dict]:
    """语义检索，返回最相关的历史记忆"""
    try:
        col = _get_chroma()
        results = col.query(
            query_texts=[query],
            n_results=n_results,
            where={"session_id": session_id},
        )
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        return [
            {**m, "score": 1 - d}  # cosine distance → similarity
            for m, d in zip(metadatas, distances)
            if (1 - d) > 0.5  # 相似度阈值
        ]
    except Exception as e:
        logger.warning(f"[MemoryDB] Chroma search failed: {e}")
        return []
