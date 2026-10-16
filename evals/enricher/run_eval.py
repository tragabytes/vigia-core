"""
Banco de prueba del enricher (spec 002, H2): pasa las convocatorias de
`casos.json` por el enricher de producción con varios modelos y apunta si
acierta la relevancia, los campos y lo que gasta.

Uso (un perfil por proceso: el enricher lee el perfil al importarse):

    python evals/enricher/run_eval.py --perfil enfermeria --salida res.jsonl
    PYTHONPATH=../vigia-docencia python evals/enricher/run_eval.py --perfil docencia --salida res.jsonl
    python evals/enricher/run_eval.py --perfil enfermeria --simular   # sin API, sin gasto

Cada modelo va como `id:esfuerzo:max_tokens` (esfuerzo `-` = no enviarlo).
El cuerpo de cada convocatoria se descarga una vez (como `enrich_pending`) y se
reutiliza para todos los modelos, para que comparen lo mismo.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path
from types import SimpleNamespace

MODELOS = "claude-sonnet-4-6:-:2048,claude-sonnet-5-5:low:8000,claude-haiku-5-5:low:8000"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perfil", choices=["enfermeria", "docencia"], required=True)
    ap.add_argument("--modelos", default=MODELOS)
    ap.add_argument("--casos", default=str(Path(__file__).with_name("casos.json")))
    ap.add_argument("--salida", default="resultados.jsonl")
    ap.add_argument("--simular", action="store_true", help="cliente falso: comprueba el montaje sin gastar")
    ap.add_argument("--precargar", type=int, default=0,
                    help="descarga la página si el texto tiene menos de N caracteres (0 = como producción)")
    args = ap.parse_args()

    if args.perfil == "docencia":
        from vigia.profile import set_active_profile
        from vigia_docencia.profile import PERFIL_DOCENCIA
        set_active_profile(PERFIL_DOCENCIA)
    from vigia import enricher  # después de fijar el perfil
    from vigia.storage import Item

    casos = [c for c in json.loads(Path(args.casos).read_text(encoding="utf-8"))
             if c["perfil"] == args.perfil]

    # Cuerpo de cada convocatoria, una vez para todos los modelos.
    for c in casos:
        if not c["raw_text"] or len(c["raw_text"]) < args.precargar:
            body = "" if args.simular else enricher._fetch_body_full(c["url"])
            if body and not body.startswith("ERROR"):
                c["raw_text"] = body
        print(f"[cuerpo] {c['id']}: {len(c['raw_text'])} caracteres", flush=True)

    base = _cliente_falso() if args.simular else _cliente_real()
    with open(args.salida, "a", encoding="utf-8") as out:
        for spec in args.modelos.split(","):
            modelo, esfuerzo, max_tokens = spec.split(":")
            enricher.MODEL = modelo
            enricher.MAX_TOKENS = int(max_tokens)
            client = _con_esfuerzo(base, None if esfuerzo == "-" else esfuerzo)
            for c in casos:
                item = Item(source=c["source"], url=c["url"], titulo=c["titulo"],
                            fecha=date.fromisoformat(c["fecha"][:10]),
                            categoria=c["categoria"] or "otro")
                item.extra = {"raw_text": c["raw_text"]}
                uso = enricher._uso_vacio()
                t0 = time.time()
                error = None
                try:
                    data = enricher._enrich_one(client, item, uso)
                    enricher._apply_enrichment(item, data)
                except Exception as exc:  # se apunta y se sigue
                    error = f"{type(exc).__name__}: {exc}"[:300]
                fila = {
                    "id": c["id"], "perfil": args.perfil, "modelo": modelo,
                    "esfuerzo": esfuerzo, "relevante": c["relevante"],
                    "prediccion": item.is_relevant, "plazas": item.plazas,
                    "plazo": item.deadline_inscripcion, "motivo": item.relevance_reason,
                    "error": error, "uso": uso, "segundos": round(time.time() - t0, 1),
                    "titulo": c["titulo"][:120], "nota": c["nota"],
                }
                out.write(json.dumps(fila, ensure_ascii=False, default=str) + "\n")
                out.flush()
                print(f"[{modelo}] {c['id']}: esperado {c['relevante']} -> {item.is_relevant}"
                      f"{' ERROR ' + error if error else ''}", flush=True)


def _cliente_real():
    import anthropic
    return anthropic.Anthropic()


def _con_esfuerzo(base, esfuerzo):
    """Envuelve el cliente para añadir `output_config.effort` sin tocar el enricher."""
    if esfuerzo is None:
        return base

    def create(**kw):
        kw["output_config"] = {"effort": esfuerzo}
        return base.messages.create(**kw)

    return SimpleNamespace(messages=SimpleNamespace(create=create))


def _cliente_falso():
    texto = ('{"is_relevant": true, "relevance_reason": "simulado", "process_type": "otro",'
             ' "summary": "simulado", "fase": "otro", "plazas": 1}')

    def create(**kw):
        return SimpleNamespace(
            stop_reason="end_turn",
            content=[SimpleNamespace(type="text", text=texto)],
            usage=SimpleNamespace(input_tokens=1000, output_tokens=100,
                                  cache_creation_input_tokens=0, cache_read_input_tokens=0),
        )

    return SimpleNamespace(messages=SimpleNamespace(create=create))


if __name__ == "__main__":
    sys.exit(main())
