"""
Perfil profesional de un bot vigia.

Un `Profile` encapsula TODO lo específico de un perfil: keywords de
matching, prompts del LLM, watchlist de organismos, fuentes propias y
branding. El núcleo (`vigia`) es agnóstico y lee el perfil activo en
tiempo de llamada mediante `get_active_profile()`.

Modelo de uso: **un proceso = un bot = un perfil**, fijado al arranque con
`set_active_profile(...)` antes de importar el resto del pipeline. Si nadie
lo fija, se usa el perfil por defecto (Enfermería del Trabajo) de
`vigia._default_profile`, de modo que el bot histórico sigue funcionando
exactamente igual sin cambios.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Profile:
    # --- Identidad / branding ---
    slug: str
    display_name: str
    dashboard_url: str
    test_message: str

    # --- Matching (extractor) ---
    strong_patterns: tuple[str, ...]
    weak_context_patterns: tuple[tuple[str, str], ...]
    false_positive_patterns: tuple[str, ...]
    fast_keywords: tuple[str, ...]
    category_hints: dict

    # --- Watchlist (dashboard) ---
    watchlist_orgs: tuple[dict, ...]
    watchlist_recency_days: int

    # --- Enricher / diff (LLM) ---
    enricher_system_prompt: str
    enricher_snippet_keywords_high: tuple[str, ...]
    enricher_snippet_keywords_low: tuple[str, ...]
    enricher_allowed_fetch_hosts: frozenset
    diff_system_prompt: str

    # --- Fuentes ---
    sources_enabled: tuple[str, ...]
    extra_sources: dict = field(default_factory=dict)
    source_params: dict = field(default_factory=dict)

    # --- Enricher: enums de process_type válidos (sanitización del LLM) ---
    # Cada bot puede ampliarlos (p.ej. docencia añade lectorado/auxiliar/privada/
    # ele); el default genérico cubre el perfil enfermería sin cambios.
    valid_process_types: tuple[str, ...] = (
        "oposicion", "bolsa", "concurso_traslados", "interinaje", "temporal", "otro",
    )

    # --- Recordatorios de cierre de plazo ---
    # Días antes del cierre en los que se re-avisa de una convocatoria abierta
    # (un único aviso por umbral). Vacío = desactiva los recordatorios.
    deadline_reminder_days: tuple[int, ...] = (7, 3, 1)

    # --- Enricher: anclas de snippet para la sección de PLAZO ---
    # Términos genéricos de convocatoria pública española alrededor de los
    # cuales el enricher inyecta una ventana de texto, para que la fecha/plazo
    # de cierre llegue al prompt aunque viva lejos de las keywords de la
    # especialidad. Default genérico (sirve a cualquier perfil); un bot puede
    # sobrescribirlo si lo necesita.
    enricher_snippet_keywords_deadline: tuple[str, ...] = (
        "plazo de presentación", "plazo de presentacion",
        "plazo de inscripción", "plazo de inscripcion",
        "presentación de solicitudes", "presentacion de solicitudes",
        "presentación de instancias", "presentacion de instancias",
        "fecha límite", "fecha limite",
        "hasta el día", "hasta el dia",
        "días hábiles", "dias habiles",
        "días naturales", "dias naturales",
        "a partir del día siguiente", "a partir del dia siguiente",
        "siguiente al de la publicación", "siguiente al de la publicacion",
    )


# ---------------------------------------------------------------------------
# Registro del perfil activo (un perfil por proceso)
# ---------------------------------------------------------------------------
_active_profile = None


def set_active_profile(profile):
    """Fija el perfil activo del proceso.

    Llamar al arranque del bot, ANTES de importar el pipeline: el extractor
    y las fuentes leen los símbolos del perfil (vía la fachada de
    `vigia.config`) en import-time.
    """
    global _active_profile
    _active_profile = profile


def get_active_profile():
    """Devuelve el perfil activo. Si no se ha fijado ninguno, carga de forma
    perezosa el perfil por defecto (Enfermería del Trabajo)."""
    global _active_profile
    if _active_profile is None:
        from vigia._default_profile import DEFAULT
        _active_profile = DEFAULT
    return _active_profile
