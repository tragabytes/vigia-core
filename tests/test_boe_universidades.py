"""
BOE: convocatorias de personal NO docente de universidades.

Fallo que impide: en el BOE todas las universidades salen bajo el
departamento "Universidades", que no está en la whitelist de cuerpos a
descargar, y sus convocatorias de personal llevan títulos genéricos
("…plazas de personal laboral"). Caso real: BOE-A-2024-18785 (UPM,
19/09/2024) incluía la plaza L900088 de Enfermería del Trabajo y el bot la
habría descartado sin abrirla. Solo se abren las de personal laboral /
PTGAS / PAS: las de profesorado (la mayoría, a diario) no.
"""
from __future__ import annotations

from datetime import date
from unittest.mock import patch

from vigia.sources.boe import BOESource

TITULO_UPM_2024 = (
    "Resolución de 12 de septiembre de 2024, de la Universidad Politécnica "
    "de Madrid, por la que se convoca proceso selectivo para la provisión, "
    "por el sistema general de acceso libre, de plazas de personal laboral."
)
CUERPO_UPM_2024 = (
    "ANEXO I. Plaza L900088. Titulado Primer Ciclo. Enfermería, con la "
    "especialidad Enfermería del Trabajo. Grupo II."
)


def _build(titulo: str):
    with patch.object(
        BOESource, "_fetch_html_with_pdf_links", return_value=(CUERPO_UPM_2024, [])
    ) as fake_html:
        item = BOESource()._build_raw_item(
            titulo=titulo,
            url_html="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-18785",
            target=date(2024, 9, 19),
            sec_code="2B",
            dept_name="Universidades",
        )
    return item, fake_html


def test_personal_laboral_de_universidad_se_abre_y_matchea():
    item, fake_html = _build(TITULO_UPM_2024)
    fake_html.assert_called_once()
    assert item is not None
    assert "Enfermería del Trabajo" in item.text


def test_ptgas_de_universidad_tambien_se_abre():
    _, fake_html = _build(
        "Resolución de la Universidad Rey Juan Carlos, por la que se convoca "
        "proceso selectivo de Personal Técnico, de Gestión y de Administración "
        "y Servicios (PTGAS)."
    )
    fake_html.assert_called_once()


def test_profesorado_de_universidad_no_se_abre():
    item, fake_html = _build(
        "Resolución de la Universidad de Granada, por la que se convoca "
        "concurso de acceso a plazas de cuerpos docentes universitarios."
    )
    fake_html.assert_not_called()
    assert item is None
