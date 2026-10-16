"""
Fuente común para portales de empleo en Teamtailor.

Teamtailor publica todas las ofertas activas de un portal en un RSS público,
sin login: `https://<portal>/jobs.rss`. Cada `<item>` trae `title`, `link`
(enlace estable `/jobs/<id>-<slug>`), `pubDate` y, en el espacio de nombres
`https://teamtailor.com/locations`, una o varias `<location>` con `name`,
`city` y `country`. El RSS trae el portal entero (no hay que paginar).

Los portales los pone cada perfil en `source_params["teamtailor"]["portales"]`
(vacío por defecto: la fuente no hace nada). Por portal:
- `palabras`: filtro por título; vacío = FAST_KEYWORDS del perfil (leídas al
  usarlas, regla 7 del CLAUDE.md);
- `ubicaciones`: si no va vacío, la oferta tiene que tener alguna ubicación
  que contenga una de esas palabras (una oferta multisede vale si una de sus
  sedes encaja).
El mismo portal puede ir dos veces con filtros distintos.

Primer uso: vigia-docencia, SEK Education Group (16/10/2026).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from email.utils import parsedate
from typing import Optional
from xml.etree import ElementTree as ET

import requests

from vigia import config
from vigia.config import normalize
from vigia.profile import get_active_profile
from vigia.sources.base import RawItem, Source

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT = 30


@dataclass(frozen=True)
class TeamtailorPortal:
    code: str                 # "SEK_MADRID"
    nombre: str               # "SEK Education Group"
    rss_url: str              # "https://empleo.sek.es/jobs.rss"
    palabras: tuple = ()      # filtro por título; vacío = FAST_KEYWORDS
    ubicaciones: tuple = ()   # vacío = cualquier ubicación


def _portales() -> list[TeamtailorPortal]:
    params = get_active_profile().source_params.get("teamtailor", {})
    return list(params.get("portales", []))


class TeamtailorSource(Source):
    name = "teamtailor"

    @property
    def probe_url(self) -> str:  # type: ignore[override]
        portales = _portales()
        return portales[0].rss_url if portales else "https://www.teamtailor.com"

    def probe_content_count(self) -> int:
        counts = {}
        for p in _portales():
            try:
                counts[p.rss_url] = len(_items(self._get(p.rss_url)))
            except Exception:
                counts[p.rss_url] = 0
        self.probe_empty_listings = [u for u, n in counts.items() if n == 0]
        return min(counts.values()) if counts else 0

    def fetch(self, since_date: date) -> list[RawItem]:
        items: list[RawItem] = []
        cache: dict[str, bytes] = {}
        for portal in _portales():
            try:
                if portal.rss_url not in cache:
                    cache[portal.rss_url] = self._get(portal.rss_url)
            except Exception as exc:
                logger.warning("%s Teamtailor error: %s", portal.code, exc)
                self.last_errors.append(f"{portal.code}: {exc}")
                continue
            items.extend(self._parse(portal, cache[portal.rss_url], since_date))
        logger.info("Teamtailor: %d ofertas (%d portales)", len(items), len(_portales()))
        return items

    def _get(self, url: str) -> bytes:
        resp = requests.get(url, headers=self._default_headers(), timeout=_HTTP_TIMEOUT)
        resp.raise_for_status()
        return resp.content

    def _parse(
        self, portal: TeamtailorPortal, content: bytes, since_date: Optional[date]
    ) -> list[RawItem]:
        palabras = portal.palabras or tuple(config.FAST_KEYWORDS)
        out: list[RawItem] = []
        for title, url, pub, lugares in _items(content):
            if not any(p in normalize(title) for p in palabras):
                continue
            lugar = " / ".join(lugares)
            if portal.ubicaciones and not any(
                u in normalize(lugar) for u in portal.ubicaciones
            ):
                continue
            if since_date is not None and pub < since_date:
                continue
            out.append(RawItem(
                source=self.name,
                url=url,
                title=title,
                date=pub,
                text=f"{portal.nombre}. {lugar}",
                extra={"empresa": portal.code, "empresa_nombre": portal.nombre,
                       "lugar": lugar},
            ))
        return out


def _items(content: bytes) -> list[tuple]:
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return []
    out = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        url = (it.findtext("link") or "").strip()
        lugares = []
        for el in it.iter():
            if el.tag.split("}")[-1] == "location":
                partes = {c.tag.split("}")[-1]: (c.text or "").strip() for c in el}
                texto = ", ".join(
                    x for x in (partes.get("name"), partes.get("city"), partes.get("country")) if x
                )
                if texto:
                    lugares.append(texto)
        if title and url:
            out.append((title, url, _fecha(it.findtext("pubDate")), lugares))
    return out


def _fecha(raw: Optional[str]) -> date:
    parsed = parsedate(raw) if raw else None
    if parsed:
        try:
            return date(parsed[0], parsed[1], parsed[2])
        except ValueError:
            pass
    return date.today()
