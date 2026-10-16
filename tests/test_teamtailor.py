"""
Fuente genérica Teamtailor (RSS `/jobs.rss`), primer uso en vigia-docencia
(SEK Education Group, 16/10/2026). Offline, con un RSS recortado del real.

Fallos que impiden: ofertas de otras sedes colándose cuando el perfil pide
ubicación; ofertas multisede perdidas aunque una sede encaje; un portal leído
dos veces cuando va con dos filtros; un portal roto tapado en el probe.
"""
from __future__ import annotations

import dataclasses
from contextlib import contextmanager
from datetime import date
from unittest.mock import MagicMock, patch

from vigia import profile as profile_mod
from vigia._default_profile import DEFAULT
from vigia.sources import teamtailor
from vigia.sources.teamtailor import TeamtailorPortal, TeamtailorSource

RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:tt="https://teamtailor.com/locations"><channel>
<item><title>Spanish Teacher. SEK International School - Turtle Bay</title>
 <link>https://empleo.sek.es/jobs/8544268-spanish-teacher</link><pubDate>Wed, 14 Oct 2026 10:00:00 +0000</pubDate>
 <tt:locations><tt:location><tt:name>Red Sea Region</tt:name><tt:city>Red Sea Region</tt:city><tt:country>Saudi Arabia</tt:country></tt:location></tt:locations></item>
<item><title>Profesor/a de Geografía e Historia</title>
 <link>https://empleo.sek.es/jobs/1-geografia-historia</link><pubDate>Tue, 13 Oct 2026 10:00:00 +0000</pubDate>
 <tt:locations><tt:location><tt:name>Villanueva de la Cañada, Madrid, España</tt:name><tt:city>Villanueva de la Cañada</tt:city><tt:country>Spain</tt:country></tt:location></tt:locations></item>
<item><title>Profesor/a de Historia (varias sedes)</title>
 <link>https://empleo.sek.es/jobs/2-historia-multisede</link><pubDate>Tue, 13 Oct 2026 10:00:00 +0000</pubDate>
 <tt:locations><tt:location><tt:name>Catalunya</tt:name><tt:city>La Garriga</tt:city><tt:country>Spain</tt:country></tt:location>
 <tt:location><tt:name></tt:name><tt:city>Alcobendas</tt:city><tt:country>Spain</tt:country></tt:location></tt:locations></item>
<item><title>Profesor/a de Historia</title>
 <link>https://empleo.sek.es/jobs/3-historia-garriga</link><pubDate>Mon, 05 Oct 2026 10:00:00 +0000</pubDate>
 <tt:locations><tt:location><tt:name>Catalunya</tt:name><tt:city>La Garriga</tt:city><tt:country>Spain</tt:country></tt:location></tt:locations></item>
</channel></rss>""".encode("utf-8")

MADRID = TeamtailorPortal("SEK_MADRID", "SEK", "https://empleo.sek.es/jobs.rss",
                          palabras=("historia",), ubicaciones=("madrid", "alcobendas"))
ELE = TeamtailorPortal("SEK_ELE", "SEK", "https://empleo.sek.es/jobs.rss",
                       palabras=("spanish",))


@contextmanager
def _con_portales(portales):
    profile_mod.set_active_profile(dataclasses.replace(
        DEFAULT, source_params={"teamtailor": {"portales": portales}},
    ))
    try:
        yield
    finally:
        profile_mod.set_active_profile(None)


def _resp(content):
    r = MagicMock(status_code=200, content=content)
    r.raise_for_status = lambda: None
    return r


def test_filtros_de_ubicacion_y_palabras_y_un_solo_get_por_rss():
    with _con_portales([MADRID, ELE]), patch.object(
        teamtailor.requests, "get", return_value=_resp(RSS),
    ) as get:
        items = TeamtailorSource().fetch(since_date=date(2026, 10, 1))
    assert get.call_count == 1
    assert {(i.extra["empresa"], i.title) for i in items} == {
        ("SEK_MADRID", "Profesor/a de Geografía e Historia"),
        ("SEK_MADRID", "Profesor/a de Historia (varias sedes)"),   # una sede en Alcobendas
        ("SEK_ELE", "Spanish Teacher. SEK International School - Turtle Bay"),
    }


def test_ventana_de_fechas():
    with _con_portales([MADRID]), patch.object(
        teamtailor.requests, "get", return_value=_resp(RSS),
    ):
        items = TeamtailorSource().fetch(since_date=date(2026, 10, 14))
    assert items == []


def test_probe_dice_que_portal_esta_vacio():
    otro = dataclasses.replace(ELE, code="X", rss_url="https://x.teamtailor.com/jobs.rss")
    with _con_portales([MADRID, otro]), patch.object(
        teamtailor.requests, "get",
        side_effect=lambda url, **kw: _resp(b"<rss/>" if "x.teamtailor" in url else RSS),
    ):
        s = TeamtailorSource()
        assert s.probe_content_count() == 0
        assert s.probe_empty_listings == ["https://x.teamtailor.com/jobs.rss"]
