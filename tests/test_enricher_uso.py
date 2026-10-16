"""
Uso de la API en el enricher (spec 002, H1).

Fallos que impiden:
- no saber cuánto gasta el bot (no había ningún registro de tokens);
- pagar entero, en cada vuelta del bucle, el prompt de sistema y los
  documentos ya enviados (sin caché);
- convocatorias que se quedan sin resumir para siempre cuando la API falla un
  día (pasó del 22 al 29/09/2026: límite de gasto agotado).
"""
from __future__ import annotations

import logging
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from vigia import enricher
from vigia.storage import Item, Storage

_JSON = '{"is_relevant": true, "summary": "ok", "process_type": "oposicion", "fase": "convocatoria"}'


def _usage(i, o, cw=0, cr=0):
    return SimpleNamespace(input_tokens=i, output_tokens=o,
                           cache_creation_input_tokens=cw, cache_read_input_tokens=cr)


def _resp(stop, blocks, usage):
    return SimpleNamespace(stop_reason=stop, content=blocks, usage=usage)


def _item(t="Convocatoria", url="https://www.boe.es/x?id=1"):
    return Item(source="boe", url=url, titulo=t, fecha=date(2026, 10, 1), categoria="oposicion")


def _client_con(respuestas, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    fake = MagicMock()
    fake.messages.create.side_effect = respuestas
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", lambda: fake)
    return fake


def test_registra_los_tokens_del_run(monkeypatch, caplog):
    tool = SimpleNamespace(type="tool_use", id="t1", name="fetch_url",
                           input={"url": "https://www.boe.es/x"})
    _client_con([
        _resp("tool_use", [tool], _usage(1000, 50, cw=1800)),
        _resp("end_turn", [SimpleNamespace(type="text", text=_JSON)], _usage(9000, 400, cr=2900)),
    ], monkeypatch)
    with patch.object(enricher, "_run_fetch_url", return_value="cuerpo"), \
            caplog.at_level(logging.INFO, logger="vigia.enricher"):
        enricher.enrich([_item()])
    assert ("Enricher uso: 2 llamadas, entrada 10000, salida 450, "
            "caché escrita 1800, caché leída 2900") in caplog.text


def test_marca_caché_en_el_sistema_y_en_el_último_resultado(monkeypatch):
    tool = SimpleNamespace(type="tool_use", id="t1", name="fetch_url",
                           input={"url": "https://www.boe.es/x"})
    fake = _client_con([
        _resp("tool_use", [tool], _usage(1, 1)),
        _resp("end_turn", [SimpleNamespace(type="text", text=_JSON)], _usage(1, 1)),
    ], monkeypatch)
    with patch.object(enricher, "_run_fetch_url", return_value="cuerpo"):
        enricher.enrich([_item()])

    primera = fake.messages.create.call_args_list[0].kwargs
    assert primera["system"][0]["cache_control"] == {"type": "ephemeral"}
    segunda = fake.messages.create.call_args_list[1].kwargs
    ultimo_user = segunda["messages"][-1]["content"]
    assert ultimo_user[-1]["type"] == "tool_result"
    assert ultimo_user[-1]["cache_control"] == {"type": "ephemeral"}


def test_respuestas_sin_usage_no_rompen(monkeypatch):
    fake = _client_con([SimpleNamespace(
        stop_reason="end_turn", content=[SimpleNamespace(type="text", text=_JSON)])], monkeypatch)
    out = enricher.enrich([_item()])
    assert out[0].is_relevant is True
    assert fake.messages.create.call_count == 1


def test_reintento_solo_de_los_nunca_resumidos_y_sin_los_de_hoy(tmp_path):
    s = Storage(db_path=tmp_path / "seen.db")
    viejo = _item("Vieja sin resumir", "https://www.boe.es/x?id=viejo")
    hoy = _item("De hoy, recién fallada", "https://www.boe.es/x?id=hoy")
    resumido = _item("Ya resumida", "https://www.boe.es/x?id=ok")
    for it in (viejo, hoy, resumido):
        s.save(it)
    resumido.enriched_version = 1          # versión antigua: no se re-resume a diario
    s.update_enrichment(resumido)

    vistos = []

    def fake_enrich(items):
        vistos.extend(i.titulo for i in items)
        return items

    with patch.object(enricher, "enrich", side_effect=fake_enrich), \
            patch.object(enricher, "_fetch_body_full", return_value="cuerpo"):
        enricher.enrich_pending(s, solo_sin_resumir=True, excluir={hoy.id_hash}, limite=20)
    s.close()
    assert vistos == ["Vieja sin resumir"]
