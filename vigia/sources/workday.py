"""
Fuente común para portales de empleo en Workday (`*.myworkdayjobs.com`).

Workday sirve el listado de cada portal por una API JSON pública, sin login:

    POST https://<tenant>.<wdN>.myworkdayjobs.com/wday/cxs/<tenant>/<site>/jobs
    {"appliedFacets": {...}, "limit": 20, "offset": N, "searchText": "..."}

Cada oferta trae `title`, `externalPath` (enlace estable con código R…/JR…),
`locationsText` (a veces falta o dice "3 Locations") y `postedOn` relativo
("Posted Today", "Posted Yesterday", "Posted 7 Days Ago", "Posted 30+ Days
Ago"). El listado va de más nueva a más antigua, así que se pagina hasta que
una página entera queda fuera de la ventana.

Los portales los pone cada perfil en `source_params["workday"]["portales"]`
(vacío por defecto: la fuente no hace nada). Para acotar por ubicación se usan
las facetas del propio portal, más fiables que el texto. Ojo: la clave a
enviar es la del nivel ANIDADO de la faceta, no `locationMainGroup` (da 400):
`locations` en CEU, `locationRegionStateProvince` en ISP. Se ve en el campo
`facets` de la propia respuesta. Pasado el total, la API repite resultados.
`palabras` filtra por título; si va vacío, se usan las FAST_KEYWORDS del perfil
(leídas al usarlas, no al importar: ver regla 7 del CLAUDE.md).

Primer uso: vigia-docencia, Colegios CEU e ISP (16/10/2026).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

import requests

from vigia import config
from vigia.config import normalize
from vigia.profile import get_active_profile
from vigia.sources.base import RawItem, Source

logger = logging.getLogger(__name__)

_PAGE_SIZE = 20
_MAX_PAGES = 10
_HTTP_TIMEOUT = 30
_HACE_RE = re.compile(r"(\d+)\+?\s+days?\s+ago", re.I)


@dataclass(frozen=True)
class WorkdayPortal:
    code: str                    # "CEU_COL"
    nombre: str                  # "Colegios CEU"
    url_base: str                # "https://ceu.wd3.myworkdayjobs.com"
    tenant: str                  # "ceu"
    site: str                    # "COL"
    facetas: dict = field(default_factory=dict)   # {"locationMainGroup": [id, …]}
    busqueda: str = ""           # searchText
    palabras: tuple = ()         # filtro por título; vacío = FAST_KEYWORDS

    @property
    def api_url(self) -> str:
        return f"{self.url_base}/wday/cxs/{self.tenant}/{self.site}/jobs"


def _portales() -> list[WorkdayPortal]:
    params = get_active_profile().source_params.get("workday", {})
    return list(params.get("portales", []))


class WorkdaySource(Source):
    name = "workday"

    @property
    def probe_url(self) -> str:  # type: ignore[override]
        # La página del portal, no la raíz del dominio: Workday contesta la
        # raíz con 406 aunque el portal funcione (daily de docencia, 19/10/2026).
        portales = _portales()
        return f"{portales[0].url_base}/{portales[0].site}" if portales else "https://www.myworkday.com"

    def probe_content_count(self) -> int:
        counts = {}
        for p in _portales():
            try:
                counts[p.api_url] = len(self._pagina(p, 0).get("jobPostings") or [])
            except Exception:
                counts[p.api_url] = 0
        self.probe_empty_listings = [u for u, n in counts.items() if n == 0]
        return min(counts.values()) if counts else 0

    def fetch(self, since_date: date) -> list[RawItem]:
        items: list[RawItem] = []
        for portal in _portales():
            items.extend(self._fetch_portal(portal, since_date))
        logger.info("Workday: %d ofertas (%d portales)", len(items), len(_portales()))
        return items

    def _pagina(self, portal: WorkdayPortal, offset: int) -> dict:
        resp = requests.post(
            portal.api_url,
            json={
                "appliedFacets": portal.facetas,
                "limit": _PAGE_SIZE,
                "offset": offset,
                "searchText": portal.busqueda,
            },
            headers={**self._default_headers(), "Accept": "application/json"},
            timeout=_HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def _fetch_portal(self, portal: WorkdayPortal, since_date: date) -> list[RawItem]:
        items: list[RawItem] = []
        vistas: set[str] = set()
        hoy = date.today()
        for page in range(_MAX_PAGES):
            offset = page * _PAGE_SIZE
            try:
                data = self._pagina(portal, offset)
            except Exception as exc:
                logger.warning("%s Workday error (página %d): %s", portal.code, page, exc)
                self.last_errors.append(f"{portal.code} página {page}: {exc}")
                break
            ofertas = data.get("jobPostings") or []
            if not ofertas:
                break
            fechas = []
            for o in ofertas:
                pub = _fecha(o.get("postedOn"), hoy)
                fechas.append(pub)
                item = self._item(portal, o, pub, since_date)
                if item is not None and item.url not in vistas:
                    vistas.add(item.url)
                    items.append(item)
            # Pasado el total, la API repite resultados: fin.
            if offset + len(ofertas) >= int(data.get("total") or 0):
                break
            # De más nueva a más antigua: si toda la página queda fuera, fin.
            if all(f is not None and f < since_date for f in fechas):
                break
        return items

    def _item(
        self, portal: WorkdayPortal, oferta: dict, pub: Optional[date], since_date: date
    ) -> Optional[RawItem]:
        title = (oferta.get("title") or "").strip()
        path = (oferta.get("externalPath") or "").strip()
        if not title or not path:
            return None
        palabras = portal.palabras or tuple(config.FAST_KEYWORDS)
        if not any(p in normalize(title) for p in palabras):
            return None
        pub = pub or date.today()
        if pub < since_date:
            return None
        lugar = (oferta.get("locationsText") or "").strip()
        return RawItem(
            source=self.name,
            url=f"{portal.url_base}/{portal.site}{path}",
            title=title,
            date=pub,
            text=f"{portal.nombre}. {lugar}",
            extra={"empresa": portal.code, "empresa_nombre": portal.nombre, "lugar": lugar},
        )


def _fecha(posted_on: Optional[str], hoy: date) -> Optional[date]:
    """'Posted Today' / 'Posted Yesterday' / 'Posted N Days Ago' / 'Posted
    30+ Days Ago' → fecha. "30+" se toma como 31 (seguro fuera de ventana)."""
    texto = (posted_on or "").lower()
    if "today" in texto:
        return hoy
    if "yesterday" in texto:
        return hoy - timedelta(days=1)
    m = _HACE_RE.search(texto)
    if m:
        dias = int(m.group(1)) + (1 if "+" in texto else 0)
        return hoy - timedelta(days=dias)
    return None
