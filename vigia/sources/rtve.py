"""
Fuente RTVE — convocatorias de empleo de la Corporación de Radio y Televisión
Española publicadas en su **portal corporativo** (no en el BOE).

Contexto (research 2026-06-26): las grandes OPE de plaza fija de RTVE sí salen
en el BOE (las coge `boe.py` vía `DEPT_KEYWORDS_FOR_BODY`), pero las **bolsas /
bancos de datos para contratos de duración determinada** —entre ellas la de
"Enfermería de Empresa" (Enfermería del Trabajo), diana de este bot— se publican
**solo en el portal de RTVE**. El portal de inscripción `convocatorias.rtve.es`
es una SPA Angular inescrutable por `requests` (shell vacío), PERO la página
corporativa `www.rtve.es/corporacion/ofertas-empleo/` es **HTML server-rendered**
(alcanzable con `requests`) y lista cada convocatoria con título, entradilla y
enlace a las bases. Esa es la que parseamos.

Estructura del DOM (cada convocatoria es un módulo de noticia):
    article.cell > div.mod.notic_mod
        header.txtBox  > span.pretitle ("Convocatoria 1/2026")
                       > h3 span.maintitle ("Banco de Datos de Enfermería de Empresa")
        div.auxBox     > p (entradilla / descripción)
                       > ul.listing > li > a (Bases de la convocatoria → PDF)

**Matching:** la fuente solo aplica el filtro grueso `FAST_KEYWORDS` sobre
título+entradilla (mismo patrón que `epreselec.py`). La relevancia real
(Enfermería del Trabajo / de Empresa, salud laboral, prevención) la deciden los
STRONG/WEAK patterns del extractor aguas abajo. Validado el 2026-06-26: de los
módulos de la página, solo la convocatoria de "Enfermería de Empresa" pasa; el
resto (166 puestos fijos, contratos formativos, etc.) se descarta.

**Semántica de "listado actual":** la página muestra lo vigente ahora, sin fecha
de publicación fiable por convocatoria. Por eso emitimos con `date=today()` (no
filtramos por `since_date`: una convocatoria abierta puede haberse publicado
antes del primer cron) y dejamos que la deduplicación por `url` (estable: el PDF
de bases) evite re-alertar.
"""
from __future__ import annotations

import logging
import re
from datetime import date
from typing import Optional

import requests

from vigia.sources.base import RawItem, Source

logger = logging.getLogger(__name__)

RTVE_OFERTAS_URL = "https://www.rtve.es/corporacion/ofertas-empleo/"
FETCH_TIMEOUT = 30


class RTVESource(Source):
    name = "rtve"
    probe_url = RTVE_OFERTAS_URL

    def fetch(self, since_date: date) -> list[RawItem]:
        from bs4 import BeautifulSoup

        try:
            resp = requests.get(
                RTVE_OFERTAS_URL,
                headers=self._default_headers(),
                timeout=FETCH_TIMEOUT,
            )
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("RTVE ofertas-empleo error: %s", exc)
            self.last_errors.append(str(exc))
            return []

        # La página declara ISO-8859-1; requests lo respeta vía Content-Type.
        soup = BeautifulSoup(resp.text, "html.parser")
        mods = soup.select("article.cell div.mod.notic_mod")
        if not mods:
            # Estructura inesperada: la página cambió de maquetación. No es un
            # "0 convocatorias" normal — avisamos al operador (no llega al usuario).
            msg = "estructura inesperada: 0 módulos notic_mod en la página"
            logger.warning("RTVE: %s", msg)
            self.last_errors.append(msg)
            return []

        items: list[RawItem] = []
        seen_urls: set[str] = set()
        for mod in mods:
            item = self._parse_module(mod, seen_urls)
            if item is not None:
                items.append(item)
                logger.info("RTVE match: %s", item.title[:90])
        return items

    def _parse_module(self, mod, seen_urls: set[str]) -> Optional[RawItem]:
        title_el = mod.select_one(".maintitle") or mod.find(["h2", "h3"])
        if title_el is None:
            return None
        maintitle = title_el.get_text(" ", strip=True)
        if not maintitle:
            return None

        pre_el = mod.select_one(".pretitle")
        pretitle = pre_el.get_text(" ", strip=True) if pre_el else ""
        title = f"{pretitle}: {maintitle}" if pretitle else maintitle

        aux = mod.select_one(".auxBox")
        entradilla = ""
        if aux is not None:
            p = aux.find("p")
            entradilla = p.get_text(" ", strip=True) if p else ""

        # Filtro grueso: la relevancia fina la decide el extractor.
        if not _matches_fast_keywords(f"{title} {entradilla}"):
            return None

        url = _module_url(mod)
        if url in seen_urls:
            return None
        seen_urls.add(url)

        return RawItem(
            source=self.name,
            url=url,
            title=title,
            date=date.today(),
            text=entradilla,
            extra={"convocatoria": pretitle} if pretitle else {},
        )


# ---------------------------------------------------------------------------
# Helpers puros
# ---------------------------------------------------------------------------

def _matches_fast_keywords(text: str) -> bool:
    # Import perezoso: `vigia.config` resuelve símbolos del perfil activo.
    from vigia.config import FAST_KEYWORDS, normalize
    norm = normalize(text)
    return any(kw in norm for kw in FAST_KEYWORDS)


def _module_url(mod) -> str:
    """URL estable de la convocatoria para dedup y enlace. Preferimos el enlace
    a las bases (PDF específico y estable); si no hay, caemos a la página de
    ofertas con un ancla derivada del título."""
    link_el = (
        mod.select_one(".auxBox ul.listing a[href]")
        or mod.select_one(".auxBox a[href]")
    )
    if link_el is not None:
        href = link_el.get("href", "").strip()
        if href:
            return href
    title_el = mod.select_one(".maintitle") or mod.find(["h2", "h3"])
    from vigia.config import normalize
    raw = title_el.get_text(" ", strip=True) if title_el else ""
    slug = re.sub(r"[^a-z0-9]+", "-", normalize(raw)).strip("-")
    return f"{RTVE_OFERTAS_URL}#{slug}" if slug else RTVE_OFERTAS_URL
