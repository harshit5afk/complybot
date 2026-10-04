"""
agents.py
Implements the ComplyBot multi-agent architecture:

  Router Agent        -> classifies query into a domain + detects language
  Retriever Agent      -> RAG search over the standards corpus (ChromaDB)
  Certification Agent  -> maps product/domain to certification scheme + process
  Consumer Agent        -> simpler-language responses for general consumer queries
  Hallmarking Agent     -> rule-based (no LLM needed) purity/HUID/verification info
  Lab Finder Agent      -> rule-based lookup of BIS-recognized labs
  Translator            -> LLM-based translation layer (English <-> Hindi)

Each public function returns a dict: {"agent": <name>, "answer": <text>, "citations": [...]}
"""

import os
import json
import time
import chromadb
import ollama

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "qwen2.5:7b-instruct"  # swap for a smaller model if your GPU struggles, see README
COLLECTION_NAME = "bis_standards"

# ---------------------------------------------------------------------------
# Load structured data once at import time
# ---------------------------------------------------------------------------
with open(os.path.join(DATA_DIR, "certification_schemes.json"), encoding="utf-8") as f:
    CERTIFICATION_SCHEMES = json.load(f)["schemes"]

with open(os.path.join(DATA_DIR, "hallmarking_rules.json"), encoding="utf-8") as f:
    HALLMARKING_RULES = json.load(f)

with open(os.path.join(DATA_DIR, "labs.json"), encoding="utf-8") as f:
    LABS = json.load(f)["labs"]

# Chroma client (lazy-loaded so the module can be imported even before ingest.py has run)
_chroma_client = None
_collection = None


def _get_collection():
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = _chroma_client.get_collection(COLLECTION_NAME)
    return _collection


def _ollama_chat(system_prompt: str, user_prompt: str, retries: int = 2) -> str:
    """Call Ollama chat with automatic retry on transient failures (e.g. GPU crash)."""
    for attempt in range(retries + 1):
        try:
            response = ollama.chat(
                model=CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response["message"]["content"].strip()
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)  # exponential backoff: 1s, 2s
                continue
            raise


# ---------------------------------------------------------------------------
# Router Agent
# ---------------------------------------------------------------------------
# Keyword-first routing for reliability/determinism (avoids LLM misclassification
# during a live demo); falls back to an LLM classifier only if no keywords match.

_ROUTING_KEYWORDS = {
    "hallmarking": ["hallmark", "huid", "gold purity", "silver purity", "karat", "jewellery", "jewelry", "jeweller"],
    "lab_finder": ["lab", "laboratory", "testing lab", "test my", "where can i test", "which lab"],
    "certification": ["certificat", "license", "licence", "isi mark", "crs", "registration scheme", "how do i get"],
    "consumer": ["complaint", "verify my product", "is this genuine", "consumer right", "fake product", "file a complaint"],
}


def route_query(query: str) -> str:
    """Returns one of: 'hallmarking', 'lab_finder', 'certification', 'consumer', 'standards' """
    q_lower = query.lower()
    for domain, keywords in _ROUTING_KEYWORDS.items():
        if any(kw in q_lower for kw in keywords):
            return domain

    # Fallback: ask the LLM to classify when no keyword matched
    system = (
        "You are a query router for a BIS (Bureau of Indian Standards) assistant. "
        "Classify the user's query into exactly one of these domains: "
        "hallmarking, lab_finder, certification, consumer, standards. "
        "Reply with only the single domain word, nothing else."
    )
    try:
        result = _ollama_chat(system, query).strip().lower()
        if result in _ROUTING_KEYWORDS or result == "standards":
            return result
    except Exception:
        pass
    return "standards"  # safe default


def detect_language(query: str) -> str:
    """Very lightweight heuristic: Devanagari script present -> Hindi, else English."""
    for ch in query:
        if "\u0900" <= ch <= "\u097F":
            return "hi"
    return "en"


# ---------------------------------------------------------------------------
# Retriever Agent (standards Q&A + product -> standard recommendation)
# ---------------------------------------------------------------------------
def retriever_agent(query: str) -> dict:
    collection = _get_collection()
    embed_response = ollama.embeddings(model=EMBED_MODEL, prompt=query)
    query_embedding = embed_response["embedding"]

    results = collection.query(query_embeddings=[query_embedding], n_results=3)

    retrieved_chunks = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []

    if not retrieved_chunks:
        return {
            "agent": "Retriever Agent",
            "answer": "I couldn't find a matching standard in the current knowledge base for that query.",
            "citations": [],
        }

    context_block = "\n\n".join(
        f"[Source: {m['source']} | Section: {m['section']}]\n{c}"
        for c, m in zip(retrieved_chunks, metadatas)
    )

    system = (
        "You are the Retriever Agent for ComplyBot, a BIS (Bureau of Indian Standards) assistant. "
        "Answer the user's question using ONLY the provided context below. "
        "Always cite the source document and section at the end of your answer. "
        "If the context does not contain the answer, say you don't have that information "
        "rather than guessing."
    )
    user = f"Context:\n{context_block}\n\nQuestion: {query}"
    answer = _ollama_chat(system, user)

    citations = [f"{m['source']} — {m['section']}" for m in metadatas]
    return {"agent": "Retriever Agent", "answer": answer, "citations": citations}


# ---------------------------------------------------------------------------
# Certification & Licensing Agent
# ---------------------------------------------------------------------------
def certification_agent(query: str) -> dict:
    # Find the most relevant scheme by simple keyword overlap against applies_to
    q_lower = query.lower()
    best_match = None
    for scheme in CERTIFICATION_SCHEMES:
        for product in scheme["applies_to"]:
            if product.lower() in q_lower:
                best_match = scheme
                break
        if best_match:
            break

    if not best_match:
        # Fall back to the Retriever agent, which has fuller document context
        return retriever_agent(query)

    steps_text = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(best_match["process_steps"]))
    context = (
        f"Scheme: {best_match['scheme_name']}\n"
        f"Applies to: {', '.join(best_match['applies_to'])}\n"
        f"Description: {best_match['description']}\n"
        f"Process steps:\n{steps_text}\n"
        f"Typical timeline: {best_match['typical_timeline']}"
    )

    system = (
        "You are the Certification & Licensing Agent for ComplyBot. "
        "Explain the certification scheme and process clearly to the user based on the "
        "structured data provided. Keep it practical and step-by-step."
    )
    answer = _ollama_chat(system, f"Scheme data:\n{context}\n\nUser question: {query}")

    citation = f"BIS Certification Scheme Database — {best_match['scheme_name']}"
    if best_match.get("source_url"):
        citation += f" ({best_match['source_url']})"

    return {
        "agent": "Certification & Licensing Agent",
        "answer": answer,
        "citations": [citation],
    }


# ---------------------------------------------------------------------------
# Consumer Query Agent
# ---------------------------------------------------------------------------
def consumer_agent(query: str) -> dict:
    system = (
        "You are the Consumer Query Agent for ComplyBot, a BIS assistant. "
        "Answer in simple, plain language suitable for an everyday consumer (not a technical "
        "audience). If the question is about verifying a product or filing a complaint, "
        "mention that consumers can use the BIS CARE app or the National Consumer Helpline "
        "(1915) for complaints. Keep the answer short and reassuring."
    )
    answer = _ollama_chat(system, query)
    return {
        "agent": "Consumer Query Agent",
        "answer": answer,
        "citations": ["BIS Consumer Services — General Guidance"],
    }


# ---------------------------------------------------------------------------
# Hallmarking Agent (rule-based, no LLM required for the core lookup)
# ---------------------------------------------------------------------------
def hallmarking_agent(query: str) -> dict:
    q_lower = query.lower()

    if "huid" in q_lower or "verify" in q_lower or "check" in q_lower:
        answer = HALLMARKING_RULES["huid_explanation"] + "\n\nTo verify a hallmark:\n" + "\n".join(
            f"- {step}" for step in HALLMARKING_RULES["how_to_verify"]
        )
        return {"agent": "Hallmarking Agent", "answer": answer, "citations": ["BIS Hallmarking Rules — HUID & Verification"]}

    if "silver" in q_lower:
        grades = "\n".join(
            f"- {g['grade']}: {g['description']}" for g in HALLMARKING_RULES["purity_grades_silver"]
        )
        answer = f"Silver purity grades under BIS hallmarking:\n{grades}"
        return {"agent": "Hallmarking Agent", "answer": answer, "citations": ["BIS Hallmarking Rules — Silver Purity Grades"]}

    # default: gold purity info
    grades = "\n".join(
        f"- {g['karat']} ({g['fineness']} fineness): {g['description']}" for g in HALLMARKING_RULES["purity_grades_gold"]
    )
    answer = (
        f"Gold purity grades under BIS hallmarking:\n{grades}\n\n"
        f"{HALLMARKING_RULES['jeweller_registration_note']}"
    )
    return {"agent": "Hallmarking Agent", "answer": answer, "citations": ["BIS Hallmarking Rules — Gold Purity Grades"]}


# ---------------------------------------------------------------------------
# Lab Finder Agent (rule-based lookup)
# ---------------------------------------------------------------------------
def lab_finder_agent(query: str) -> dict:
    q_lower = query.lower()
    matches = []
    for lab in LABS:
        if any(cat.lower() in q_lower for cat in lab["categories"]) or lab["region"].lower() in q_lower or lab["city"].lower() in q_lower:
            matches.append(lab)

    if not matches:
        matches = LABS[:3]  # fallback: show a few general options

    lines = [f"- {lab['name']} ({lab['city']}, {lab['region']} region) — tests: {', '.join(lab['categories'])}" for lab in matches]
    answer = "Here are some BIS-recognized testing labs that may be relevant:\n" + "\n".join(lines)
    answer += "\n\n(Note: this is sample/illustrative lab data for demo purposes — verify against the official BIS lab directory before contacting.)"

    return {
        "agent": "Lab Finder Agent",
        "answer": answer,
        "citations": ["BIS Recognized Laboratories Directory (sample data)"],
    }


# ---------------------------------------------------------------------------
# Translator
# ---------------------------------------------------------------------------
def translate(text: str, target_lang: str) -> str:
    if target_lang == "en":
        return text
    lang_names = {"hi": "Hindi"}
    target_name = lang_names.get(target_lang, target_lang)
    system = f"Translate the following text into {target_name}. Only output the translation, nothing else."
    try:
        return _ollama_chat(system, text)
    except Exception:
        return text  # fail open — show English rather than erroring out


# ---------------------------------------------------------------------------
# Top-level entry point used by main.py
# ---------------------------------------------------------------------------
def handle_query(query: str, language: str = None) -> dict:
    try:
        domain = route_query(query)
        lang = language or detect_language(query)

        if domain == "hallmarking":
            result = hallmarking_agent(query)
        elif domain == "lab_finder":
            result = lab_finder_agent(query)
        elif domain == "certification":
            result = certification_agent(query)
        elif domain == "consumer":
            result = consumer_agent(query)
        else:
            result = retriever_agent(query)

        result["answer"] = translate(result["answer"], lang)
        result["domain"] = domain
        result["language"] = lang
        return result
    except Exception as e:
        return {
            "agent": "System",
            "domain": "error",
            "language": language or "en",
            "answer": f"Ollama model error — the local LLM may have crashed. Please try again in a few seconds. (Details: {str(e)[:150]})",
            "citations": [],
        }
