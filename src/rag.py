"""
Cœur du RAG : ingestion PDF -> chunking -> embeddings -> recherche vectorielle,
puis génération d'une réponse SOURCÉE avec Claude (garde-fous anti-hallucination).

- La récupération (retrieve) fonctionne SANS clé API.
- La génération (generate/answer) nécessite ANTHROPIC_API_KEY.
"""
from __future__ import annotations
import glob
import json
import os
from pathlib import Path

import numpy as np
import pdfplumber
from fastembed import TextEmbedding

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CHUNKS_JSON = DATA / "chunks.json"
EMB_NPY = DATA / "embeddings.npy"
CLAUDE_MODEL = "claude-sonnet-5"

_embedder: TextEmbedding | None = None


def embedder() -> TextEmbedding:
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(MODEL)
    return _embedder


def embed(texts: list[str]) -> np.ndarray:
    vecs = np.array(list(embedder().embed(texts)), dtype=np.float32)
    vecs /= (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9)   # normalise -> cosine
    return vecs


def chunk_page(text: str, doc: str, page: int, max_chars: int = 400) -> list[dict]:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    chunks, buf = [], ""
    for l in lines:
        if buf and len(buf) + len(l) + 1 > max_chars:
            chunks.append(buf); buf = l
        else:
            buf = (buf + " " + l).strip()
    if buf:
        chunks.append(buf)
    return [{"doc": doc, "page": page, "text": c} for c in chunks if len(c) > 15]


def build_index() -> int:
    """Ingère tous les PDF de data/ et construit l'index vectoriel."""
    chunks: list[dict] = []
    for pdf in sorted(glob.glob(str(DATA / "*.pdf"))):
        name = Path(pdf).name
        with pdfplumber.open(pdf) as doc:
            for i, page in enumerate(doc.pages, start=1):
                chunks += chunk_page(page.extract_text() or "", name, i)
    vecs = embed([c["text"] for c in chunks])
    CHUNKS_JSON.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    np.save(EMB_NPY, vecs)
    return len(chunks)


def _load():
    chunks = json.loads(CHUNKS_JSON.read_text(encoding="utf-8"))
    return chunks, np.load(EMB_NPY)


def retrieve(query: str, k: int = 4) -> list[dict]:
    """Renvoie les k passages les plus pertinents avec leur source (citation)."""
    chunks, vecs = _load()
    qv = embed([query])[0]
    scores = vecs @ qv
    top = np.argsort(scores)[::-1][:k]
    return [{**chunks[i], "score": round(float(scores[i]), 3)} for i in top]


def _context(passages: list[dict]) -> str:
    return "\n\n".join(
        f"[{i+1}] (source : {p['doc']}, p.{p['page']})\n{p['text']}"
        for i, p in enumerate(passages))


SYSTEM = (
    "Tu es un analyste financier. Réponds UNIQUEMENT à partir des extraits fournis. "
    "Cite tes sources entre crochets, ex. [1], [2]. "
    "Si l'information n'est pas dans les extraits, réponds exactement : "
    "\"Je ne trouve pas cette information dans les documents.\" "
    "Ne calcule que si les chiffres nécessaires sont présents. Sois concis et factuel."
)


def generate(query: str, passages: list[dict]) -> str:
    """Génère une réponse sourcée avec Claude. Nécessite ANTHROPIC_API_KEY."""
    import anthropic
    client = anthropic.Anthropic()   # lit ANTHROPIC_API_KEY
    msg = client.messages.create(
        model=CLAUDE_MODEL, max_tokens=500, system=SYSTEM,
        messages=[{"role": "user",
                   "content": f"Extraits :\n{_context(passages)}\n\nQuestion : {query}"}],
    )
    return msg.content[0].text


def answer(query: str, k: int = 4) -> dict:
    passages = retrieve(query, k)
    out = {"query": query, "passages": passages}
    if os.environ.get("ANTHROPIC_API_KEY"):
        out["answer"] = generate(query, passages)
    else:
        out["answer"] = "(génération désactivée : définir ANTHROPIC_API_KEY)"
    return out
