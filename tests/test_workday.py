"""
Fuente genérica Workday (`*.myworkdayjobs.com`), primer uso en vigia-docencia
(Colegios CEU e ISP, 16/10/2026). Offline: se simula la API JSON.

Fallos que impiden:
- leer las 800 ofertas globales de ISP cada día: se para al salir de la ventana;
- fechas relativas mal convertidas ("Posted 30+ Days Ago" dentro de la ventana);
- ofertas sin `locationsText` rompiendo el lector (pasa en CEU);
- un portal roto tapado por otro en el probe;
- el probe en rojo a diario por mirar la raíz del dominio, que Workday
  contesta con 406 (daily de docencia del 19/10/2026).
"""
from __future__ import annotations

import dataclasses
from contextlib import contextmanager
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from vigia import profile as profile_mod
from vigia._default_profile import DEFAULT
from vigia.sources import workday
from vigia.sources.workday import WorkdayPortal, WorkdaySource, _fecha

HOY = date.today()

CEU = WorkdayPortal(
    "CEU_COL", "Colegios CEU", "https://ceu.wd3.myworkdayjobs.com", "ceu", "COL",
    facetas={"locations": ["id-madrid"]}, palabras=("historia", "sociales"),
)


@contextmanager
def _con_portales(portales):
    profile_mod.set_active_profile(dataclasses.replace(
        DEFAULT, source_params={"workday": {"portales": portales}},
    ))
    try:
        yield
    finally:
        profile_mod.set_active_profile(None)


def _resp(postings, total=None):
    r = MagicMock(status_code=200)
    r.json.return_value = {"total": total if total is not None else len(postings),
                           "jobPostings": postings}
    r.raise_for_status = lambda: None
    return r


def _o(title, posted, path, lugar="Madrid"):
    o = {"title": title, "postedOn": posted, "externalPath": path, "bulletFields": ["R1"]}
    if lugar is not None:
        o["locationsText"] = lugar
    return o


def test_fechas_relativas():
    assert _fecha("Posted Today", HOY) == HOY
    assert _fecha("Posted Yesterday", HOY) == HOY - timedelta(days=1)
    assert _fecha("Posted 7 Days Ago", HOY) == HOY - timedelta(days=7)
    assert _fecha("Posted 30+ Days Ago", HOY) == HOY - timedelta(days=31)
    assert _fecha("", HOY) is None


def test_filtra_palabras_ventana_y_tolera_sin_ubicacion():
    pagina = [
        _o("Profesor/a de Historia ESO", "Posted Today", "/job/Madrid/Historia_R1", lugar=None),
        _o("Profesor/a de Francés", "Posted Today", "/job/Madrid/Frances_R2"),
        _o("Ciencias Sociales Bachillerato", "Posted 10 Days Ago", "/job/Madrid/Sociales_R3"),
    ]
    with _con_portales([CEU]), patch.object(
        workday.requests, "post", side_effect=[_resp(pagina), _resp([])],
    ):
        items = WorkdaySource().fetch(since_date=HOY - timedelta(days=3))
    assert [i.title for i in items] == ["Profesor/a de Historia ESO"]
    assert items[0].url == "https://ceu.wd3.myworkdayjobs.com/COL/job/Madrid/Historia_R1"


def test_envia_facetas_y_para_al_salir_de_la_ventana():
    vieja = [_o("Historia", "Posted 30+ Days Ago", f"/job/x_{n}") for n in range(20)]
    with _con_portales([CEU]), patch.object(
        workday.requests, "post", side_effect=[_resp(vieja, total=800), _resp(vieja, total=800)],
    ) as post:
        WorkdaySource().fetch(since_date=HOY - timedelta(days=3))
    assert post.call_count == 1
    assert post.call_args.kwargs["json"]["appliedFacets"] == {"locations": ["id-madrid"]}


def test_sin_portales_no_hace_red():
    with _con_portales([]), patch.object(workday.requests, "post") as post:
        assert WorkdaySource().fetch(since_date=HOY) == []
    post.assert_not_called()


def test_probe_dice_que_portal_esta_vacio():
    otro = dataclasses.replace(CEU, code="ISP", url_base="https://isp.wd3.myworkdayjobs.com",
                               tenant="isp", site="ISP")

    def post(url, **kw):
        return _resp([] if "isp" in url else [_o("Historia", "Posted Today", "/job/a")])

    with _con_portales([CEU, otro]), patch.object(workday.requests, "post", side_effect=post):
        s = WorkdaySource()
        assert s.probe_content_count() == 0
        assert s.probe_empty_listings == [otro.api_url]


def test_para_al_llegar_al_total_y_no_repite():
    """Fallo visto contra la API real (16/10/2026): con `searchText`, pedir
    páginas más allá del total devuelve otra vez las mismas ofertas, y se
    repetían 10 veces."""
    cuatro = [_o(f"Spanish Teacher {n}", "Posted Today", f"/job/x/Spanish_{n}") for n in range(4)]
    portal = dataclasses.replace(CEU, facetas={}, busqueda="Spanish", palabras=("spanish",))
    with _con_portales([portal]), patch.object(
        workday.requests, "post", return_value=_resp(cuatro),
    ) as post:
        items = WorkdaySource().fetch(since_date=HOY - timedelta(days=3))
    assert post.call_count == 1
    assert len(items) == 4


def test_probe_mira_el_portal_y_no_la_raiz_del_dominio():
    """Daily de docencia del 19/10/2026: el probe daba 406 Not Acceptable en
    https://ceu.wd3.myworkdayjobs.com (también desde local) mientras la
    lectura iba bien. Workday solo sirve la página del portal (`/COL`)."""
    def http(url, **kw):
        r = MagicMock(status_code=406 if url.rstrip("/").endswith(".com") else 200,
                      reason="Not Acceptable")
        return r

    with _con_portales([CEU]),             patch("vigia.sources.base.requests.head", side_effect=http),             patch("vigia.sources.base.requests.get", side_effect=http),             patch.object(workday.requests, "post",
                         return_value=_resp([_o("Historia", "Posted Today", "/job/a")])):
        s = WorkdaySource()
        assert s.probe_url == "https://ceu.wd3.myworkdayjobs.com/COL"
        assert s.probe()["status"] == "ok"
