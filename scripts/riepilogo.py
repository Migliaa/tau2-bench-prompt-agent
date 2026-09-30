"""
Ricalcola i numeri del README da `results/esiti-per-task.json`, senza chiamate a modelli.

Uso, dalla radice del repo:
    python scripts/riepilogo.py
"""

import json
import sys
from math import comb
from pathlib import Path

ESITI = json.loads((Path(__file__).parent.parent / "results" / "esiti-per-task.json").read_text(encoding="utf-8"))["run"]


def reward(run: str) -> dict:
    return {t: r for t, r in ESITI[run]["reward"].items()}


def mcnemar_esatto(a: dict, b: dict) -> tuple[int, int, float]:
    """Vinti e persi di `a` rispetto a `b` sui task comuni, e p a due code del test esatto."""
    comuni = set(a) & set(b)
    vinti = sum(1 for t in comuni if a[t] == 1.0 and b[t] != 1.0)
    persi = sum(1 for t in comuni if a[t] != 1.0 and b[t] == 1.0)
    n = vinti + persi
    if n == 0:
        return vinti, persi, 1.0
    coda = sum(comb(n, k) for k in range(0, min(vinti, persi) + 1)) / 2**n
    return vinti, persi, min(1.0, 2 * coda)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    base = reward("baseline_1")
    print("pass^1 per esecuzione (task superati / task eseguiti) e confronto con baseline_1\n")
    print(f"{'esecuzione':<12}{'superati':>10}{'pass^1':>9}{'vinti':>7}{'persi':>7}{'p (McNemar)':>13}")
    for nome, r in ESITI.items():
        rw = reward(nome)
        ok = sum(1 for v in rw.values() if v == 1.0)
        if nome in ("baseline_1", "baseline_2"):
            print(f"{nome:<12}{f'{ok}/{len(rw)}':>10}{ok / len(rw):>9.1%}")
            continue
        v, p, pv = mcnemar_esatto(rw, base)
        print(f"{nome:<12}{f'{ok}/{len(rw)}':>10}{ok / len(rw):>9.1%}{v:>7}{p:>7}{pv:>13.3f}")

    trial = [reward(f"v6_trial{i}") for i in range(1, 5)]
    media = sum(sum(1 for v in t.values() if v == 1.0) / len(t) for t in trial) / 4
    tutti = sorted(set.intersection(*[set(t) for t in trial]), key=int)
    pass4 = sum(1 for t in tutti if all(x[t] == 1.0 for x in trial)) / len(tutti)
    print(f"\nv6, quattro trial: pass^1 medio {media:.1%}, pass^4 {pass4:.1%} ({len(tutti)} task)")

    b1, b2, t1, t2 = reward("baseline_1"), reward("baseline_2"), trial[0], trial[1]
    comuni = sorted(set(b1) & set(b2) & set(t1) & set(t2), key=int)
    n = len(comuni)

    def p1(a, b):
        return sum((a[t] == 1.0) + (b[t] == 1.0) for t in comuni) / (2 * n)

    def p2(a, b):
        return sum(a[t] == 1.0 and b[t] == 1.0 for t in comuni) / n

    print(f"\naffidabilità sui {n} task con due esecuzioni sia per il baseline sia per la v6 (trial 1 e 2)")
    print(f"{'':<10}{'pass^1 (media)':>16}{'pass^2':>9}")
    print(f"{'baseline':<10}{p1(b1, b2):>16.1%}{p2(b1, b2):>9.1%}")
    print(f"{'v6':<10}{p1(t1, t2):>16.1%}{p2(t1, t2):>9.1%}")

    mai = [t for t in tutti if all(x[t] != 1.0 for x in trial)]
    print(f"\ntask mai superati nei quattro trial v6: {mai}")


if __name__ == "__main__":
    main()
