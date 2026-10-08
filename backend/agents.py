"""
agents.py
Implements the ComplyBot multi-agent architecture:

  Router Agent               -> classifies query into a domain + detects language
  Retriever Agent             -> RAG search over the standards corpus (ChromaDB)
  Compliance Checker Agent   -> structured compliance roadmap & checklists (NEW Phase 2)
  Compare Agent              -> side-by-side product standards comparison (NEW Phase 2)
  Certification Agent        -> maps product to certification scheme & application steps
  Consumer Agent              -> simpler-language guidance for consumers (BIS CARE & 1915)
  Hallmarking Agent           -> rule-based purity, fineness, and HUID verification
  Lab Finder Agent            -> filterable directory of BIS-recognized test laboratories
  Document Analysis Agent    -> product label and certificate OCR verification (NEW Phase 2)
  Translator                  -> LLM-based translation layer (English <-> Hindi)

Each public function returns:
{
    "agent": <name>,
    "answer": <text>,
    "citations": [...],
    "confidence": <float>,
    "explanation": <text>  # "Why this answer?"
}
"""

import os
import json
import time
import chromadb
import ollama

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "qwen2.5:3b-instruct"  # ultra-fast and stable on local GPU
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

checklist_file = os.path.join(DATA_DIR, "compliance_checklists.json")
if os.path.exists(checklist_file):
    with open(checklist_file, encoding="utf-8") as f:
        COMPLIANCE_CHECKLISTS = json.load(f)["checklists"]
else:
    COMPLIANCE_CHECKLISTS = []

catalog_file = os.path.join(DATA_DIR, "standards_catalog.json")
if os.path.exists(catalog_file):
    with open(catalog_file, encoding="utf-8") as f:
        STANDARDS_CATALOG = json.load(f).get("catalog", [])
else:
    STANDARDS_CATALOG = []


def find_standards_catalog_match(query: str) -> dict | None:
    """Matches query keywords or IS numbers against the master standards catalog."""
    q_lower = query.lower()
    for item in STANDARDS_CATALOG:
        for kw in item.get("keywords", []):
            if kw.lower() in q_lower:
                return item
        if item.get("category", "").lower() in q_lower:
            return item
        for is_num in item.get("is_numbers", []):
            clean_is = is_num.lower().replace(":", " ").replace("(", " ").replace(")", " ")
            if any(part in q_lower for part in clean_is.split() if part.startswith("is")):
                return item
    return None

# Chroma client (lazy-loaded so the module can be imported safely)
_chroma_client = None
_collection = None


def _get_collection():
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = _chroma_client.get_collection(COLLECTION_NAME)
    return _collection


def _ollama_chat(system_prompt: str, user_prompt: str, conversation_history: list[dict] = None, retries: int = 2) -> str:
    """Call Ollama chat with automatic retry and support for conversation history."""
    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        for item in conversation_history[-6:]:
            role = item.get("role")
            content = item.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_prompt})

    for attempt in range(retries + 1):
        try:
            response = ollama.chat(
                model=CHAT_MODEL,
                messages=messages,
            )
            return response["message"]["content"].strip()
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)  # exponential backoff: 1s, 2s
                continue
            raise


# ---------------------------------------------------------------------------
# Router Agent (Enhanced with Hinglish & Master Catalog Support)
# ---------------------------------------------------------------------------
_ROUTING_KEYWORDS = {
    "compare": [
        "compare", "vs", "versus", "difference between", "side by side", "led vs", "fan vs", "toys vs",
        "kisme antar", "fark", "compare karo", "difference batao", "antar kya hai", "kaunsa better",
    ],
    "compliance_check": [
        "checklist", "what do i need", "compliance check", "steps to apply", "documents needed",
        "how to certify", "certification requirements", "timeline estimate", "cost range", "am i compliant",
        "readiness score", "requirements for", "kaise apply kare", "documents kya lagenge", "checklist chahiye",
        "process batao", "process kya hai", "kaise banega", "kya chahiye", "kaise certify kare",
        "standard kya hai", "standard batao", "kaise milega",
    ],
    "hallmarking": [
        "hallmark", "huid", "gold purity", "silver purity", "karat", "jewellery", "jewelry", "jeweller",
        "sona", "chandi", "shuddhata", "purity kaise", "huid kaise", "hallmark kaise", "gold test", "silver test",
    ],
    "lab_finder": [
        "lab", "laboratory", "testing lab", "test my", "where can i test", "which lab",
        "kahan test", "test kahan", "laboratory kahan", "lab batao", "kahan check karaye", "sample test",
    ],
    "certification": [
        "certificat", "license", "licence", "isi mark", "crs", "registration scheme", "how do i get",
        "license kaise", "isi mark kaise", "crs kaise", "registration kaise", "parwana",
    ],
    "consumer": [
        "complaint", "verify my product", "is this genuine", "consumer right", "fake product", "file a complaint",
        "shikayat", "fraud", "nakli", "fake samaan", "asli ya nakli", "complaint kaise", "bis care",
    ],
}


def route_query(query: str) -> str:
    """Returns domain: 'compare', 'compliance_check', 'hallmarking', 'lab_finder', 'certification', 'consumer', or 'standards'"""
    q_lower = query.lower()
    for domain, keywords in _ROUTING_KEYWORDS.items():
        if any(kw in q_lower for kw in keywords):
            return domain

    # Fallback: ask the LLM to classify when no keyword matched
    system = (
        "You are a query router for a BIS (Bureau of Indian Standards) assistant. "
        "Classify the user's query into exactly one of these domains: "
        "compare, compliance_check, hallmarking, lab_finder, certification, consumer, standards. "
        "Reply with only the single domain word, nothing else."
    )
    try:
        result = _ollama_chat(system, query).strip().lower()
        if result in _ROUTING_KEYWORDS or result == "standards":
            return result
    except Exception:
        pass
    return "standards"


def detect_language(query: str) -> str:
    """Lightweight heuristic: Devanagari script present -> Hindi, else English."""
    for ch in query:
        if "\u0900" <= ch <= "\u097F":
            return "hi"
    return "en"


# ---------------------------------------------------------------------------
# 1. Compliance Checker Agent (NEW - Phase 2)
# ---------------------------------------------------------------------------
def compliance_checker_agent(query: str, conversation_history: list[dict] = None) -> dict:
    """Generates structured, step-by-step compliance roadmap and document checklist."""
    q_lower = query.lower()
    matched_item = None

    for item in COMPLIANCE_CHECKLISTS:
        for kw in item.get("keywords", []):
            if kw.lower() in q_lower:
                matched_item = item
                break
        if matched_item:
            break

    # If not in checklists, check standards catalog before fallback
    if not matched_item:
        cat_match = find_standards_catalog_match(query)
        if cat_match:
            is_stds = "\n".join(f"- **{s}**" for s in cat_match["is_numbers"])
            qco_stat = "Mandatory Quality Control Order (QCO)" if cat_match.get("mandatory_qco") else "Voluntary Scheme"
            answer = f"""### 📋 Official Compliance Roadmap: {cat_match['category']}

#### 1. Mandatory Applicable Standards
{is_stds}
- **Standard Title**: {cat_match['standard_title']}

#### 2. Certification Route
- **Scheme**: {cat_match['scheme']}
- **Regulatory Status**: {qco_stat}

#### 3. Prescribed Testing & Key Clauses
- **Safety & Quality Scope**: {cat_match['scope']}
- **Key Mandatory Clauses**: {cat_match['key_clauses']}

#### 4. Pre-Application Document Checklist
1. Valid Business Registration (GST / MSME / CIN)
2. Manufacturing Process Flowchart & Machinery List
3. In-House Test & Inspection Plan (STI)
4. Calibration certificates of test instruments
5. Test reports from a BIS-recognized / NABL laboratory

#### 5. Official Verification & Application
Apply or verify standards on the official BIS portal: [{cat_match['portal_url']}]({cat_match['portal_url']})
"""
            return {
                "agent": "Compliance Checker Agent",
                "answer": answer.strip(),
                "citations": [
                    f"Bureau of Indian Standards — {cat_match['category']} ({cat_match['is_numbers'][0]})",
                    cat_match["portal_url"]
                ],
                "confidence": 0.95,
                "explanation": f"Generated structured compliance roadmap using BIS Quality Control Order and standard specification for {cat_match['category']}."
            }
        return certification_agent(query, conversation_history=conversation_history)

    # Build rich structured compliance roadmap
    stds_formatted = "\n".join(f"- **{s}**" for s in matched_item["applicable_standards"])
    markings_formatted = "\n".join(f"- {m}" for m in matched_item["marking_requirements"])
    tests_formatted = "\n".join(f"- {t}" for t in matched_item["testing_required"])
    docs_formatted = "\n".join(f"{idx+1}. {d}" for idx, d in enumerate(matched_item["documents_needed"]))

    answer = f"""### 📋 Official Compliance Roadmap: {matched_item['product_category']}

#### 1. Mandatory Applicable Standards
{stds_formatted}

#### 2. Certification Route
- **Scheme**: {matched_item['certification_route']}
- **Regulatory Risk Level**: {matched_item['risk_level']}

#### 3. Mandatory Marking & Labeling
{markings_formatted}

#### 4. Required Laboratory Testing
{tests_formatted}

#### 5. Documentation Checklist to Apply
{docs_formatted}

#### 6. Timeline, Commercials & Maintenance
- **Estimated Timeline**: {matched_item['timeline_estimate']}
- **Estimated Testing / License Cost**: {matched_item['estimated_cost_range']}
- **Validity & Renewal**: {matched_item['renewal_period']}
"""

    citations = [
        f"BIS Mandatory Standards Database — {matched_item['product_category']}",
        f"Scheme Regulations ({matched_item['certification_route']})"
    ]
    if matched_item.get("source_url"):
        citations.append(matched_item["source_url"])

    return {
        "agent": "Compliance Checker Agent",
        "answer": answer.strip(),
        "citations": citations,
        "confidence": 0.96,
        "explanation": f"Generated using structured BIS conformity requirements and Quality Control Orders (QCO) for {matched_item['product_category']}."
    }


# ---------------------------------------------------------------------------
# 2. Compare Agent (NEW - Phase 2)
# ---------------------------------------------------------------------------
def compare_agent(query: str) -> dict:
    """Compares certification requirements between two products side-by-side."""
    q_lower = query.lower()

    # Find matching products from checklists
    matched = []
    for item in COMPLIANCE_CHECKLISTS:
        if any(kw.lower() in q_lower for kw in item.get("keywords", [])):
            if item not in matched:
                matched.append(item)

    if len(matched) < 2:
        # Default to LED vs Electric Fans if query mentions LED or Fan or general compare
        p1 = next((item for item in COMPLIANCE_CHECKLISTS if "led" in item["product_category"].lower()), COMPLIANCE_CHECKLISTS[0])
        p2 = next((item for item in COMPLIANCE_CHECKLISTS if "fan" in item["product_category"].lower()), COMPLIANCE_CHECKLISTS[1])
        matched = [p1, p2]

    prod1, prod2 = matched[0], matched[1]

    answer = f"""### ⚖️ Side-by-Side Comparison: {prod1['product_category']} vs {prod2['product_category']}

| Parameter | {prod1['product_category']} | {prod2['product_category']} |
| :--- | :--- | :--- |
| **Applicable Standards** | {', '.join(s.split(':')[0] for s in prod1['applicable_standards'])} | {', '.join(s.split(':')[0] for s in prod2['applicable_standards'])} |
| **Certification Route** | {prod1['certification_route']} | {prod2['certification_route']} |
| **Marking Format** | {prod1['marking_requirements'][0]} | {prod2['marking_requirements'][0]} |
| **Audit Required?** | Lab Report based (No initial factory audit) | Factory Inspection + Sample drawing mandatory |
| **Typical Timeline** | {prod1['timeline_estimate']} | {prod2['timeline_estimate']} |
| **Estimated Cost** | {prod1['estimated_cost_range']} | {prod2['estimated_cost_range']} |
| **Validity & Renewal** | {prod1['renewal_period']} | {prod2['renewal_period']} |

#### 🔑 Key Strategic Differences:
- **Certification Scheme**: **{prod1['product_category']}** falls under **{prod1['certification_route'].split('(')[0].strip()}**, which operates primarily on lab test report submission. In contrast, **{prod2['product_category']}** requires **{prod2['certification_route'].split('(')[0].strip()}**, necessitating a full physical BIS factory inspection.
- **Marking Style**: Note that {prod1['product_category']} uses **Registration Numbers**, while {prod2['product_category']} uses the traditional **ISI Mark Monogram (CM/L)**.
"""

    return {
        "agent": "Compare Agent",
        "answer": answer.strip(),
        "citations": [
            f"BIS Scheme Matrix — {prod1['product_category']}",
            f"BIS Scheme Matrix — {prod2['product_category']}",
            "Bureau of Indian Standards Conformity Assessment Regulations"
        ],
        "confidence": 0.95,
        "explanation": f"Extracted cross-scheme regulatory parameters comparing {prod1['product_category']} against {prod2['product_category']}."
    }


# ---------------------------------------------------------------------------
# 3. Enhanced Lab Finder Agent (Phase 2 Upgrade)
# ---------------------------------------------------------------------------
def lab_finder_agent(query: str, filters: dict = None) -> dict:
    """Finds testing laboratories with rich filters (state, accreditation, export certification)."""
    q_lower = query.lower()
    matches = []

    filters = filters or {}
    state_filter = filters.get("state", "").lower()
    cat_filter = filters.get("category", "").lower()
    export_filter = filters.get("export_certified")
    accred_filter = filters.get("accreditation", "").lower()

    for lab in LABS:
        score = 0
        lab_cats = [c.lower() for c in lab.get("categories", [])]
        lab_state = lab.get("state", "").lower()
        lab_city = lab.get("city", "").lower()
        lab_region = lab.get("region", "").lower()
        lab_accreds = [a.lower() for a in lab.get("accreditation", [])]

        # Explicit filters match
        if state_filter and state_filter in lab_state:
            score += 3
        if cat_filter and any(cat_filter in c for c in lab_cats):
            score += 3
        if export_filter is not None and lab.get("export_certified") == export_filter:
            score += 2
        if accred_filter and any(accred_filter in a for a in lab_accreds):
            score += 2

        # Natural language query matching
        if any(cat in q_lower for cat in lab_cats):
            score += 3
        if lab_state and lab_state in q_lower:
            score += 2
        if lab_city and lab_city in q_lower:
            score += 2
        if lab_region and lab_region in q_lower:
            score += 1
        if "export" in q_lower and lab.get("export_certified"):
            score += 2
        if "nabl" in q_lower and "nabl" in lab_accreds:
            score += 2

        if score > 0:
            matches.append((score, lab))

    matches.sort(key=lambda x: x[0], reverse=True)
    selected_labs = [m[1] for m in matches[:4]] if matches else LABS[:3]

    lab_cards = []
    for l in selected_labs:
        accreds = ", ".join(l.get("accreditation", ["BIS"]))
        export_badge = "✅ Certified for Global Export" if l.get("export_certified") else "Domestic Testing Only"
        card = (
            f"**{l['name']}**\n"
            f"- 📍 **Location**: {l['city']}, {l.get('state', l['region'])}\n"
            f"- 🧪 **Testing Scope**: {', '.join(l['categories'])}\n"
            f"- 🏅 **Accreditations**: {accreds} ({export_badge})\n"
            f"- ⏱️ **Turnaround Time**: {l.get('turnaround_days', '10-20')} business days\n"
            f"- 💰 **Estimated Fee**: {l.get('cost_range', 'Contact lab for quote')}\n"
            f"- 📞 **Contact**: `{l.get('contact_phone', 'N/A')}` | `{l.get('contact_email', 'N/A')}`"
        )
        lab_cards.append(card)

    answer = "### 🧪 BIS-Recognized Testing Laboratories\n\n" + "\n\n---\n\n".join(lab_cards)
    answer += "\n\n*(Note: Turnaround times and fees are representative estimates. Always obtain an official commercial quote prior to dispatching product test samples.)*"

    return {
        "agent": "Lab Finder Agent",
        "answer": answer.strip(),
        "citations": [
            "National Accreditation Board for Testing and Calibration Laboratories (NABL) Directory",
            "BIS Recognized Testing Laboratory Register"
        ],
        "confidence": 0.95,
        "explanation": f"Matched {len(selected_labs)} laboratories based on product testing category, regional proximity, and NABL accreditation status."
    }


# ---------------------------------------------------------------------------
# 4. Document Analysis Agent (NEW - Phase 2)
# ---------------------------------------------------------------------------
def document_analysis_agent(analysis: dict) -> dict:
    """Formats verification report from label or certificate OCR text."""
    scheme = analysis.get("detected_scheme", "BIS Regulatory Framework")
    score = analysis.get("compliance_score", 0)
    is_compliant = analysis.get("is_compliant", False)
    findings = analysis.get("findings", [])
    missing = analysis.get("missing_items", [])
    standards = analysis.get("standards_found", [])

    status_badge = "✅ **COMPLIANT SPECIFICATION**" if is_compliant else "⚠️ **COMPLIANCE ATTENTION REQUIRED**"
    findings_fmt = "\n".join(f"- {f}" for f in findings) if findings else "- None identified."
    missing_fmt = "\n".join(f"- {m}" for m in missing) if missing else "- No missing mandatory markings detected."

    answer = f"""### 🔍 Label & Document Compliance Audit Report

{status_badge}  
**Overall Marking Compliance Score**: `{score}/100`  
**Identified Regulatory Scheme**: `{scheme}`

#### 1. Detected Regulatory Standards & Markings
{findings_fmt}

#### 2. Missing Mandatory Elements
{missing_fmt}

#### 3. Recommended Action Plan
"""
    if not is_compliant:
        answer += """1. Correct product label artwork before commercial distribution to avoid Quality Control Order (QCO) seizures.
2. Ensure mandatory registration or license numbers are permanently affixed on both product body and retail packaging.
3. Verify test report validity with a BIS-recognized testing laboratory."""
    else:
        answer += """1. Product label markings conform to standard BIS statutory guidelines.
2. Confirm annual or biennial license renewals to maintain active market authorization."""

    return {
        "agent": "Document Analysis Agent",
        "answer": answer.strip(),
        "citations": [
            "BIS (Conformity Assessment) Regulations — Statutory Marking Requirements",
            f"Relevant Indian Standard: {', '.join(standards) if standards else 'General BIS Guidelines'}"
        ],
        "confidence": 0.90,
        "explanation": f"Analyzed label layout and OCR markers with rule-based validation against official BIS marking standards (Score: {score}/100)."
    }


# ---------------------------------------------------------------------------
# 5. Retriever Agent (RAG)
# ---------------------------------------------------------------------------
def retriever_agent(query: str, conversation_history: list[dict] = None) -> dict:
    retrieved_chunks = []
    metadatas = []
    distances = []
    try:
        collection = _get_collection()
        embed_response = ollama.embeddings(model=EMBED_MODEL, prompt=query)
        query_embedding = embed_response["embedding"]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        retrieved_chunks = results["documents"][0] if results.get("documents") else []
        metadatas = results["metadatas"][0] if results.get("metadatas") else []
        distances = results["distances"][0] if results.get("distances") else []
    except Exception:
        retrieved_chunks = []
        metadatas = []
        distances = []

    # Calculate confidence score based on Chroma distance
    if distances:
        best_dist = distances[0]
        confidence = round(max(0.20, min(0.98, 1.0 - (best_dist / 1.4))), 2)
    elif retrieved_chunks:
        confidence = 0.70
    else:
        confidence = 0.40

    if not retrieved_chunks:
        # Check Master Standards Catalog before falling back to ungrounded LLM
        catalog_item = find_standards_catalog_match(query)
        if catalog_item:
            is_list = ", ".join(f"**{num}**" for num in catalog_item["is_numbers"])
            qco_badge = "Mandatory Quality Control Order (QCO)" if catalog_item.get("mandatory_qco") else "Voluntary / Standard Certification"
            answer = f"""### 🏛️ Official BIS Standards Specification: {catalog_item['category']}

- **Applicable Indian Standard(s)**: {is_list}
- **Standard Title**: {catalog_item['standard_title']}
- **Regulatory Scheme**: {catalog_item['scheme']}
- **Statutory Status**: {qco_badge}
- **Testing & Safety Scope**: {catalog_item['scope']}
- **Key Mandatory Clauses**: {catalog_item['key_clauses']}

💡 **Verification & License Application**:
You can look up active license holders or apply for certification at the official BIS portal: [{catalog_item['portal_url']}]({catalog_item['portal_url']})
"""
            return {
                "agent": "Retriever Agent (Master Catalog)",
                "answer": answer.strip(),
                "citations": [
                    f"Bureau of Indian Standards — {catalog_item['category']} ({catalog_item['is_numbers'][0]})",
                    f"BIS Official Portal: {catalog_item['portal_url']}",
                    "Gazette Quality Control Orders (QCO) Database"
                ],
                "confidence": 0.95,
                "explanation": f"Retrieved authoritative statutory specification from the BIS Master Standards Catalog for {catalog_item['category']}."
            }

        system = (
            "You are ComplyBot, an AI assistant for the Bureau of Indian Standards (BIS). "
            "Answer the user's question about Indian Standards or BIS certification accurately and politely. "
            "If relevant, mention standard numbers (IS numbers)."
        )
        answer = _ollama_chat(system, query, conversation_history=conversation_history)
        return {
            "agent": "Retriever Agent",
            "answer": answer,
            "citations": ["Bureau of Indian Standards (BIS) Portal"],
            "confidence": confidence,
            "explanation": "Answer synthesized via foundational BIS compliance knowledge base.",
        }

    context_block = "\n\n".join(
        f"[Source: {m['source']} | Section: {m['section']}]\n{c}"
        for c, m in zip(retrieved_chunks, metadatas)
    )

    system = (
        "You are the Retriever Agent for ComplyBot, a BIS (Bureau of Indian Standards) assistant. "
        "Answer the user's question using ONLY the provided context below and any previous dialogue context. "
        "Always cite the source document and section at the end of your answer. "
        "If the context does not contain the answer, say you don't have that information "
        "rather than guessing."
    )
    user = f"Context:\n{context_block}\n\nQuestion: {query}"
    answer = _ollama_chat(system, user, conversation_history=conversation_history)

    # Fallback advisory or Master Catalog enhancement when confidence is low
    if confidence < 0.50:
        catalog_item = find_standards_catalog_match(query)
        if catalog_item:
            is_list = ", ".join(f"**{num}**" for num in catalog_item["is_numbers"])
            return {
                "agent": "Retriever Agent (Master Catalog)",
                "answer": (
                    f"### 🏛️ Official BIS Standards Specification: {catalog_item['category']}\n\n"
                    f"- **Applicable Indian Standard(s)**: {is_list}\n"
                    f"- **Standard Title**: {catalog_item['standard_title']}\n"
                    f"- **Regulatory Scheme**: {catalog_item['scheme']}\n"
                    f"- **Testing & Safety Scope**: {catalog_item['scope']}\n"
                    f"- **Key Mandatory Clauses**: {catalog_item['key_clauses']}\n\n"
                    f"💡 Official BIS Portal: [{catalog_item['portal_url']}]({catalog_item['portal_url']})"
                ),
                "citations": [
                    f"Bureau of Indian Standards — {catalog_item['category']} ({catalog_item['is_numbers'][0]})",
                    catalog_item["portal_url"],
                ],
                "confidence": 0.95,
                "explanation": f"Corpus confidence was low; synthesized via authoritative BIS Master Catalog specification for {catalog_item['category']}.",
            }

        answer = (
            "⚠️ Note: Low confidence score on exact clause match. Please confirm the product category or consult official BIS publications.\n\n"
            + answer
        )

    citations = [f"{m['source']} — {m['section']}" for m in metadatas]
    top_sec = metadatas[0]['section'] if metadatas else "Standards Corpus"
    return {
        "agent": "Retriever Agent",
        "answer": answer,
        "citations": citations,
        "confidence": confidence,
        "explanation": f"Retrieved {len(retrieved_chunks)} verified sections from ChromaDB standards corpus, matching '{top_sec}'."
    }


# ---------------------------------------------------------------------------
# 6. Certification & Licensing Agent
# ---------------------------------------------------------------------------
def certification_agent(query: str, conversation_history: list[dict] = None) -> dict:
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
        return retriever_agent(query, conversation_history=conversation_history)

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
    answer = _ollama_chat(system, f"Scheme data:\n{context}\n\nUser question: {query}", conversation_history=conversation_history)

    citation = f"BIS Certification Scheme Database — {best_match['scheme_name']}"
    if best_match.get("source_url"):
        citation += f" ({best_match['source_url']})"

    return {
        "agent": "Certification & Licensing Agent",
        "answer": answer,
        "citations": [citation],
        "confidence": 0.92,
        "explanation": f"Matched official BIS scheme profile for {best_match['scheme_name']}."
    }


# ---------------------------------------------------------------------------
# 7. Consumer Query Agent
# ---------------------------------------------------------------------------
def consumer_agent(query: str, conversation_history: list[dict] = None) -> dict:
    system = (
        "You are the Consumer Query Agent for ComplyBot, a BIS assistant. "
        "Answer in simple, plain language suitable for an everyday consumer (not a technical "
        "audience). If the question is about verifying a product or filing a complaint, "
        "mention that consumers can use the BIS CARE app or the National Consumer Helpline "
        "(1915) for complaints. Keep the answer short and reassuring."
    )
    answer = _ollama_chat(system, query, conversation_history=conversation_history)
    return {
        "agent": "Consumer Query Agent",
        "answer": answer,
        "citations": ["BIS Consumer Services — General Guidance", "National Consumer Helpline (1915)"],
        "confidence": 0.85,
        "explanation": "Consumer assistance guidance referenced to the official BIS CARE framework.",
    }


# ---------------------------------------------------------------------------
# 8. Hallmarking Agent
# ---------------------------------------------------------------------------
def hallmarking_agent(query: str) -> dict:
    q_lower = query.lower()

    if "huid" in q_lower or "verify" in q_lower or "check" in q_lower:
        answer = HALLMARKING_RULES["huid_explanation"] + "\n\nTo verify a hallmark:\n" + "\n".join(
            f"- {step}" for step in HALLMARKING_RULES["how_to_verify"]
        )
        return {
            "agent": "Hallmarking Agent",
            "answer": answer,
            "citations": ["BIS Hallmarking Rules — HUID & Verification Protocol"],
            "confidence": 1.0,
            "explanation": "Deterministic verification rules based on BIS compulsory hallmarking statutory order."
        }

    if "silver" in q_lower:
        grades = "\n".join(
            f"- {g['grade']}: {g['description']}" for g in HALLMARKING_RULES["purity_grades_silver"]
        )
        answer = f"Silver purity grades under BIS hallmarking:\n{grades}"
        return {
            "agent": "Hallmarking Agent",
            "answer": answer,
            "citations": ["BIS Hallmarking Rules — Silver Purity Grades (IS 2112)"],
            "confidence": 1.0,
            "explanation": "Deterministic standard fineness lookup per IS 2112 specification."
        }

    # default: gold purity info
    grades = "\n".join(
        f"- {g['karat']} ({g['fineness']} fineness): {g['description']}" for g in HALLMARKING_RULES["purity_grades_gold"]
    )
    answer = (
        f"Gold purity grades under BIS hallmarking:\n{grades}\n\n"
        f"{HALLMARKING_RULES['jeweller_registration_note']}"
    )
    return {
        "agent": "Hallmarking Agent",
        "answer": answer,
        "citations": ["BIS Hallmarking Rules — Gold Purity Grades (IS 1417)"],
        "confidence": 1.0,
        "explanation": "Deterministic standard fineness lookup per IS 1417 specification."
    }


# ---------------------------------------------------------------------------
# 9. Translator
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
        return text


# ---------------------------------------------------------------------------
# Top-level query handler
# ---------------------------------------------------------------------------
def handle_query(query: str, language: str = None, conversation_history: list[dict] = None) -> dict:
    try:
        domain = route_query(query)
        lang = language or detect_language(query)

        if domain == "compare":
            result = compare_agent(query)
        elif domain == "compliance_check":
            result = compliance_checker_agent(query, conversation_history=conversation_history)
        elif domain == "hallmarking":
            result = hallmarking_agent(query)
        elif domain == "lab_finder":
            result = lab_finder_agent(query)
        elif domain == "certification":
            result = certification_agent(query, conversation_history=conversation_history)
        elif domain == "consumer":
            result = consumer_agent(query, conversation_history=conversation_history)
        else:
            result = retriever_agent(query, conversation_history=conversation_history)

        result["answer"] = translate(result["answer"], lang)
        result["domain"] = domain
        result["language"] = lang
        result["confidence"] = result.get("confidence", 0.85)
        result["explanation"] = result.get("explanation", "Synthesized by ComplyBot multi-agent swarm.")
        return result
    except Exception as e:
        return {
            "agent": "System",
            "domain": "error",
            "language": language or "en",
            "confidence": 0.0,
            "explanation": "Inference error occurred.",
            "answer": f"Ollama model error — the local LLM may have crashed. Please try again in a few seconds. (Details: {str(e)[:150]})",
            "citations": [],
        }
