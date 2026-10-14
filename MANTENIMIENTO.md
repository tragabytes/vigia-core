# Mantenimiento de vigia-core

Procedimientos paso a paso. Las reglas (el porqué) están en `CLAUDE.md`; aquí, el cómo.

## 1. Pasar la suite

```
PYTHONIOENCODING=utf-8 python -m pytest tests -q --capture=no
```

- Resultado esperado a v0.8.3: **547 passed, 2 skipped**.
- Sin `PYTHONIOENCODING=utf-8`, en Windows falla `test_probe.py::test_exit_code_1_si_alguna_fuente_falla`: la consola cp1252 no sabe escribir el `→`. Lo mismo les pasa a `--probe` y `--dry-run`.
- `--capture=no` hace falta en las consolas que rompen la captura de pytest.
- Si faltan dependencias (`No module named 'requests'`), instala el núcleo en un entorno aparte: `python -m venv <dir>` y `<dir>/Scripts/python -m pip install -e .`.
- El código tiene que funcionar en **Python 3.9**: nada de `X | Y` en tiempo de ejecución; `from __future__ import annotations`.

## 2. Ver el estado real de producción

El `seen.db` local casi nunca coincide con producción. Cada bot guarda su base de datos en su rama `state` y el dashboard en su rama `gh-pages`.

```
git fetch origin state
git show FETCH_HEAD:state/seen.db > <scratch>/prod.db
git show origin/gh-pages:data/items.json
```

(Estos comandos se lanzan en el repo del **bot**, no en el del núcleo.)

- No subas `state/` local a la rama `state` ni edites la base de datos local sin restaurarla antes.
- Para saber si un aviso de los logs hizo daño de verdad: busca el `id_hash` del item en `data/items.json`. Si no está, era solo ruido en el log.

## 3. Leer el log de un run

El `conclusion: success` no basta, y el «probe 200 OK» del dashboard tampoco: puede haber items perdidos por timeouts sueltos.

```
gh run list -R tragabytes/<bot> --workflow daily.yml -L 10
gh run view <id> -R tragabytes/<bot> --log | grep -E "WARNING|errores|DetailWatcher"
```

Síntoma típico de pérdida silenciosa: `<fuente> 2 raw items, 1 errores` con el probe en verde.

## 4. Backfill (recuperar un periodo pasado)

- Con `since` de más de 30 días, el run de Actions se pasa de tiempo y se aborta (boletines con paginación completa × 100+ días = miles de PDF; el BOE = miles de items con anexos).
- `dry_run=true` **no acorta** el run: sigue descargándolo todo; solo evita guardar y avisar por Telegram.
- Hazlo por meses (`since=2025-12-01`, luego `2026-01-01`, …) o en local.

## 5. Publicar una versión nueva del núcleo

El núcleo se publica **por etiqueta** (sin script de sincronización).

1. Cambios **aditivos** y con la suite en verde sin tocar los tests existentes.
2. En el mismo commit, subir `version` en `pyproject.toml` (va a la par de la etiqueta; aditivo = minor, arreglo = patch).
3. PR, fusionar, y etiqueta `vX.Y.Z` sobre `main`: `git tag vX.Y.Z && git push origin vX.Y.Z`.
4. En **cada bot**: cambiar la línea `vigia-core @ git+https://github.com/tragabytes/vigia-core@vX.Y.Z` de `requirements.txt`, PR y esperar su CI (instala la etiqueta, tests y un dry-run).
5. Comprobar en el primer daily real de cada bot lo que el arreglo prometía (apartado 3). El dry-run del CI arranca con la base de datos vacía, así que no prueba nada que dependa del estado.

## 6. Crear un bot nuevo

El núcleo no sabe de perfiles. Un bot nuevo es un repo fino que instala `vigia-core` por pip, define su `Profile` y aporta solo sus fuentes propias. Referencia viva: `vigia-docencia`.

### El `Profile`

`@dataclass(frozen=True)` en `vigia/profile.py`. El núcleo lo lee con `get_active_profile()`. Ejemplo completo: `vigia/_default_profile.py` (Enfermería del Trabajo, el que se carga si nadie fija otro).

| Grupo | Campos |
|---|---|
| Identidad | `slug`, `display_name`, `dashboard_url`, `test_message` |
| Matching (extractor) | `strong_patterns`, `weak_context_patterns`, `false_positive_patterns`, `fast_keywords`, `category_hints` |
| Watchlist (dashboard) | `watchlist_orgs`, `watchlist_recency_days` |
| Enricher / diff (LLM) | `enricher_system_prompt`, `enricher_snippet_keywords_high/low`, `enricher_allowed_fetch_hosts`, `diff_system_prompt` |
| Fuentes | `sources_enabled`, `extra_sources`, `source_params` |
| Saneado LLM | `valid_process_types` (6 genéricos por defecto; cada bot puede ampliarlos) |

Se quedan en el núcleo: `normalize()`, esquema SQLite, credenciales de Telegram, `USER_AGENT`, fases de proceso.

### El arranque (un proceso = un bot = un perfil)

El extractor y el enricher compilan sus patrones **al importarse**, leyendo el perfil activo. Por eso el perfil se fija **antes** de importar el pipeline:

```python
from vigia.profile import set_active_profile
from vigia_<bot>.profile import PERFIL_<BOT>

set_active_profile(PERFIL_<BOT>)        # 1) ANTES de tocar el pipeline

def main() -> None:
    from vigia.main import main as _core_main   # 2) import diferido
    _core_main()
```

### Estructura del repo

```
vigia_<bot>/
  profile.py      PERFIL_<BOT> = Profile(...)
  __main__.py     arranque de arriba
  sources/        fuentes propias (registradas en extra_sources)
requirements.txt  vigia-core @ git+https://github.com/tragabytes/vigia-core.git@vX.Y.Z
.github/workflows/daily.yml   cron + VIGIA_STATE_DIR + `python -m vigia_<bot>`
web/              dashboard (se rebrandea con meta.json)
tests/            solo tests del bot
```

- **Fuente propia**: clase `Source` en `vigia_<bot>/sources/`, registrada en `Profile.extra_sources={"<id>": MiFuente}`. Si el id coincide con una del núcleo (p. ej. `bocm`), la **sustituye** para ese bot.
- **Ajustar una fuente del núcleo** sin reescribirla: `Profile.source_params={"boe": {...}}`. Los valores por defecto son los de enfermería.
- **¿Al núcleo o al bot?** Genérica (un boletín autonómico, un portal que sirve a varios perfiles) → núcleo (`vigia/sources/` + `CORE_SOURCES` en `registry.py`). De un nicho concreto → bot.
- **Estado aislado**: cada bot fija `VIGIA_STATE_DIR`; nunca comparten `seen.db`.
- **Tests del bot**: solo su perfil y sus fuentes, por comportamiento (`extract()` → match / None / categoría), más un `conftest.py` que fija el perfil. **Nunca copiar tests del núcleo** (regla 6 de `CLAUDE.md`).
- **Secrets (3)**: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ANTHROPIC_API_KEY` (sin esta, el bot funciona sin enriquecer).

## 7. Sustituir un bot ya desplegado (cutover)

Para no volver a avisar de lo ya visto:

1. Copia el `seen.db` del bot viejo a la rama `state` del nuevo.
2. Primer run real esperando **0 avisos repetidos**.
3. Comprueba Telegram con `send_test` (workflow de ping manual).
4. Apaga el cron del bot viejo y archiva su repo.
