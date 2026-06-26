"""
Tests de los recordatorios de cierre de plazo (Incremento 2) y del surface
de campos accionables del enricher en el notifier (Incremento 1).

Cubre:
  - Storage: query de deadlines abiertos + control idempotente de envíos.
  - Notifier: formato del bloque "Cierran pronto" y de los campos nuevos
    (requisitos_clave, url_inscripcion) en el bloque de item.
  - main(): lógica de umbrales (7/3/1) + idempotencia entre runs.
"""
from __future__ import annotations

from datetime import date, timedelta

from vigia.notifier import _build_message, _format_item, _format_reminder
from vigia.sources.base import RawItem, Source
from vigia.storage import DeadlineReminder, Item, Storage


def _seed(storage, *, url, titulo, deadline, is_relevant=1, source="boe",
          organismo=None, url_inscripcion=None):
    """Inserta un item con deadline e is_relevant (source=boe por defecto:
    excluido del DetailWatcher, así los tests de main() no hacen red)."""
    item = Item(
        source=source, url=url, titulo=titulo,
        fecha=date(2026, 1, 1), categoria="oposicion",
        organismo=organismo, url_inscripcion=url_inscripcion,
    )
    storage.save(item)
    storage._conn.execute(
        "UPDATE items SET deadline_inscripcion = ?, is_relevant = ?, "
        "organismo = ?, url_inscripcion = ? WHERE id_hash = ?",
        (deadline, is_relevant, organismo, url_inscripcion, item.id_hash),
    )
    storage._conn.commit()
    return item


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

class TestStorageDeadlines:
    def test_iter_solo_deadlines_futuros_y_relevantes(self, tmp_path):
        s = Storage(db_path=tmp_path / "seen.db")
        today = date(2026, 6, 13)
        _seed(s, url="https://e/abierta", titulo="Abierta",
              deadline=(today + timedelta(days=3)).isoformat())
        _seed(s, url="https://e/cerrada", titulo="Cerrada",
              deadline=(today - timedelta(days=1)).isoformat())
        _seed(s, url="https://e/fp", titulo="FP", is_relevant=0,
              deadline=(today + timedelta(days=2)).isoformat())
        _seed(s, url="https://e/sin", titulo="Sin deadline", deadline=None)
        rows = s.iter_items_with_open_deadline(today)
        s.close()
        titulos = [r.titulo for r in rows]
        assert titulos == ["Abierta"]
        assert isinstance(rows[0], DeadlineReminder)

    def test_relevante_null_se_incluye(self, tmp_path):
        s = Storage(db_path=tmp_path / "seen.db")
        today = date(2026, 6, 13)
        _seed(s, url="https://e/x", titulo="Sin clasificar",
              is_relevant=None, deadline=(today + timedelta(days=5)).isoformat())
        rows = s.iter_items_with_open_deadline(today)
        s.close()
        assert [r.titulo for r in rows] == ["Sin clasificar"]

    def test_mark_y_get_thresholds_idempotente(self, tmp_path):
        s = Storage(db_path=tmp_path / "seen.db")
        assert s.get_sent_reminder_thresholds("abc") == set()
        s.mark_reminder_sent("abc", 7, "2026-06-13T08:00:00")
        s.mark_reminder_sent("abc", 3, "2026-06-13T08:00:00")
        # Re-marcar el mismo umbral no duplica ni falla (INSERT OR IGNORE).
        s.mark_reminder_sent("abc", 7, "2026-06-14T08:00:00")
        got = s.get_sent_reminder_thresholds("abc")
        s.close()
        assert got == {3, 7}

    def test_thresholds_por_item_independientes(self, tmp_path):
        s = Storage(db_path=tmp_path / "seen.db")
        s.mark_reminder_sent("a", 7, "t")
        s.mark_reminder_sent("b", 1, "t")
        assert s.get_sent_reminder_thresholds("a") == {7}
        assert s.get_sent_reminder_thresholds("b") == {1}
        s.close()


# ---------------------------------------------------------------------------
# Notifier — formato del recordatorio
# ---------------------------------------------------------------------------

def _rem(**kw) -> DeadlineReminder:
    base = dict(
        id_hash="h", titulo="Bolsa Enfermería del Trabajo",
        url="https://e/anuncio", deadline_inscripcion="2026-06-20",
        days_left=3,
    )
    base.update(kw)
    return DeadlineReminder(**base)


class TestFormatReminder:
    def test_en_n_dias(self):
        block = _format_reminder(_rem(days_left=3))
        assert "Cierra en 3 días" in block[0]
        assert "Bolsa Enfermería del Trabajo" in block[1]
        assert any("06/2026" in b for b in block)

    def test_manana_y_hoy(self):
        assert "mañana" in _format_reminder(_rem(days_left=1))[0]
        assert "HOY" in _format_reminder(_rem(days_left=0))[0]

    def test_prefiere_url_inscripcion(self):
        block = _format_reminder(_rem(url_inscripcion="https://e/apuntate"))
        assert any("https://e/apuntate" in b for b in block)
        assert not any("https://e/anuncio" in b for b in block)

    def test_sin_inscripcion_cae_al_anuncio(self):
        block = _format_reminder(_rem(url_inscripcion=None))
        assert any("https://e/anuncio" in b for b in block)

    def test_organismo_en_cabecera(self):
        block = _format_reminder(_rem(organismo="SERMAS"))
        assert "SERMAS" in block[0]


# ---------------------------------------------------------------------------
# Notifier — _build_message con recordatorios
# ---------------------------------------------------------------------------

class TestBuildMessageReminders:
    def test_seccion_cierran_pronto_presente(self):
        msg = _build_message([], [], date(2026, 6, 13), [_rem()])
        assert "Cierran pronto" in msg
        assert "Bolsa Enfermería del Trabajo" in msg
        # Recordatorio-solo: no debe decir "Sin novedades hoy".
        assert "Sin novedades hoy" not in msg

    def test_sin_items_ni_recordatorios_dice_sin_novedades(self):
        msg = _build_message([], [("boe", "503")], date(2026, 6, 13), [])
        assert "Sin novedades hoy" in msg
        # Los errores de fuentes NO se renderizan al usuario, ni siquiera
        # cuando se construye un mensaje "sin novedades".
        assert "no respondió" not in msg
        assert "503" not in msg

    def test_errores_no_se_renderizan_con_novedades_reales(self):
        # Con una convocatoria real, el bloque de errores tampoco se cuela.
        msg = _build_message(
            [_item(titulo="Convocatoria visible")],
            [("boe", "503"), ("isciii", "500 Server Error")],
            date(2026, 6, 13),
            [],
        )
        assert "Convocatoria visible" in msg
        assert "no respondió" not in msg
        assert "Server Error" not in msg


# ---------------------------------------------------------------------------
# Notifier — Incremento 1: campos accionables en el bloque de item
# ---------------------------------------------------------------------------

def _item(**kw) -> Item:
    base = dict(
        source="boe", url="https://e/x", titulo="Oposición Enf. del Trabajo",
        fecha=date(2026, 6, 1), categoria="oposicion",
    )
    base.update(kw)
    return Item(**base)


class TestFormatItemAccionable:
    def test_requisitos_clave_se_muestran(self):
        item = _item(requisitos_clave=["Título especialista (vía EIR)", "2 años exp."])
        lines = _format_item(item, date(2026, 6, 13))
        joined = "\n".join(lines)
        assert "Requisitos:" in joined
        assert "vía EIR" in joined
        assert "2 años exp." in joined

    def test_url_inscripcion_se_muestra_si_difiere(self):
        item = _item(url_inscripcion="https://e/apuntate")
        joined = "\n".join(_format_item(item, date(2026, 6, 13)))
        assert "Inscripción: https://e/apuntate" in joined

    def test_url_inscripcion_oculta_si_igual_al_anuncio(self):
        item = _item(url_inscripcion="https://e/x")  # == url
        joined = "\n".join(_format_item(item, date(2026, 6, 13)))
        assert "Inscripción:" not in joined

    def test_requisitos_vacios_no_emiten_linea(self):
        joined = "\n".join(_format_item(_item(requisitos_clave=[]), date(2026, 6, 13)))
        assert "Requisitos:" not in joined


# ---------------------------------------------------------------------------
# main() — lógica de umbrales + idempotencia
# ---------------------------------------------------------------------------

class _SilentSource(Source):
    name = "silent"

    def fetch(self, since_date):
        return []


class TestMainRecordatorios:
    def test_emite_umbral_correcto_y_es_idempotente(self, monkeypatch, tmp_path):
        from vigia import main as main_module
        from vigia import storage as storage_module

        monkeypatch.setattr(main_module, "SOURCE_REGISTRY", {"silent": _SilentSource})
        monkeypatch.setattr(main_module, "SOURCES_ENABLED", ["silent"])
        db = tmp_path / "seen.db"
        monkeypatch.setattr(storage_module, "DB_PATH", db)
        monkeypatch.setattr(main_module, "DASHBOARD_OUT_DIR", str(tmp_path / "dash"))

        today = date.today()
        s = Storage(db_path=db)
        _seed(s, url="https://e/3d", titulo="Cierra en 3",
              deadline=(today + timedelta(days=3)).isoformat())
        _seed(s, url="https://e/20d", titulo="Cierra en 20",
              deadline=(today + timedelta(days=20)).isoformat())  # > max umbral
        _seed(s, url="https://e/fp", titulo="FP en 2", is_relevant=0,
              deadline=(today + timedelta(days=2)).isoformat())
        _seed(s, url="https://e/old", titulo="Cerrada",
              deadline=(today - timedelta(days=1)).isoformat())
        s.close()

        cap = {}

        def fake_send(items, errors, run_date=None, reminders=None):
            cap["items"] = items
            cap["errors"] = errors
            cap["reminders"] = reminders

        monkeypatch.setattr(main_module, "send", fake_send)
        monkeypatch.setattr("sys.argv", ["main.py"])

        main_module.main()

        titulos = [r.titulo for r in (cap.get("reminders") or [])]
        assert titulos == ["Cierra en 3"]
        assert cap["reminders"][0].days_left == 3

        # Segunda corrida el mismo día: idempotente → 0 recordatorios, y como
        # no hay items ni errores, el notifier no se invoca.
        cap.clear()
        main_module.main()
        assert cap == {}
