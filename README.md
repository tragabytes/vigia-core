# vigia-core

Núcleo reutilizable de **vigia**: un pipeline de vigilancia de ofertas de empleo
(fetch → extract → enrich → notify) sobre el que se construyen bots de Telegram,
uno por perfil profesional.

El núcleo es agnóstico al perfil. Las keywords de matching, los prompts del LLM,
la watchlist de organismos, el branding y las fuentes propias viven en un
`Profile` (`vigia/profile.py`). Cada bot fija su perfil al arranque con
`set_active_profile(...)` y reutiliza todo el pipeline.

## Uso

    from vigia.profile import set_active_profile
    from mi_bot.profile import MI_PERFIL

    set_active_profile(MI_PERFIL)   # ANTES de importar el resto del pipeline
    from vigia.main import main
    main()

## Instalación

    pip install git+https://github.com/tragabytes/vigia-core.git@v0.4.4

Requiere Python >= 3.9. Cada bot debe fijar `VIGIA_STATE_DIR` para que la BD de
estado (`seen.db`) viva en su propio directorio/rama `state`.

## Perfil de referencia

`vigia/_default_profile.py` contiene el perfil completo de **Enfermería del
Trabajo** (el bot original), útil como ejemplo de cómo se define un `Profile`.

## Estado

Extraído de `vigia-enfermeria` el 2026-06-02. Suite del core: 472 passed, 2 skipped.
