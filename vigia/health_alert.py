"""
Alerta de salud de fuentes vía GitHub issue.

Lee el `sources_status.json` que produce `--probe` y mantiene UNA issue de salud
por repositorio: la abre/actualiza cuando hay fuentes en `status == "error"`
(URL caída o selector roto) y la cierra cuando todo vuelve a estar OK.

La señal es el PROBE, no los `last_errors` del pipeline (dominados por timeouts
transitorios) — así la alerta es señal, no ruido.

Idempotente y silencioso: sin `GITHUB_REPOSITORY`/`GITHUB_TOKEN` (runs locales)
hace no-op, igual que el enricher sin `ANTHROPIC_API_KEY`. Nunca aborta.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
# Marcador oculto en el body para localizar la issue de salud sin depender de
# labels (que habría que crear/gestionar). El set de fuentes se embebe aparte
# para detectar cambios sin comentar en cada probe.
_MARKER = "<!-- vigia-health -->"
_SET_RE = re.compile(r"<!-- set:(.*?) -->")
_TITLE = "🔴 Fuentes con error en el probe"
_TIMEOUT = 20


def run_health_issue(status_path: Path) -> int:
    """Punto de entrada del modo `--health-issue`. Devuelve exit code (0)."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not repo or not token:
        logger.info(
            "health-issue: sin GITHUB_REPOSITORY/GH_TOKEN — no-op (run local)"
        )
        return 0

    failing = _read_failing_sources(Path(status_path))
    if failing is None:
        logger.info("health-issue: sources_status.json ausente/ilegible — no-op")
        return 0

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })

    existing = _find_open_issue(session, repo)

    if failing:
        if existing is None:
            _create_issue(session, repo, failing)
            logger.info(
                "health-issue: creada issue con %d fuentes en error", len(failing)
            )
        else:
            _update_issue(session, repo, existing, failing)
            logger.info(
                "health-issue: actualizada issue #%s (%d fuentes)",
                existing["number"], len(failing),
            )
    elif existing is not None:
        _close_issue(session, repo, existing)
        logger.info("health-issue: cerrada issue #%s (todo OK)", existing["number"])
    else:
        logger.info("health-issue: sin errores y sin issue abierta — nada que hacer")
    return 0


def _read_failing_sources(status_path: Path) -> Optional[list[dict]]:
    """Fuentes con `status == "error"` del sources_status.json.

    Devuelve `None` si el fichero no existe o no es legible (no podemos afirmar
    "todo OK", así que el caller hace no-op y NO cierra la issue por error).
    """
    try:
        data = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("health-issue: no se pudo leer %s: %s", status_path, exc)
        return None
    if not isinstance(data, list):
        return None
    failing = [
        {
            "name": e.get("name", "?"),
            "code": e.get("code"),
            "detail": e.get("detail", "") or "",
            "url": e.get("url", "") or "",
        }
        for e in data
        if isinstance(e, dict) and e.get("status") == "error"
    ]
    failing.sort(key=lambda e: e["name"])
    return failing


def _source_set(failing: list[dict]) -> str:
    return ",".join(e["name"] for e in failing)


def _render_body(failing: list[dict]) -> str:
    lines = [
        _MARKER,
        f"<!-- set:{_source_set(failing)} -->",
        "",
        "El probe diario ha detectado fuentes con **error** (URL caída o selector",
        "roto). Los timeouts transitorios quedan fuera: esto apunta a un fallo real.",
        "",
        "| Fuente | Code | Detalle | URL |",
        "|---|---|---|---|",
    ]
    for e in failing:
        detail = e["detail"].replace("|", "\\|").replace("\n", " ")[:120]
        lines.append(f"| `{e['name']}` | {e['code']} | {detail} | {e['url']} |")
    lines += [
        "",
        "_Esta issue se actualiza sola en cada probe y se cierra al recuperarse._",
    ]
    return "\n".join(lines)


def _find_open_issue(session: requests.Session, repo: str) -> Optional[dict]:
    resp = session.get(
        f"{GITHUB_API}/repos/{repo}/issues",
        params={"state": "open", "per_page": 100},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    for issue in resp.json():
        if "pull_request" in issue:
            continue  # /issues también lista PRs
        if _MARKER in (issue.get("body") or ""):
            return issue
    return None


def _create_issue(session: requests.Session, repo: str, failing: list[dict]) -> None:
    session.post(
        f"{GITHUB_API}/repos/{repo}/issues",
        json={"title": f"{_TITLE} ({len(failing)})", "body": _render_body(failing)},
        timeout=_TIMEOUT,
    ).raise_for_status()


def _update_issue(
    session: requests.Session, repo: str, issue: dict, failing: list[dict]
) -> None:
    number = issue["number"]
    prev_match = _SET_RE.search(issue.get("body") or "")
    prev_set = prev_match.group(1) if prev_match else ""
    changed = _source_set(failing) != prev_set
    # Refresca siempre el body (códigos/detalles pueden variar) y el título.
    session.patch(
        f"{GITHUB_API}/repos/{repo}/issues/{number}",
        json={"title": f"{_TITLE} ({len(failing)})", "body": _render_body(failing)},
        timeout=_TIMEOUT,
    ).raise_for_status()
    # Comenta SOLO si cambió el conjunto de fuentes (evita spam diario).
    if changed:
        names = ", ".join(e["name"] for e in failing)
        session.post(
            f"{GITHUB_API}/repos/{repo}/issues/{number}/comments",
            json={"body": f"⚠️ Conjunto de fuentes en error actualizado: {names}"},
            timeout=_TIMEOUT,
        ).raise_for_status()


def _close_issue(session: requests.Session, repo: str, issue: dict) -> None:
    number = issue["number"]
    session.post(
        f"{GITHUB_API}/repos/{repo}/issues/{number}/comments",
        json={"body": "✅ Todas las fuentes vuelven a estar OK en el probe. Cerrando."},
        timeout=_TIMEOUT,
    ).raise_for_status()
    session.patch(
        f"{GITHUB_API}/repos/{repo}/issues/{number}",
        json={"state": "closed"},
        timeout=_TIMEOUT,
    ).raise_for_status()
