"""
Resumen del banco de prueba del enricher (spec 002, H2): por modelo, aciertos
de relevancia, falsos «no» (lo grave: el aviso no llega), falsos «sí»,
errores, tokens y coste.

    python evals/enricher/resumen.py resultados.jsonl > resumen.md
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict

# $/millón de tokens: entrada, salida, caché escrita (5 min), caché leída.
# Precios de la API de Anthropic a 16/10/2026.
PRECIOS = {
    "claude-sonnet-4-6": (3.00, 15.00, 3.75, 0.30),
    "claude-sonnet-5-5": (2.00, 10.00, 2.50, 0.20),
    "claude-haiku-5-5": (0.10, 0.50, 0.125, 0.01),
}


def coste(modelo: str, uso: dict) -> float:
    pi, po, pw, pr = PRECIOS.get(modelo, (0, 0, 0, 0))
    return (uso["entrada"] * pi + uso["salida"] * po
            + uso["cache_escrita"] * pw + uso["cache_leida"] * pr) / 1e6


def main(path: str) -> None:
    filas = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    por_modelo = defaultdict(list)
    for f in filas:
        por_modelo[f["modelo"]].append(f)

    print("## Banco de prueba del enricher\n")
    print("| Modelo | Casos | Aciertos | Falsos «no» (grave) | Falsos «sí» | Errores | Tokens entrada / salida | Coste total | Coste por caso |")
    print("|---|---|---|---|---|---|---|---|---|")
    for modelo, fs in por_modelo.items():
        ok = sum(1 for f in fs if f["error"] is None and f["prediccion"] == f["relevante"])
        fno = sum(1 for f in fs if f["relevante"] and f["prediccion"] is not True)
        fsi = sum(1 for f in fs if not f["relevante"] and f["prediccion"] is True)
        err = sum(1 for f in fs if f["error"])
        ent = sum(f["uso"]["entrada"] + f["uso"]["cache_escrita"] + f["uso"]["cache_leida"] for f in fs)
        sal = sum(f["uso"]["salida"] for f in fs)
        c = sum(coste(modelo, f["uso"]) for f in fs)
        print(f"| {modelo} | {len(fs)} | {ok} | {fno} | {fsi} | {err} | {ent:,} / {sal:,} | {c:.3f} $ | {c / max(len(fs), 1):.4f} $ |")

    print("\n## Fallos por caso\n")
    print("| Caso | Esperado | " + " | ".join(por_modelo) + " | Nota |")
    print("|---|---|" + "---|" * len(por_modelo) + "---|")
    por_caso = defaultdict(dict)
    meta = {}
    for f in filas:
        por_caso[f["id"]][f["modelo"]] = "ERROR" if f["error"] else f["prediccion"]
        meta[f["id"]] = (f["relevante"], f["nota"])
    for cid, preds in por_caso.items():
        esperado, nota = meta[cid]
        if any(p != esperado for p in preds.values()):
            celdas = " | ".join(str(preds.get(m, "")) for m in por_modelo)
            print(f"| {cid} | {esperado} | {celdas} | {nota} |")

    print("\n## Plazas y plazos (acuerdo con el modelo actual)\n")
    base = {f["id"]: f for f in por_modelo.get("claude-sonnet-4-6", [])}
    for modelo, fs in por_modelo.items():
        if modelo == "claude-sonnet-4-6" or not base:
            continue
        mismos_plazos = sum(1 for f in fs if f["id"] in base and f["plazo"] == base[f["id"]]["plazo"])
        mismas_plazas = sum(1 for f in fs if f["id"] in base and f["plazas"] == base[f["id"]]["plazas"])
        print(f"- {modelo}: plazo igual en {mismos_plazos}/{len(fs)}, plazas iguales en {mismas_plazas}/{len(fs)}")


if __name__ == "__main__":
    main(sys.argv[1])
