"""
Tests del parser RTVE (página corporativa server-rendered de ofertas de empleo).

Cubre:
  1. De varios módulos de convocatoria, solo emite los que pasan FAST_KEYWORDS
     (la convocatoria de "Enfermería de Empresa"); el resto se descarta en la
     fuente, sin necesidad del extractor.
  2. El RawItem emitido lo matchea el extractor aguas abajo.
  3. URL estable = enlace a las bases (PDF) para dedup.
  4. Tolerancia a fallos: HTTP error y excepción de red no levantan, registran
     en `last_errors` y devuelven [].
  5. Si la maquetación cambia (0 módulos), se registra un error de estructura
     (distinto de "hoy no hay convocatoria de enfermería").
"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from vigia.extractor import extract
from vigia.sources.rtve import RTVESource

BASES_URL = (
    "https://www.rtve.es/contenidos/corporacion/rrhh/"
    "otras_convocatorias/BasesBBDD_Enfermeria-Empresa.pdf"
)


def _resp(html: str, status: int = 200):
    r = MagicMock()
    r.status_code = status
    r.text = html
    if status >= 400:
        r.raise_for_status = MagicMock(side_effect=Exception(f"HTTP {status}"))
    else:
        r.raise_for_status = lambda: None
    return r


# Dos módulos como en la página real: la convocatoria de Enfermería de Empresa
# (relevante) y la oferta general de 166 puestos fijos (no sanitaria).
HTML_OK = f"""
<html><body>
<div class="gridBox">
  <article class="cell">
    <div class="mod notic_mod txtsize_03"><div class="mainBox">
      <header class="txtBox">
        <span class="pretitle">Convocatoria 1/2026</span>
        <h3><span class="maintitle">Banco de Datos de Enfermería de Empresa</span></h3>
      </header>
      <div class="auxBox">
        <p>Convocatoria 1/2026 de pruebas específicas para el acceso al Banco de
        Datos de otras modalidades de contratos de duración determinada respecto a
        la ocupación tipo &ldquo;Enfermería de Empresa&rdquo; de la Corporación de
        Radio y Televisión Española, S.A., S.M.E.</p>
        <ul class="listing ul">
          <li><a href="{BASES_URL}">Bases de la convocatoria</a></li>
        </ul>
        <p><strong>Inscripciones</strong>: del 15 de junio hasta el 5 de julio de
        2026, en <a href="https://www.convocatorias.rtve.es">www.convocatorias.rtve.es</a>.</p>
      </div>
    </div></div>
  </article>
  <article class="cell">
    <div class="mod notic_mod txtsize_03"><div class="mainBox">
      <header class="txtBox">
        <span class="pretitle">29/12/2025</span>
        <h3><span class="maintitle">Oferta de 166 puestos</span></h3>
      </header>
      <div class="auxBox">
        <p>Cobertura de puestos de trabajo de personal fijo de la Corporación.</p>
        <ul class="listing ul">
          <li><a href="https://www.rtve.es/contenidos/corporacion/rrhh/convocatorias/RTVE_Convocatoria_1-2025.pdf">Bases</a></li>
        </ul>
      </div>
    </div></div>
  </article>
</div>
</body></html>
"""

HTML_SIN_MODULOS = "<html><body><div class='gridBox'><p>Página en mantenimiento</p></div></body></html>"


def test_fetch_emite_solo_la_convocatoria_de_enfermeria():
    src = RTVESource()
    with patch("vigia.sources.rtve.requests.get", return_value=_resp(HTML_OK)):
        items = src.fetch(date(2026, 1, 1))

    assert len(items) == 1
    raw = items[0]
    assert raw.source == "rtve"
    assert "Enfermería de Empresa" in raw.title
    assert raw.url == BASES_URL          # dedup estable por el PDF de bases
    assert raw.date == date.today()      # semántica de "listado actual"
    assert src.last_errors == []
    # La oferta general de 166 puestos NO se emite (no pasa FAST_KEYWORDS).
    assert all("166" not in it.title for it in items)


def test_item_emitido_matchea_el_extractor():
    src = RTVESource()
    with patch("vigia.sources.rtve.requests.get", return_value=_resp(HTML_OK)):
        raw = src.fetch(date(2026, 1, 1))[0]
    item = extract(raw)
    assert item is not None              # "enfermería de empresa" es STRONG


def test_fetch_http_error_no_levanta_y_registra_last_errors():
    src = RTVESource()
    with patch("vigia.sources.rtve.requests.get", return_value=_resp("", status=500)):
        items = src.fetch(date(2026, 1, 1))
    assert items == []
    assert len(src.last_errors) == 1


def test_fetch_excepcion_de_red_no_levanta_y_registra_last_errors():
    src = RTVESource()
    with patch("vigia.sources.rtve.requests.get",
               side_effect=Exception("connection reset")):
        items = src.fetch(date(2026, 1, 1))
    assert items == []
    assert len(src.last_errors) == 1
    assert "connection reset" in src.last_errors[0]


def test_estructura_inesperada_registra_error_distinto():
    """0 módulos = la página cambió de maquetación, no 'hoy no hay enfermería'."""
    src = RTVESource()
    with patch("vigia.sources.rtve.requests.get", return_value=_resp(HTML_SIN_MODULOS)):
        items = src.fetch(date(2026, 1, 1))
    assert items == []
    assert len(src.last_errors) == 1
    assert "estructura" in src.last_errors[0].lower()
