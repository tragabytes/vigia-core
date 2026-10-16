"""
Ventana por defecto del daily (`_default_since`).

Fallo que impide: con `since` = ayer, lo publicado un día en que una fuente
fallaba (timeout, 404 pasajero, run caído) quedaba fuera del filtro al día
siguiente: se perdía, no se retrasaba (DECISIONES D15, aprobado el
16/10/2026). Con 2 días de margen, un aviso perdido se recupera en los dos
runs siguientes; la deduplicación por `id_hash` evita avisos repetidos.
"""
from __future__ import annotations

from datetime import date

import pytest

import vigia.main as main_module


def _con_hoy(monkeypatch, hoy: date) -> None:
    class _Fecha(date):
        @classmethod
        def today(cls):
            return hoy

    monkeypatch.setattr(main_module, "date", _Fecha)


@pytest.mark.parametrize("hoy, esperado", [
    (date(2026, 10, 14), date(2026, 10, 11)),  # miércoles → domingo
    (date(2026, 10, 16), date(2026, 10, 13)),  # viernes → martes
    (date(2026, 10, 12), date(2026, 10, 7)),   # lunes → miércoles
])
def test_mira_tres_dias_atras_y_los_lunes_desde_el_miercoles(monkeypatch, hoy, esperado):
    _con_hoy(monkeypatch, hoy)
    assert main_module._default_since() == esperado
