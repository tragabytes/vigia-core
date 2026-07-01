"""
Tests del probe de salud de fuentes (--probe).

Verifica que:
- Source.probe() devuelve "ok" cuando la URL responde 2xx/3xx.
- Devuelve "error" cuando responde 4xx/5xx o lanza excepción.
- Devuelve "skipped" si la fuente no tiene probe_url (caso stubs).
- main.py --probe sale con código 0 si todas OK/skipped, 1 si alguna error.
"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from vigia.sources.base import RawItem, Source


class _StubSource(Source):
    """Fuente sin probe_url: el probe debe devolver 'skipped'."""
    name = "stub"
    # probe_url heredado None de la base.

    def fetch(self, since_date: date) -> list[RawItem]:
        return []


class _ProbedSource(Source):
    """Fuente con probe_url para los tests."""
    name = "probed"
    probe_url = "https://example.com/probe"

    def fetch(self, since_date: date) -> list[RawItem]:
        return []


# ---------------------------------------------------------------------------
# Tests directos del método Source.probe()
# ---------------------------------------------------------------------------

class TestSourceProbe:
    def test_skipped_si_no_hay_probe_url(self):
        s = _StubSource()
        result = s.probe()
        assert result["name"] == "stub"
        assert result["status"] == "skipped"
        assert result["code"] is None
        assert result["url"] is None

    def test_ok_si_head_devuelve_200(self, monkeypatch):
        head_mock = MagicMock()
        head_mock.return_value = MagicMock(status_code=200, reason="OK")

        monkeypatch.setattr("vigia.sources.base.requests.head", head_mock)

        s = _ProbedSource()
        result = s.probe()
        assert result["status"] == "ok"
        assert result["code"] == 200
        assert result["url"] == "https://example.com/probe"

    def test_ok_si_redirige_3xx_y_termina_en_200(self, monkeypatch):
        # `allow_redirects=True` ya lo gestiona requests; el resultado final
        # es lo que llega al objeto resp.
        head_mock = MagicMock(return_value=MagicMock(status_code=200, reason="OK"))
        monkeypatch.setattr("vigia.sources.base.requests.head", head_mock)

        s = _ProbedSource()
        assert s.probe()["status"] == "ok"

    def test_error_si_404(self, monkeypatch):
        head_mock = MagicMock(return_value=MagicMock(status_code=404, reason="Not Found"))
        get_mock = MagicMock(return_value=MagicMock(
            status_code=404, reason="Not Found", close=MagicMock()
        ))
        monkeypatch.setattr("vigia.sources.base.requests.head", head_mock)
        monkeypatch.setattr("vigia.sources.base.requests.get", get_mock)

        s = _ProbedSource()
        result = s.probe()
        assert result["status"] == "error"
        assert result["code"] == 404
        assert "Not Found" in result["detail"]

    def test_fallback_a_get_si_head_da_4xx(self, monkeypatch):
        """Algunos servidores rechazan HEAD; debe reintentar con GET."""
        head_mock = MagicMock(return_value=MagicMock(status_code=405, reason="Method Not Allowed"))
        get_mock = MagicMock(return_value=MagicMock(
            status_code=200, reason="OK", close=MagicMock()
        ))
        monkeypatch.setattr("vigia.sources.base.requests.head", head_mock)
        monkeypatch.setattr("vigia.sources.base.requests.get", get_mock)

        s = _ProbedSource()
        result = s.probe()
        assert result["status"] == "ok"
        assert result["code"] == 200
        # Debe haber llamado a get tras el HEAD fallido
        get_mock.assert_called_once()

    def test_error_si_excepcion_de_red(self, monkeypatch):
        from requests.exceptions import ConnectionError
        head_mock = MagicMock(side_effect=ConnectionError("connection refused"))
        monkeypatch.setattr("vigia.sources.base.requests.head", head_mock)

        s = _ProbedSource()
        result = s.probe()
        assert result["status"] == "error"
        assert result["code"] is None
        assert "connection refused" in result["detail"]


# ---------------------------------------------------------------------------
# Content-check reforzado (anti "probe ≠ runtime")
# ---------------------------------------------------------------------------

class TestProbeContentCheck:
    def _ok_head(self, monkeypatch):
        head_mock = MagicMock(return_value=MagicMock(status_code=200, reason="OK"))
        monkeypatch.setattr("vigia.sources.base.requests.head", head_mock)

    def test_error_si_content_count_cero(self, monkeypatch):
        """HTTP 200 pero el selector no rinde nada → 'error' (caso UAH)."""
        self._ok_head(monkeypatch)

        class _ZeroSource(_ProbedSource):
            name = "zero"
            def probe_content_count(self):
                return 0

        result = _ZeroSource().probe()
        assert result["status"] == "error"
        assert result["code"] == 200
        assert "selector" in result["detail"].lower()

    def test_ok_si_content_count_positivo(self, monkeypatch):
        self._ok_head(monkeypatch)

        class _NonZeroSource(_ProbedSource):
            name = "nonzero"
            def probe_content_count(self):
                return 7

        assert _NonZeroSource().probe()["status"] == "ok"

    def test_ok_si_no_hay_override(self, monkeypatch):
        """Sin override (default None), el probe valida solo HTTP (no-breaking)."""
        self._ok_head(monkeypatch)
        assert _ProbedSource().probe()["status"] == "ok"

    def test_error_si_content_check_lanza(self, monkeypatch):
        self._ok_head(monkeypatch)

        class _RaisingSource(_ProbedSource):
            name = "raising"
            def probe_content_count(self):
                raise RuntimeError("boom")

        result = _RaisingSource().probe()
        assert result["status"] == "error"
        assert "content-check" in result["detail"]

    def test_probe_count_selector_cuenta_y_excluye(self, monkeypatch):
        html = (
            "<html><body>"
            "<div class='card'>a</div>"
            "<div class='card filtro'>panel</div>"
            "<div class='card'>b</div>"
            "</body></html>"
        )
        get_mock = MagicMock(return_value=MagicMock(
            status_code=200, text=html, raise_for_status=MagicMock(),
        ))
        monkeypatch.setattr("vigia.sources.base.requests.get", get_mock)

        s = _ProbedSource()
        assert s._probe_count_selector("https://x/listado", "div.card") == 3
        assert s._probe_count_selector(
            "https://x/listado", "div.card", exclude_classes=("filtro",)
        ) == 2


# ---------------------------------------------------------------------------
# Test del flag --probe de main.py
# ---------------------------------------------------------------------------

class TestMainProbe:
    @staticmethod
    def _isolate(monkeypatch, tmp_path):
        """Aísla los efectos secundarios de --probe (BD + export dashboard)."""
        from vigia import main as main_module
        from vigia import storage as storage_module

        monkeypatch.setattr(storage_module, "DB_PATH", tmp_path / "seen.db")
        monkeypatch.setattr(
            main_module, "DASHBOARD_OUT_DIR", str(tmp_path / "dashboard"),
        )

    def test_exit_code_0_si_todas_ok_o_skipped(self, monkeypatch, tmp_path, capsys):
        """Con todas las fuentes 'ok' o 'skipped', main --probe debe salir con 0."""
        from vigia import main as main_module
        self._isolate(monkeypatch, tmp_path)

        class _OkSource(Source):
            name = "ok_source"
            probe_url = "https://example.com"
            def fetch(self, since_date): return []
            def probe(self, timeout=10):
                return {"name": "ok_source", "status": "ok", "code": 200,
                        "url": "https://example.com", "detail": ""}

        monkeypatch.setattr(main_module, "SOURCE_REGISTRY", {"ok_source": _OkSource})
        monkeypatch.setattr(main_module, "SOURCES_ENABLED", ["ok_source"])
        monkeypatch.setattr("sys.argv", ["main.py", "--probe"])

        with pytest.raises(SystemExit) as excinfo:
            main_module.main()
        assert excinfo.value.code == 0

    def test_exit_code_1_si_alguna_fuente_falla(self, monkeypatch, tmp_path):
        """Con al menos una fuente 'error', main --probe debe salir con 1."""
        from vigia import main as main_module
        self._isolate(monkeypatch, tmp_path)

        class _OkSource(Source):
            name = "ok_source"
            probe_url = "https://example.com"
            def fetch(self, since_date): return []
            def probe(self, timeout=10):
                return {"name": "ok_source", "status": "ok", "code": 200,
                        "url": "https://example.com", "detail": ""}

        class _BrokenSource(Source):
            name = "broken_source"
            probe_url = "https://broken.example.com"
            def fetch(self, since_date): return []
            def probe(self, timeout=10):
                return {"name": "broken_source", "status": "error", "code": 403,
                        "url": "https://broken.example.com", "detail": "Forbidden"}

        monkeypatch.setattr(
            main_module, "SOURCE_REGISTRY",
            {"ok_source": _OkSource, "broken_source": _BrokenSource},
        )
        monkeypatch.setattr(
            main_module, "SOURCES_ENABLED", ["ok_source", "broken_source"]
        )
        monkeypatch.setattr("sys.argv", ["main.py", "--probe"])

        with pytest.raises(SystemExit) as excinfo:
            main_module.main()
        assert excinfo.value.code == 1

    def test_probe_exporta_dashboard_con_estado_vivo(
        self, monkeypatch, tmp_path
    ):
        """`--probe` debe refrescar sources_status.json con los probe_results
        del run, no solo dejar contadores en blanco."""
        import json
        from vigia import main as main_module
        self._isolate(monkeypatch, tmp_path)

        class _OkSource(Source):
            name = "ok_source"
            probe_url = "https://example.com"
            def fetch(self, since_date): return []
            def probe(self, timeout=10):
                return {"name": "ok_source", "status": "ok", "code": 200,
                        "url": "https://example.com", "detail": ""}

        monkeypatch.setattr(main_module, "SOURCE_REGISTRY", {"ok_source": _OkSource})
        monkeypatch.setattr(main_module, "SOURCES_ENABLED", ["ok_source"])
        monkeypatch.setattr("sys.argv", ["main.py", "--probe"])

        with pytest.raises(SystemExit):
            main_module.main()

        sources = json.loads(
            (tmp_path / "dashboard" / "sources_status.json").read_text(encoding="utf-8")
        )
        by_name = {s["name"]: s for s in sources}
        assert "ok_source" in by_name
        assert by_name["ok_source"]["status"] == "ok"
        assert by_name["ok_source"]["code"] == 200
