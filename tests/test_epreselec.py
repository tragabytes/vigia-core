"""
Tests del parser ePreselec (ATS multi-tenant ASP.NET, HTML server-rendered).

Estructura confirmada vía HTTP crudo 2026-06-13 con Fraternidad-Muprespa:
  <li>
    <a data_idoferta="3325662" href="javascript:__doPostBack(...)">
      <span class="op-titulo">{título}</span>
      <span class="op-provincia">{provincia}, España</span>
      <span class="op-fecha">DD de MES, YYYY</span>
    </a>
  </li>

La fuente solo aplica el filtro grueso FAST_KEYWORDS ("enfermer") sobre el
título; la relevancia real (Enf. del Trabajo vs. asistencial) la deciden los
STRONG/WEAK patterns aguas abajo, no esta fuente. Los tenants los inyecta el
perfil vía source_params["epreselec"]["empresas"].
"""
from __future__ import annotations

import dataclasses
from contextlib import contextmanager
from datetime import date
from unittest.mock import MagicMock, patch

from vigia import profile as profile_mod
from vigia._default_profile import DEFAULT
from vigia.sources import epreselec
from vigia.sources.epreselec import EpreselecEmpresa, EpreselecSource, _parse_es_date


def _resp(text: str, status: int = 200):
    r = MagicMock()
    r.status_code = status
    r.text = text
    r.raise_for_status = lambda: None
    return r


_TENANT = EpreselecEmpresa("TEST", "Test SPA", "https://test.epreselec.com")


@contextmanager
def _con_tenants(empresas):
    """Fija un perfil de prueba con los tenants dados y restaura al salir."""
    profile_mod.set_active_profile(
        dataclasses.replace(DEFAULT, source_params={"epreselec": {"empresas": empresas}})
    )
    try:
        yield
    finally:
        profile_mod.set_active_profile(None)  # vuelve al DEFAULT perezoso


# HTML representativo recortado del portal real (Fraternidad). 3 ofertas: una de
# Enfermería del Trabajo, una de enfermería asistencial (también lleva
# "enfermer", la fuente la deja pasar; el extractor la descarta luego) y una de
# Médico (sin "enfermer", la fuente la descarta).
EPRESELEC_HTML = """
<html><body><ul>
  <li>
    <a data_idoferta="111" href="javascript:__doPostBack('x','')">
      <div class="row"><div class="col-md-12">
        <span class="op-titulo">Enfermero/a del Trabajo MADRID (Servicio de Prevención) </span>
        <span class="op-provincia">Madrid, España</span>
        <span class="op-fecha"> 12 de junio, 2026</span>
      </div></div>
    </a>
  </li>
  <li>
    <a data_idoferta="222" href="javascript:__doPostBack('y','')">
      <div class="row"><div class="col-md-12">
        <span class="op-titulo">Enfermero/a URGENCIAS MADRID CENTRO (Sustitución) </span>
        <span class="op-provincia">Madrid, España</span>
        <span class="op-fecha"> 11 de junio, 2026</span>
      </div></div>
    </a>
  </li>
  <li>
    <a data_idoferta="333" href="javascript:__doPostBack('z','')">
      <div class="row"><div class="col-md-12">
        <span class="op-titulo">Médico/a Asistencial Mutua MÁLAGA </span>
        <span class="op-provincia">Málaga, España</span>
        <span class="op-fecha"> 1 de junio, 2026</span>
      </div></div>
    </a>
  </li>
</ul></body></html>
"""


class TestEpreselecSource:
    def test_extrae_solo_ofertas_con_keyword(self):
        source = EpreselecSource()
        with _con_tenants([_TENANT]), patch.object(
            epreselec.requests, "get", return_value=_resp(EPRESELEC_HTML),
        ):
            items = source.fetch(since_date=date(2000, 1, 1))

        # Las dos de enfermería pasan; el médico (sin "enfermer") no.
        assert len(items) == 2
        titles = " ".join(it.title.upper() for it in items)
        assert "ENFERMERO/A DEL TRABAJO" in titles
        assert "URGENCIAS" in titles
        assert "MÉDICO" not in titles

    def test_url_sintetica_por_idoferta_y_fecha(self):
        source = EpreselecSource()
        with _con_tenants([_TENANT]), patch.object(
            epreselec.requests, "get", return_value=_resp(EPRESELEC_HTML),
        ):
            items = source.fetch(since_date=date(2000, 1, 1))

        item = items[0]
        assert item.url == "https://test.epreselec.com/Ofertas/Ofertas.aspx?idOferta=111"
        assert item.date == date(2026, 6, 12)
        assert item.source == "epreselec"
        assert item.extra["empresa"] == "TEST"
        assert item.extra["provincia"] == "Madrid, España"

    def test_filtra_por_since_date(self):
        source = EpreselecSource()
        with _con_tenants([_TENANT]), patch.object(
            epreselec.requests, "get", return_value=_resp(EPRESELEC_HTML),
        ):
            items = source.fetch(since_date=date(2026, 6, 12))

        # Solo la del 12 de junio entra; la del 11 (y el médico) quedan fuera.
        assert len(items) == 1
        assert items[0].date == date(2026, 6, 12)

    def test_sin_tenants_no_hace_red(self):
        source = EpreselecSource()
        with _con_tenants([]), patch.object(
            epreselec.requests, "get", return_value=_resp(EPRESELEC_HTML),
        ) as fake_get:
            items = source.fetch(since_date=date(2000, 1, 1))

        assert items == []
        fake_get.assert_not_called()

    def test_listado_caido_devuelve_lista_vacia_con_error(self):
        source = EpreselecSource()
        with _con_tenants([_TENANT]), patch.object(
            epreselec.requests, "get", side_effect=Exception("connection reset"),
        ):
            items = source.fetch(since_date=date(2000, 1, 1))

        assert items == []
        assert source.last_errors and "connection reset" in source.last_errors[0]

    def test_probe_url_es_listado(self):
        assert EpreselecSource.probe_url == \
            "https://fraternidad.epreselec.com/Ofertas/Ofertas.aspx"


class TestParseFecha:
    def test_formato_largo_con_de_y_coma(self):
        assert _parse_es_date("12 de junio, 2026") == date(2026, 6, 12)

    def test_formato_abreviado_sin_de(self):
        assert _parse_es_date("5 jun 2026") == date(2026, 6, 5)

    def test_texto_sin_fecha(self):
        assert _parse_es_date("próximamente") is None
        assert _parse_es_date("") is None
