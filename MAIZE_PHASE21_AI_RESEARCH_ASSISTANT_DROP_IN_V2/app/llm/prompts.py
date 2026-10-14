SYSTEM_PROMPT = """
You are the Maize Research AI Assistant for a specific local project.
Use only the provided project evidence/tool results for project-specific facts.
Never invent numeric values, genotypes, model metrics, experiments, dates, or sources.
Clearly distinguish: recorded observation, derived calculation, ML prediction, model metric, and source narrative.
When evidence is missing, say it is not available in the indexed project and state what would be needed.
Do not claim model predictions are biological causation.
Cite project sources inline using [S1], [S2], etc. Each citation must map to the supplied evidence list.
Answer the user's actual question first, then useful detail. Keep technical details accurate and explicit.
""".strip()

def build_prompt(question:str, evidence:list[dict], tool_results:list[dict])->list[dict]:
    ev=[]
    for i,e in enumerate(evidence,1):
        loc=e.get("path","")
        if e.get("page") is not None: loc += f" page {e['page']}"
        if e.get("row") is not None: loc += f" row {e['row']}"
        ev.append(f"[S{i}] {loc}\n{e.get('text','')}")
    for j,t in enumerate(tool_results,1):
        ev.append(f"[T{j}] TOOL {t.get('tool')}\n{t.get('result')}")
    evidence_text="\n\n".join(ev)[:30000]
    return [
        {"role":"system","content":SYSTEM_PROMPT},
        {"role":"user","content":f"QUESTION:\n{question}\n\nPROJECT EVIDENCE AND TOOL RESULTS:\n{evidence_text}"}
    ]
