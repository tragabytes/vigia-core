"""
Tests del Incremento 3: mejor extracción de `deadline_inscripcion`.

Cubre:
  - Inyección de snippets de la sección de PLAZO en el prompt del enricher
    (independiente de las keywords de especialidad).
  - Parseo de `deadline_estimated` en `_apply_enrichment`.
  - Persistencia + round-trip de `deadline_estimated` (storage).
  - Marcador "(estimada)"/"fecha estimada" en el notifier (item y recordatorio).
"""
from __future__ import annotations

from datetime import date

from vigia.enricher import (
    _SNIPPET_KEYWORDS_DEADLINE,
    _apply_enrichment,
    _build_initial_user_content,
    _extract_relevant_snippets,
)
from vigia.notifier import _format_countdown, _format_item, _format_reminder
from vigia.storage import DeadlineReminder, Item, Storage


# ---------------------------------------------------------------------------
# Inyección de snippets de plazo
# ---------------------------------------------------------------------------

class TestDeadlineSnippets:
    def test_extrae_ventana_de_plazo(self):
        text = (
            "Bla bla generalidades del proceso. " * 50
            + "El plazo de presentación de solicitudes será de 20 días hábiles "
            "a partir del día siguiente al de la publicación en el BOE. " * 1
            + "Más texto irrelevante. " * 50
        )
        snips = _extract_relevant_snippets(
            text, keywords=_SNIPPET_KEYWORDS_DEADLINE, max_snippets=2,
        )
        joined = " ".join(snips)
        assert "20 días hábiles" in joined
        assert "plazo de presentación" in joined.lower()

    def test_default_sin_keywords_no_cambia(self):
        # Sin keywords explícitas usa el comportamiento HIGH/LOW de siempre:
        # un texto solo con sección de plazo (sin especialidad) NO produce
        # snippets por la vía por defecto.
        text = "El plazo de presentación será de 15 días naturales."
        assert _extract_relevant_snippets(text) == []

    def test_build_user_content_inyecta_plazo_lejano(self):
        # La sección de plazo vive MÁS ALLÁ de los primeros 4000 chars (fuera
        # del head) y lejos de la mención de especialidad → solo entra por el
        # snippet de plazo dedicado.
        raw = (
            "Convocatoria de Enfermería del Trabajo. "
            + ("relleno " * 800)  # ~6400 chars de relleno
            + "Plazo de presentación de instancias: 10 días hábiles a partir "
            "del día siguiente al de la publicación."
        )
        item = Item(
            source="boe", url="https://e/x", titulo="Conv",
            fecha=date(2026, 6, 1), categoria="oposicion",
            extra={"raw_text": raw},
        )
        content = _build_initial_user_content(item)
        assert "10 días hábiles" in content
        assert "plazo de presentación" in content.lower()


# ---------------------------------------------------------------------------
# _apply_enrichment — deadline_estimated
# ---------------------------------------------------------------------------

def _bare_item() -> Item:
    return Item(source="boe", url="https://e/x", titulo="C",
                fecha=date(2026, 6, 1), categoria="oposicion")


class TestApplyEnrichmentEstimated:
    def test_estimated_true(self):
        item = _bare_item()
        _apply_enrichment(item, {
            "deadline_inscripcion": "2026-06-20", "deadline_estimated": True,
        })
        assert item.deadline_inscripcion == "2026-06-20"
        assert item.deadline_estimated is True

    def test_estimated_false_por_defecto_si_hay_deadline(self):
        item = _bare_item()
        _apply_enrichment(item, {"deadline_inscripcion": "2026-06-20"})
        assert item.deadline_estimated is False

    def test_estimated_none_si_no_hay_deadline(self):
        item = _bare_item()
        _apply_enrichment(item, {"deadline_inscripcion": None,
                                 "deadline_estimated": True})
        assert item.deadline_inscripcion is None
        assert item.deadline_estimated is None


# ---------------------------------------------------------------------------
# Storage — round-trip de deadline_estimated
# ---------------------------------------------------------------------------

class TestStorageEstimatedRoundTrip:
    def test_update_y_iter_devuelve_estimated(self, tmp_path):
        s = Storage(db_path=tmp_path / "seen.db")
        today = date(2026, 6, 13)
        item = Item(source="boe", url="https://e/x", titulo="Conv",
                    fecha=date(2026, 6, 1), categoria="oposicion")
        s.save(item)
        item.deadline_inscripcion = "2026-06-18"
        item.deadline_estimated = True
        item.is_relevant = True
        item.enriched_version = 6
        s.update_enrichment(item)
        rows = s.iter_items_with_open_deadline(today)
        s.close()
        assert len(rows) == 1
        assert rows[0].deadline_estimated is True


# ---------------------------------------------------------------------------
# Notifier — marcador "(estimada)"
# ---------------------------------------------------------------------------

class TestNotifierEstimatedMarker:
    def test_countdown_estimado(self):
        out = _format_countdown("2026-06-20", date(2026, 6, 13), estimated=True)
        assert "estimada" in out
        assert "en 7 días" in out

    def test_countdown_no_estimado_sin_marcador(self):
        out = _format_countdown("2026-06-20", date(2026, 6, 13), estimated=False)
        assert "estimada" not in out

    def test_item_block_muestra_estimada(self):
        item = Item(source="boe", url="https://e/x", titulo="Conv",
                    fecha=date(2026, 6, 1), categoria="oposicion",
                    deadline_inscripcion="2026-06-20", deadline_estimated=True)
        joined = "\n".join(_format_item(item, date(2026, 6, 13)))
        assert "estimada" in joined

    def test_reminder_muestra_estimada(self):
        rem = DeadlineReminder(
            id_hash="h", titulo="Conv", url="https://e/x",
            deadline_inscripcion="2026-06-20", days_left=7,
            deadline_estimated=True,
        )
        joined = "\n".join(_format_reminder(rem))
        assert "(estimada)" in joined

    def test_reminder_sin_estimada(self):
        rem = DeadlineReminder(
            id_hash="h", titulo="Conv", url="https://e/x",
            deadline_inscripcion="2026-06-20", days_left=7,
            deadline_estimated=False,
        )
        joined = "\n".join(_format_reminder(rem))
        assert "estimada" not in joined
