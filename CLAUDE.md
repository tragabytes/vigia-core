# CLAUDE.md — vigia-core

Núcleo de **vigia**: vigila cada día boletines y portales de empleo público (buscar → filtrar → enriquecer con IA → avisar por Telegram) y publica un dashboard. No sabe de perfiles: cada bot es un repo fino que instala este núcleo por etiqueta y pone su perfil y sus fuentes propias. Hoy hay dos bots: **vigia-enfermeria** (Enfermería del Trabajo en Madrid) y **vigia-docencia**.

| Fichero | Para qué |
|---|---|
| [`RELEVO.md`](RELEVO.md) | Estado y por dónde seguir. **Punto de entrada** de cada sesión |
| [`DECISIONES.md`](DECISIONES.md) | Lo que Claude decidió sin Laureano: qué, por qué y cómo se deshace |
| [`specs/`](specs/) | Una carpeta por cada cosa nueva, con `spec.md` (qué y por qué) y `tasks.md` (estado) |
| [`MANTENIMIENTO.md`](MANTENIMIENTO.md) | Paso a paso: pasar la suite, ver producción, leer un run, backfill, publicar el núcleo, crear un bot, cutover |
| [`vigia/profile.py`](vigia/profile.py) · [`vigia/_default_profile.py`](vigia/_default_profile.py) | El contrato `Profile` y el perfil de ejemplo completo (enfermería) |

Los bots enlazan a este fichero como «maestro» y citan «§3.6-3.7» o «Parte 3»: eso está ahora en `MANTENIMIENTO.md` (apartados 5 y 6) y en la regla 6 de aquí.

## Reglas propias

Cicatrices del pipeline, aprendidas en producción. Cada una dice cómo comprobarla.

1. **El estado vive en GitHub, no en disco.** La base de datos de cada bot está en su rama `state` y el dashboard en `gh-pages`; el `seen.db` local casi nunca es producción. *Comprobación*: antes de afirmar que un item está o no está, mirar la rama remota (`MANTENIMIENTO.md` §2).
2. **Mirar el daño real antes de arreglar.** Un aviso en el log no significa base de datos contaminada: el extractor puede descartar el item después. *Comprobación*: buscar su `id_hash` en `data/items.json`; si no está, es ruido.
3. **Backfills por meses.** Un `since` de más de 30 días revienta el runner de Actions, y `dry_run` no lo acorta (`MANTENIMIENTO.md` §4).
4. **Si lo arreglas en una fuente, búscalo en las hermanas.** Timeouts, `fast_keywords`, fechas con recurso a `today()` y `FALSE_POSITIVE_PATTERNS` están repetidos en varias fuentes. *Comprobación*: `grep -nE "timeout=|fallback a today\(\)" vigia/sources/*.py`.
5. **Probe ≠ runtime.** Un «200 OK» del probe no quita que se pierdan items por timeouts sueltos; `success` puede esconder errores. *Comprobación*: leer el log del run, no solo el resultado (`MANTENIMIENTO.md` §3).
6. **Los cambios al núcleo son aditivos y no rompen a los bots.** Suite en verde sin tocar los tests existentes. Contratos fijados por tests: `extract(raw)` mantiene su firma; `vigia.main.SOURCE_REGISTRY` y `vigia.main.SOURCES_ENABLED` siguen siendo atributos de módulo; `normalize` se importa desde `vigia.config`. Los bots **nunca copian tests del núcleo**: se desincronizan y rompen cada subida de versión (lección del PR #30 de vigia-enfermeria).
7. **Un proceso, un perfil.** El perfil se fija con `set_active_profile()` **antes** de importar el pipeline, porque los patrones se compilan al importar (`MANTENIMIENTO.md` §6).
8. **Python 3.9.** Nada de `X | Y` en tiempo de ejecución.
