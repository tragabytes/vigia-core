"""
Tests de la alerta de salud por GitHub issue (vigia/health_alert.py).

Mockea `requests.Session` para no llamar a la API real. Verifica:
- no-op sin credenciales / sin sources_status.json,
- crear issue cuando hay fuentes en error y no existe,
- actualizar + comentar solo si cambia el conjunto de fuentes,
- cerrar la issue cuando todo vuelve a OK,
- ignorar las PRs al buscar la issue de salud.
"""
from __future__ import annotations

import json

from vigia import health_alert


class _Resp:
    def __init__(self, data=None):
        self._data = data if data is not None else []

    def json(self):
        return self._data

    def raise_for_status(self):
        pass


class _FakeSession:
    def __init__(self, open_issues):
        self.headers = {}
        self._open_issues = open_issues
        self.calls = []  # (method, url, payload)

    def get(self, url, params=None, timeout=None):
        self.calls.append(("GET", url, params))
        return _Resp(self._open_issues)

    def post(self, url, json=None, timeout=None):
        self.calls.append(("POST", url, json))
        return _Resp({})

    def patch(self, url, json=None, timeout=None):
        self.calls.append(("PATCH", url, json))
        return _Resp({})


def _write_status(tmp_path, entries):
    p = tmp_path / "sources_status.json"
    p.write_text(json.dumps(entries), encoding="utf-8")
    return p


def _install(monkeypatch, open_issues):
    fake = _FakeSession(open_issues)
    monkeypatch.setattr(health_alert.requests, "Session", lambda: fake)
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GH_TOKEN", "t0ken")
    return fake


def _methods(fake):
    return [c[0] for c in fake.calls]


def test_no_op_sin_token(monkeypatch, tmp_path):
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setattr(
        health_alert.requests, "Session",
        lambda: (_ for _ in ()).throw(AssertionError("no debe crear sesión")),
    )
    p = _write_status(tmp_path, [{"name": "boe", "status": "error"}])
    assert health_alert.run_health_issue(p) == 0


def test_no_op_si_falta_el_json(monkeypatch, tmp_path):
    fake = _install(monkeypatch, open_issues=[])
    health_alert.run_health_issue(tmp_path / "no_existe.json")
    assert fake.calls == []  # ni siquiera busca la issue


def test_crea_issue_si_hay_error_y_no_existe(monkeypatch, tmp_path):
    fake = _install(monkeypatch, open_issues=[])
    p = _write_status(tmp_path, [
        {"name": "isciii", "status": "error", "code": 500, "detail": "500", "url": "u"},
        {"name": "boe", "status": "ok"},
    ])
    health_alert.run_health_issue(p)
    posts = [c for c in fake.calls if c[0] == "POST"]
    assert len(posts) == 1
    assert posts[0][1].endswith("/issues")
    assert "isciii" in posts[0][2]["body"]
    assert health_alert._MARKER in posts[0][2]["body"]


def test_actualiza_y_comenta_si_cambia_el_set(monkeypatch, tmp_path):
    existing = [{"number": 7, "body": health_alert._MARKER + "\n<!-- set:boe -->"}]
    fake = _install(monkeypatch, existing)
    p = _write_status(tmp_path, [
        {"name": "boe", "status": "error", "code": None, "detail": "", "url": ""},
        {"name": "isciii", "status": "error", "code": 500, "detail": "x", "url": ""},
    ])
    health_alert.run_health_issue(p)
    assert any(c[0] == "PATCH" and "/issues/7" in c[1] for c in fake.calls)
    comments = [c for c in fake.calls if c[0] == "POST" and c[1].endswith("/7/comments")]
    assert len(comments) == 1  # el set cambió (boe → boe,isciii)


def test_no_comenta_si_el_set_no_cambia(monkeypatch, tmp_path):
    existing = [{"number": 7, "body": health_alert._MARKER + "\n<!-- set:boe,isciii -->"}]
    fake = _install(monkeypatch, existing)
    p = _write_status(tmp_path, [
        {"name": "boe", "status": "error"},
        {"name": "isciii", "status": "error"},
    ])
    health_alert.run_health_issue(p)
    assert any(c[0] == "PATCH" for c in fake.calls)  # refresca el body
    assert not any(
        c[0] == "POST" and c[1].endswith("/comments") for c in fake.calls
    )


def test_cierra_issue_si_todo_ok(monkeypatch, tmp_path):
    existing = [{"number": 9, "body": health_alert._MARKER + "\n<!-- set:boe -->"}]
    fake = _install(monkeypatch, existing)
    p = _write_status(tmp_path, [{"name": "boe", "status": "ok"}])
    health_alert.run_health_issue(p)
    assert any(c[0] == "POST" and c[1].endswith("/9/comments") for c in fake.calls)
    assert any(
        c[0] == "PATCH" and c[2].get("state") == "closed" for c in fake.calls
    )


def test_no_op_si_todo_ok_y_no_hay_issue(monkeypatch, tmp_path):
    fake = _install(monkeypatch, open_issues=[])
    p = _write_status(tmp_path, [{"name": "boe", "status": "ok"}])
    health_alert.run_health_issue(p)
    assert _methods(fake) == ["GET"]  # solo busca; no crea ni cierra


def test_ignora_pull_requests_al_buscar(monkeypatch, tmp_path):
    existing = [
        {"number": 1, "pull_request": {}, "body": health_alert._MARKER + "<!-- set:x -->"},
    ]
    fake = _install(monkeypatch, existing)
    p = _write_status(tmp_path, [{"name": "boe", "status": "error"}])
    health_alert.run_health_issue(p)
    # La "existing" era una PR → se ignora → se crea una issue nueva.
    assert any(c[0] == "POST" and c[1].endswith("/issues") for c in fake.calls)
