# Garde-fous anti-hallucination

Le risque n°1 d'un assistant LLM sur des documents, c'est d'**inventer** un
chiffre plausible mais faux. Ce projet empile quatre garde-fous et les **mesure**.

## 1. Ancrage strict sur les sources (grounding)

La réponse n'est jamais générée à partir de la mémoire du modèle : on récupère
d'abord les passages pertinents (embeddings locaux + similarité cosinus), et le
prompt système impose de répondre **uniquement** à partir de ces extraits.

## 2. Citation obligatoire

Le modèle doit citer ses sources entre crochets (`[1]`, `[2]`), chaque extrait
étant étiqueté `(source : fichier, page)`. Une affirmation sans source est
détectable — et l'utilisateur peut vérifier dans l'expander « Sources ».

## 3. Refus explicite (le garde-fou clé)

Consigne système : si l'information n'est pas dans les extraits, répondre
**exactement** :

> Je ne trouve pas cette information dans les documents.

C'est ce qui distingue un assistant fiable d'un perroquet : savoir dire « je ne
sais pas » plutôt que d'halluciner un cours de bourse inexistant.

## 4. Pas de calcul hors-sol

Le modèle ne calcule (ex. une croissance) que si les chiffres nécessaires sont
présents dans les extraits.

## Mesure

`src/evaluate.py` teste ces garde-fous contre une **vérité terrain connue**
(`data/eval.json`, chiffres synthétiques maîtrisés) :

- **Rappel de récupération** : le bon chiffre est-il dans les *k* passages ? → **7/7 = 100 %** (k=4).
- **Exactitude des réponses** (avec `ANTHROPIC_API_KEY`) : la réponse contient
  le bon chiffre, **et** les questions hors-documents déclenchent le refus exact.

Les données sont synthétiques mais réalistes, précisément pour permettre une
évaluation rigoureuse — le pipeline tourne à l'identique sur de vrais PDF
publics déposés dans `data/`.
