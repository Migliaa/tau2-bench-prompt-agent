"""
Estrae da `tau2-bench/data/simulations/` un file compatto con il reward di ogni task in ogni
esecuzione (`results/esiti-per-task.json`). Serve a chi clona il repository: i `results.json`
originali pesano ~95 MB e non stanno in git, questo file sì.

Uso, dalla radice del repo (richiede le simulazioni locali):
    python scripts/estrai_esiti.py
"""

import glob
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
SIM = ROOT / "tau2-bench" / "data" / "simulations"

# nome nel file -> (prefisso cartella, agente, descrizione)
RUN = {
    "baseline_1": ("s6", "llm_agent", "agente di default del benchmark, esecuzione 1"),
    "baseline_2": ("s9", "llm_agent", "agente di default, esecuzione 2"),
    "v1_1": ("s6", "custom_agent", "nostra v1, esecuzione 1"),
    "v1_2": ("s9", "custom_agent", "nostra v1, esecuzione 2"),
    "v2": ("s7", "custom_agent", "v2, una esecuzione"),
    "v3": ("s8", "custom_agent", "v3, una esecuzione"),
    "v4": ("s10", "custom_agent", "v4, una esecuzione"),
    "v5": ("s13", "custom_agent", "v5, una esecuzione"),
    "v6_trial1": ("s15", "custom_agent", "v6, trial 1"),
    "v6_trial2": ("s16", "custom_agent", "v6, trial 2"),
    "v6_trial3": ("s17", "custom_agent", "v6, trial 3"),
    "v6_trial4": ("s18", "custom_agent", "v6, trial 4"),
}


def main() -> None:
    out = {"_modello": "gemini-3.5-flash-lite (agente e utente simulato), temperature 0, dominio airline, 50 task", "run": {}}
    for nome, (pref, agente, desc) in RUN.items():
        esiti = {}
        for d in glob.glob(str(SIM / f"{pref}_{agente}_t*")):
            fp = os.path.join(d, "results.json")
            if not os.path.exists(fp):
                continue
            s = (json.load(open(fp, encoding="utf-8")).get("simulations") or [{}])[0]
            r = (s.get("reward_info") or {}).get("reward")
            if r is not None:
                esiti[str(s["task_id"])] = r
        out["run"][nome] = {"descrizione": desc, "cartelle": f"{pref}_{agente}_t*", "reward": dict(sorted(esiti.items(), key=lambda kv: int(kv[0])))}
        print(f"{nome:<12} {len(esiti)} task, superati {sum(1 for v in esiti.values() if v == 1.0)}")
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "esiti-per-task.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
