"""
ingest.py
Reads markdown documents from ../data/standards/, chunks them by section,
embeds each chunk using a local Ollama embedding model, and stores them
in a persistent ChromaDB collection for retrieval by the Retriever Agent.

Run this once after setup, and again any time you add/change documents in
data/standards/.

Usage:
    python ingest.py
"""

import os
import glob
import chromadb
import ollama

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "standards")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "bis_standards"


def chunk_markdown(text: str, source: str):
    """
    Splits a markdown document into chunks by '##' section headers.
    Each chunk keeps its section title for better citations.
    Returns a list of dicts: {text, section, source}
    """
    chunks = []
    sections = text.split("\n## ")
    # First section may contain the title (starts with '# ')
    for i, section in enumerate(sections):
        if i == 0:
            # top-level title + intro
            lines = section.strip().split("\n")
            title = lines[0].lstrip("# ").strip()
            body = "\n".join(lines[1:]).strip()
            if body:
                chunks.append({"text": body, "section": title, "source": source})
        else:
            lines = section.strip().split("\n")
            section_title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
            if body:
                chunks.append({"text": body, "section": section_title, "source": source})
    return chunks


def main():
    print(f"Reading documents from: {DATA_DIR}")
    md_files = glob.glob(os.path.join(DATA_DIR, "*.md"))
    if not md_files:
        print("No markdown files found. Add .md files to data/standards/ first.")
        return

    all_chunks = []
    for path in md_files:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        source_name = os.path.basename(path)
        file_chunks = chunk_markdown(text, source_name)
        all_chunks.extend(file_chunks)
        print(f"  {source_name}: {len(file_chunks)} chunks")

    print(f"\nTotal chunks to embed: {len(all_chunks)}")

    # Set up Chroma persistent client
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    # Fresh collection each time ingest runs (simple approach for hackathon scope)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    print(f"\nEmbedding chunks using Ollama model '{EMBED_MODEL}'...")
    print("(Make sure you've run: ollama pull nomic-embed-text)\n")

    ids, documents, embeddings, metadatas = [], [], [], []
    for idx, chunk in enumerate(all_chunks):
        response = ollama.embeddings(model=EMBED_MODEL, prompt=chunk["text"])
        embedding = response["embedding"]

        ids.append(f"chunk_{idx}")
        documents.append(chunk["text"])
        embeddings.append(embedding)
        metadatas.append({"source": chunk["source"], "section": chunk["section"]})
        print(f"  Embedded chunk {idx + 1}/{len(all_chunks)}: [{chunk['source']}] {chunk['section'][:50]}")

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"\nDone. {len(all_chunks)} chunks stored in ChromaDB at: {CHROMA_DIR}")
    print("You can now start the backend with: uvicorn main:app --reload")


if __name__ == "__main__":
    main()
