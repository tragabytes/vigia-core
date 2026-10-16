"""
Modelo del enricher por perfil, precarga y modelo testigo (spec 002, H2).

Fallos que impiden:
- que los modelos nuevos se queden sin plazo en las ofertas de portales: no
  abren la página por su cuenta y el texto que llega es de ~100 caracteres
  (banco de prueba del 16/10/2026);
- que durante la prueba de un modelo nuevo se pierda un aviso: si el testigo
  (el modelo de siempre) la ve relevante, se avisa igual;
- que un perfil sin modelo propio cambie de modelo sin querer.
"""
from __future__ import annotations

import logging
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from vigia import enricher
from vigia.storage import Item


def _json(relevante):
    return ('{"is_relevant": %s, "summary": "ok", "process_type": "otro", "fase": "otro"}'
            % ("true" if relevante else "false"))


def _resp(texto):
    return SimpleNamespace(stop_reason="end_turn",
                           content=[SimpleNamespace(type="text", text=texto)],
                           usage=None)


def _item(raw="Oferta corta"):
    it = Item(source="todoele", url="https://todoele.net/ofertas-trabajo/x",
              titulo="Spanish teacher", fecha=date(2026, 10, 16), categoria="otro")
    it.extra = {"raw_text": raw}
    return it


def _cliente(monkeypatch, respuestas):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    fake = MagicMock()
    fake.messages.create.side_effect = respuestas
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", lambda: fake)
    return fake


def test_sin_modelo_propio_sigue_sonnet_46_sin_esfuerzo(monkeypatch):
    fake = _cliente(monkeypatch, [_resp(_json(True))])
    with patch.object(enricher, "_fetch_body_full") as fetch:
        enricher.enrich([_item("corta")])
    fetch.assert_not_called()          # Sonnet 4.6 abre la página él solo
    kw = fake.messages.create.call_args.kwargs
    assert kw["model"] == "claude-sonnet-4-6"
    assert kw["max_tokens"] == 2048
    assert "output_config" not in kw


def test_modelo_nuevo_con_esfuerzo_bajo(monkeypatch):
    fake = _cliente(monkeypatch, [_resp(_json(True))])
    monkeypatch.setattr(enricher, "MODEL", "claude-haiku-5-5")
    enricher.enrich([_item("x" * 600)])
    kw = fake.messages.create.call_args.kwargs
    assert kw["model"] == "claude-haiku-5-5"
    assert kw["max_tokens"] == 8000
    assert kw["output_config"] == {"effort": "low"}


def test_texto_corto_se_completa_con_la_pagina(monkeypatch):
    fake = _cliente(monkeypatch, [_resp(_json(True))])
    monkeypatch.setattr(enricher, "MODEL", "claude-haiku-5-5")
    with patch.object(enricher, "_fetch_body_full",
                      return_value="Closing date: 22 October 2026") as fetch:
        enricher.enrich([_item("Oferta corta")])
    fetch.assert_called_once()
    enviado = fake.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "Closing date: 22 October 2026" in enviado


def test_texto_largo_no_se_descarga(monkeypatch):
    _cliente(monkeypatch, [_resp(_json(True))])
    monkeypatch.setattr(enricher, "MODEL", "claude-haiku-5-5")
    with patch.object(enricher, "_fetch_body_full") as fetch:
        enricher.enrich([_item("x" * 600)])
    fetch.assert_not_called()


def test_si_el_testigo_la_ve_relevante_se_avisa(monkeypatch, caplog):
    fake = _cliente(monkeypatch, [_resp(_json(False)), _resp(_json(True))])
    monkeypatch.setattr(enricher, "MODEL", "claude-haiku-5-5")
    monkeypatch.setattr(enricher, "TESTIGO", "claude-sonnet-4-6")
    with caplog.at_level(logging.INFO, logger="vigia.enricher"):
        out = enricher.enrich([_item("x" * 600)])
    modelos = [c.kwargs["model"] for c in fake.messages.create.call_args_list]
    assert modelos == ["claude-haiku-5-5", "claude-sonnet-4-6"]
    assert out[0].is_relevant is True
    assert "Testigo: claude-haiku-5-5 dice NO y claude-sonnet-4-6 dice SÍ" in caplog.text
    assert "Testigo: 1 discrepancias en 1 items" in caplog.text


def test_si_el_testigo_falla_queda_lo_del_modelo(monkeypatch):
    _cliente(monkeypatch, [_resp(_json(True)), RuntimeError("caída")])
    monkeypatch.setattr(enricher, "MODEL", "claude-haiku-5-5")
    monkeypatch.setattr(enricher, "TESTIGO", "claude-sonnet-4-6")
    out = enricher.enrich([_item("x" * 600)])
    assert out[0].is_relevant is True
