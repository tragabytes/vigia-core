"""
Fuente común para portales de empleo basados en **ePreselec** (Adevinta Jobs),
un ATS multi-tenant en ASP.NET WebForms. Cada empresa expone su listado en
`https://{org}.epreselec.com/Ofertas/Ofertas.aspx`, que devuelve HTML
server-side completo de las ofertas activas — sin WAF, sin login. Confirmado en
el research del 2026-06-13 con Fraternidad-Muprespa (12 ofertas en página 1,
incluidas varias de Enfermería).

A diferencia de SAP SuccessFactors, ePreselec **no expone una URL GET por
oferta**: el detalle se abre con `__doPostBack` (navegación ViewState). Por eso:
- Cada oferta es un `<a data_idoferta="...">` (lxml minúscula el atributo) con:
    · título    → `<span class="op-titulo">`
    · provincia → `<span class="op-provincia">`  (a `extra`)
    · fecha     → `<span class="op-fecha">DD de MES, YYYY</span>`
- Como `url` única (para dedup y enlace) construimos una sintética estable a
  partir del id de oferta: `{portal}/Ofertas/Ofertas.aspx?idOferta={id}`. El
  server ignora el parámetro pero aterriza al usuario en el listado correcto.

**Tenants desde el perfil:** la lista de empresas NO se hardcodea aquí (esta
fuente es genérica del core); la inyecta el perfil activo vía
`Profile.source_params["epreselec"]["empresas"]` (mismo patrón que `boe.py`).
Si el perfil no aporta empresas, `fetch()` devuelve [] sin error.

**Paginación:** ePreselec pagina con `__doPostBack` (POST + `__VIEWSTATE`), no
con query params. Para un watcher diario basta la primera página (las ofertas
nuevas salen arriba, orden descendente por fecha). La paginación postback queda
como follow-up; hoy solo se lee la página 1.

**Matching:** la fuente solo aplica el filtro grueso `FAST_KEYWORDS` sobre el
título. La relevancia real (Enfermería del Trabajo vs. enfermería asistencial)
la deciden los STRONG/WEAK patterns del extractor aguas abajo. Validado el
2026-06-13: las ofertas asistenciales de Fraternidad ("Enfermero/a URGENCIAS")
se descartan correctamente; solo pasan las tituladas "del trabajo / salud
laboral / servicio de prevención".
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

import requests

from vigia.profile import get_active_profile
from vigia.sources.base import RawItem, Source

logger = logging.getLogger(__name__)

# Meses en español (el listado usa nombre largo: "12 de junio, 2026").
_MESES_ES = {
    "ene": 1, "enero": 1,
    "feb": 2, "febrero": 2,
    "mar": 3, "marzo": 3,
    "abr": 4, "abril": 4,
    "may": 5, "mayo": 5,
    "jun": 6, "junio": 6,
    "jul": 7, "julio": 7,
    "ago": 8, "agosto": 8,
    "sep": 9, "sept": 9, "septiembre": 9, "setiembre": 9,
    "oct": 10, "octubre": 10,
    "nov": 11, "noviembre": 11,
    "dic": 12, "diciembre": 12,
}

# "12 de junio, 2026" (coma opcional, "de" opcional para tolerar variantes).
_DATE_ES = re.compile(
    r"\b(\d{1,2})\s+(?:de\s+)?([a-záéíóúñ]+)\.?,?\s+(\d{4})\b",
    re.IGNORECASE,
)


@dataclass
class EpreselecEmpresa:
    code: str            # "FRATERNIDAD"
    nombre: str          # "Fraternidad-Muprespa"
    portal_url: str      # "https://fraternidad.epreselec.com"


def _epreselec_empresas() -> list[EpreselecEmpresa]:
    """Lista de tenants leída del perfil activo EN RUNTIME (no en import-time).

    Vacía por defecto: esta fuente es genérica y solo actúa si el perfil
    declara empresas en `source_params["epreselec"]["empresas"]`.
    """
    params = get_active_profile().source_params.get("epreselec", {})
    return list(params.get("empresas", []))


class EpreselecSource(Source):
    name = "epreselec"
    probe_url = "https://fraternidad.epreselec.com/Ofertas/Ofertas.aspx"

    def fetch(self, since_date: date) -> list[RawItem]:
        empresas = _epreselec_empresas()
        all_items: list[RawItem] = []
        for emp in empresas:
            all_items.extend(self._fetch_empresa(emp, since_date))
        logger.info(
            "ePreselec: %d items relevantes (%d empresas)",
            len(all_items), len(empresas),
        )
        return all_items

    def _fetch_empresa(self, emp: EpreselecEmpresa, since_date: date) -> list[RawItem]:
        from bs4 import BeautifulSoup

        listado = f"{emp.portal_url}/Ofertas/Ofertas.aspx"
        try:
            resp = requests.get(
                listado, headers=self._default_headers(), timeout=20
            )
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("%s ofertas error: %s", emp.code, exc)
            self.last_errors.append(f"{emp.code}: {exc}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        items: list[RawItem] = []
        seen_urls: set[str] = set()
        for anchor in soup.select("a[data_idoferta]"):
            item = self._parse_card(anchor, emp, since_date, seen_urls)
            if item is not None:
                items.append(item)
                logger.info("%s match: %s", emp.code, item.title[:90])
        return items

    def _parse_card(
        self, anchor, emp: EpreselecEmpresa, since_date: date, seen_urls: set[str]
    ) -> Optional[RawItem]:
        titulo_el = anchor.select_one(".op-titulo")
        if titulo_el is None:
            return None
        title = titulo_el.get_text(" ", strip=True)
        if not title or not _matches_fast_keywords(title):
            return None

        oid = anchor.get("data_idoferta") or ""
        item_url = _build_url(emp.portal_url, oid, title)
        if item_url in seen_urls:
            return None

        fecha_el = anchor.select_one(".op-fecha")
        date_text = fecha_el.get_text(" ", strip=True) if fecha_el else ""
        pub_date = _parse_es_date(date_text) or date.today()
        if pub_date < since_date:
            return None

        prov_el = anchor.select_one(".op-provincia")
        provincia = prov_el.get_text(" ", strip=True) if prov_el else ""

        seen_urls.add(item_url)
        return RawItem(
            source=self.name,
            url=item_url,
            title=title,
            date=pub_date,
            text="",
            extra={
                "empresa": emp.code,
                "empresa_nombre": emp.nombre,
                "provincia": provincia,
            },
        )


# ---------------------------------------------------------------------------
# Helpers puros (sin red).
# ---------------------------------------------------------------------------

def _matches_fast_keywords(text: str) -> bool:
    # Import perezoso: `vigia.config` resuelve símbolos del perfil activo, y esta
    # fuente la importa el propio perfil en su carga (evita import circular).
    from vigia.config import FAST_KEYWORDS, normalize
    norm = normalize(text)
    return any(kw in norm for kw in FAST_KEYWORDS)


def _build_url(portal_url: str, oid: str, title: str) -> str:
    """URL sintética estable por oferta. ePreselec no tiene detalle por GET
    (el detalle va por `__doPostBack`), así que enlazamos al listado con el id
    de oferta como ancla determinista para dedup. Si no hay id, caemos a un
    fragment derivado del título normalizado."""
    base = f"{portal_url}/Ofertas/Ofertas.aspx"
    if oid:
        return f"{base}?idOferta={oid}"
    from vigia.config import normalize
    slug = re.sub(r"[^a-z0-9]+", "-", normalize(title)).strip("-")
    return f"{base}#{slug}" if slug else base


def _parse_es_date(text: str) -> Optional[date]:
    """Parsea fechas españolas tipo '12 de junio, 2026' o '5 jun 2026'."""
    if not text:
        return None
    m = _DATE_ES.search(text)
    if not m:
        return None
    mes_token = m.group(2).lower().rstrip(".")
    mes = _MESES_ES.get(mes_token)
    if mes is None:
        return None
    try:
        return date(int(m.group(3)), mes, int(m.group(1)))
    except ValueError:
        return None
