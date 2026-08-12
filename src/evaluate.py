"""
Évaluation RIGOUREUSE du RAG contre une vérité terrain connue (data/eval.json).

Deux niveaux :
  1. Récupération (sans clé API) : le bon chiffre figure-t-il dans les k passages ?
     -> taux de rappel (recall@k).
  2. Réponse (si ANTHROPIC_API_KEY) : la réponse de Claude contient-elle le bon
     chiffre ? Les questions hors-documents doivent renvoyer le refus exact
     (garde-fou anti-hallucination).

Lancer : python src/evaluate.py
"""
from __future__ import annotations
import json
import os
from pathlib import Path

from rag import DATA, answer, retrieve

REFUS = "Je ne trouve pas cette information dans les documents."
K = 4


def load_eval() -> list[dict]:
    return json.loads((DATA / "eval.json").read_text(encoding="utf-8"))


def hit_retrieval(passages: list[dict], expect: str) -> bool:
    return any(expect in p["text"] for p in passages)


def main() -> None:
    cases = load_eval()
    use_llm = bool(os.environ.get("ANTHROPIC_API_KEY"))
    r_ok = a_ok = 0
    in_ctx = [c for c in cases if c["expect"] != "__ABSENT__"]

    print(f"Évaluation RAG — {len(cases)} questions (k={K}, LLM={'oui' if use_llm else 'non'})\n")
    for c in cases:
        q, expect = c["question"], c["expect"]
        absent = expect == "__ABSENT__"
        passages = retrieve(q, K)

        if not absent:
            hit = hit_retrieval(passages, expect)
            r_ok += hit
            tag = "OK " if hit else "MISS"
            print(f"[récup {tag}] {q}  (attendu ~{expect}, top1={passages[0]['doc']})")

        if use_llm:
            resp = answer(q, K)["answer"]
            if absent:
                good = REFUS in resp
            else:
                good = expect in resp
            a_ok += good
            print(f"    -> {'OK  ' if good else 'FAUX'} {resp[:90].strip()}")

    print(f"\nRappel récupération : {r_ok}/{len(in_ctx)} = {r_ok / len(in_ctx):.0%}")
    if use_llm:
        print(f"Exactitude réponses : {a_ok}/{len(cases)} = {a_ok / len(cases):.0%} "
              f"(dont refus correct sur les questions hors-documents)")
    else:
        print("(réponses non évaluées : définir ANTHROPIC_API_KEY pour tester la génération)")


if __name__ == "__main__":
    main()
