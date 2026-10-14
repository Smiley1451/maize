from __future__ import annotations
from .assistant import ResearchAssistant
from .indexer import ProjectIndexer

def run():
    a=ResearchAssistant()
    if not a.retriever.chunks:
        print("[INFO] Project index not found. Building it now...")
        result=ProjectIndexer().build(); print(f"[DONE] Indexed {result['chunk_count']} chunks from {result['file_count']} files")
        a.refresh()
    print("="*78); print("MAIZE AI/LLM RESEARCH ASSISTANT"); print("Type a question. Type 'exit' to quit."); print("="*78)
    while True:
        try: q=input("You: ").strip()
        except (EOFError,KeyboardInterrupt): print(); break
        if q.casefold() in {"exit","quit"}: break
        result=a.chat(q)
        print(f"Assistant ({result.get('provider','local')}):")
        print(result["answer"])
        if result.get("sources"):
            print("Sources:")
            for s in result["sources"][:10]: print(" - "+s)
        print("-"*78)

if __name__=="__main__": run()
