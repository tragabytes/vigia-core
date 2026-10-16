"""
BOCM: convocatorias de personal NO docente de universidades de Madrid.

Fallo que impide: el mismo hueco que en el BOE (ver
test_boe_universidades.py). Las universidades no estaban en HEALTH_ORGS y
el PDF de una convocatoria de personal laboral nunca se abría, aunque
dentro hubiera una plaza de Enfermería del Trabajo.
"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from vigia.sources.bocm import BOCMSource

XML = """<?xml version="1.0" encoding="UTF-8"?>
<sumario><diario><seccion nombre="B) Autoridades y Personal"><apartado>
  <organismo nombre="UNIVERSIDAD POLITÉCNICA DE MADRID">
    <disposicion>
      <identificador>BOCM-20261016-1</identificador>
      <titulo>{titulo}</titulo>
      <url_html>https://www.bocm.es/bocm-20261016-1</url_html>
      <url_pdf>https://www.bocm.es/1.PDF</url_pdf>
    </disposicion>
  </organismo>
</apartado></seccion></diario></sumario>
"""


def _parse(titulo: str):
    resp = MagicMock(content=XML.format(titulo=titulo).encode("utf-8"))
    resp.raise_for_status = lambda: None
    with patch("vigia.sources.bocm.requests.get", return_value=resp), patch.object(
        BOCMSource, "_extract_pdf_text",
        return_value="Plaza de Titulado Medio, especialidad Enfermería del Trabajo.",
    ) as fake_pdf:
        items = BOCMSource()._parse_xml("https://x/sumario.xml", date(2026, 10, 16))
    return items, fake_pdf


def test_convocatoria_de_personal_laboral_se_abre_y_matchea():
    items, fake_pdf = _parse(
        "Resolución por la que se convoca proceso selectivo de plazas de personal laboral."
    )
    fake_pdf.assert_called_once()
    assert len(items) == 1
    assert "Enfermería del Trabajo" in items[0].text


def test_convocatoria_de_profesorado_no_se_abre():
    items, fake_pdf = _parse(
        "Resolución por la que se convoca concurso de plazas de profesorado contratado doctor."
    )
    fake_pdf.assert_not_called()
    assert items == []
