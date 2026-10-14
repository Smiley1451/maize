from __future__ import annotations
import json, re
from dataclasses import dataclass
from typing import Any
from .retrieval import Retriever
from .data_tools import search_records, genotype_profile, experiment_search, domain_summary, project_file_search
from .model_tools import available_models, phase19_health, get_model_metrics, get_explainability
from .indexer import ProjectIndexer
from .llm.provider import ProviderFactory
from .llm.prompts import build_prompt

TOOLS=[
    "semantic_search","search_project_records","genotype_profile","experiment_search","dataset_summary",
    "list_models","model_metrics","model_explainability","phase19_health","predict","project_file_search"
]

@dataclass
class ToolResult:
    tool:str
    result:Any

class ResearchAssistant:
    def __init__(self):
        self.retriever=Retriever()
        self.provider=ProviderFactory.get()

    def refresh(self):
        self.retriever.refresh()
        return {"status":"ok","chunks":len(self.retriever.chunks)}

    def route(self, q:str)->list[str]:
        s=q.casefold(); tools=["semantic_search"]
        if any(x in s for x in ["genotype","line","inbred","hybrid","ma h-","mah-","bs "]): tools += ["genotype_profile"]
        if "experiment" in s or "trial" in s: tools += ["experiment_search"]
        if any(x in s for x in ["yield","grain","kg/ha","t/ha","shelling"]): tools += ["search_project_records","dataset_summary"]
        if any(x in s for x in ["tlb","turcicum","leaf blight"]): tools += ["search_project_records","model_metrics","model_explainability"]
        if any(x in s for x in ["sdm","downy mildew","pdi"]): tools += ["search_project_records","model_metrics","model_explainability"]
        if any(x in s for x in ["model","rmse","mae","r2","r²","accuracy","f1","prediction","predict"]): tools += ["list_models","model_metrics"]
        if any(x in s for x in ["cluster","pca","k-means","kmeans"]): tools += ["search_project_records"]
        if any(x in s for x in ["weather","rainfall","humidity","temperature"]): tools += ["search_project_records"]
        if any(x in s for x in ["phase","script","log","failed","failure","error","powershell","pipeline"]): tools += ["project_file_search"]
        out=[]
        for x in tools:
            if x not in out: out.append(x)
        return out

    def execute_tools(self, q:str, names:list[str])->list[ToolResult]:
        out=[]
        for name in names:
            try:
                if name=="semantic_search":
                    out.append(ToolResult(name,self.retriever.search(q)))
                elif name=="search_project_records":
                    out.append(ToolResult(name,search_records(q)))
                elif name=="genotype_profile":
                    m=re.search(r"\b[A-Za-z]{2,5}[ -]?\d{1,4}(?:[- ][A-Za-z0-9]+)*\b", q)
                    token=m.group(0) if m else q
                    candidates=re.findall(r"[A-Za-z]{2,6}[ -]?\d{1,4}(?:[- ][A-Za-z0-9]+)*", q)
                    if candidates: token=candidates[-1]
                    out.append(ToolResult(name,genotype_profile(token)))
                elif name=="experiment_search":
                    out.append(ToolResult(name,experiment_search(q)))
                elif name=="dataset_summary":
                    dom=None
                    for d in ["yield","tlb","sdm","multi_trait"]:
                        if d in q.casefold(): dom=d; break
                    out.append(ToolResult(name,domain_summary(dom)))
                elif name=="list_models": out.append(ToolResult(name,available_models(include_metadata=False)))
                elif name=="model_metrics":
                    results={}
                    for d in ["yield","tlb","sdm"]:
                        for k in ["regression","classification"]:
                            if d=="yield" and k=="classification": continue
                            results[f"{d}-{k}"]=get_model_metrics(d,k)
                    out.append(ToolResult(name,results))
                elif name=="model_explainability":
                    keys=[]; s=q.casefold()
                    if "tlb" in s: keys += ["tlb_regression","tlb_classifier"]
                    if "sdm" in s: keys += ["sdm_regression","sdm_classifier"]
                    if "yield" in s or not keys: keys += ["yield"]
                    out.append(ToolResult(name,{k:get_explainability(k) for k in keys}))
                elif name=="phase19_health": out.append(ToolResult(name,phase19_health()))
                elif name=="predict":
                    out.append(ToolResult(name,{"note":"Prediction is available through the Phase 19 API. The assistant will not invent inputs or predictions; provide a complete feature record when asking for a new prediction.","required_features":["days_to_50_percent_pollen_shedding","days_to_50_percent_silking","days_to_75_percent_dry_husk","plant_height","ear_height","plant_stand","shelling_percentage"]}))
                elif name=="project_file_search": out.append(ToolResult(name,project_file_search(q)))
            except Exception as exc:
                out.append(ToolResult(name,{"error":str(exc)}))
        return out

    def answer_local(self, q:str, results:list[ToolResult])->str:
        sections=[]
        for r in results:
            if r.tool=="semantic_search" and r.result:
                lines=[f"- {x['text']} [{self._cite(x)}]" for x in r.result[:5]]
                sections.append("Relevant project evidence:\n"+"\n".join(lines))
            elif r.tool=="genotype_profile":
                data=r.result; sections.append(f"Genotype query: {data.get('query')}\nMatched records: {data.get('match_count',0)}")
                for d,rows in data.get("domains",{}).items():
                    sections.append(f"{d}: {len(rows)} matching records")
                    for h in rows[:4]: sections.append(f"  - {h['record']} [{h['path']} row {h['row']}]")
            elif r.tool in {"search_project_records","experiment_search"} and r.result:
                sections.append(r.tool+":\n"+"\n".join(f"- {h['record']} [{h['path']} row {h['row']}]" for h in r.result[:8]))
            elif r.tool=="list_models":
                sections.append(f"Available model artifacts found: {len(r.result)}")
                sections.append("\n".join(f"- {x['kind']}: {x['path']}" for x in r.result[:15]))
            elif r.tool=="dataset_summary":
                sections.append("Dataset files: "+json.dumps(r.result, ensure_ascii=False)[:8000])
            elif r.tool in {"model_metrics","model_explainability","phase19_health"}:
                sections.append(r.tool+": "+json.dumps(r.result,ensure_ascii=False,default=str)[:10000])
            elif r.tool=="project_file_search" and r.result:
                sections.append("Relevant files:\n"+"\n".join(f"- {x['path']}" for x in r.result[:15]))
        if not sections:
            return "I could not find enough grounded evidence in the indexed project files to answer that question. Run the index refresh and try again."
        return "\n\n".join(sections)

    def _cite(self, x):
        s=x["path"]
        if x.get("page") is not None: s+=f" page {x['page']}"
        if x.get("row") is not None: s+=f" row {x['row']}"
        return s

    def chat(self, q:str)->dict[str,Any]:
        q=q.strip()
        if not q: return {"status":"ERROR","answer":"Question cannot be empty.","sources":[],"tools":[]}
        names=self.route(q); tool_results=self.execute_tools(q,names)
        evidence=[]
        for tr in tool_results:
            if tr.tool=="semantic_search" and isinstance(tr.result,list): evidence.extend(tr.result[:8])
        messages=build_prompt(q,evidence,[{"tool":x.tool,"result":x.result} for x in tool_results])
        provider_used="local"; answer=None
        if self.provider is not None:
            try:
                answer=self.provider.chat(messages); provider_used="llm"
            except Exception:
                provider_used="local_fallback"
        if not answer: answer=self.answer_local(q,tool_results)
        sources=[]; seen=set()
        for e in evidence:
            s=self._cite(e)
            if s not in seen: seen.add(s); sources.append(s)
        # Also expose tool-derived source paths when semantic retrieval did not surface them.
        for tr in tool_results:
            data=tr.result
            if isinstance(data,list):
                for x in data:
                    if isinstance(x,dict) and isinstance(x.get("path"),str):
                        s=x["path"] + (f" row {x['row']}" if x.get('row') is not None else "")
                        if s not in seen: seen.add(s); sources.append(s)
        return {"status":"ok","provider":provider_used,"question":q,"answer":answer,"tools_used":names,"sources":sources[:20]}
