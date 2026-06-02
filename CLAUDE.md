# CLAUDE.md — vigia-core (maestro)

Reglas operativas del **núcleo** de la plataforma vigia y de **cualquier bot**
construido sobre él. Es el documento canónico: los repos finos (`vigia-enfermeria`,
`vigia-docencia`, …) tienen su propio `CLAUDE.md` con lo específico de su perfil y
**enlazan aquí** para lo genérico. Tres bloques:

1. **Karpathy Guidelines** — comportamiento general para reducir errores típicos de
   un LLM al programar. Adaptado de [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) (MIT). Genérico, aplica a cualquier proyecto.
2. **Convenciones del pipeline vigia** — gotchas operativos del pipeline
   (fetch → extract → enrich → notify), comunes a todos los bots. Aprendidos en producción.
3. **Cómo crear un nuevo bot/perfil** — la receta para montar un bot fino sobre el core.

**Compromiso:** estas reglas priman cautela sobre velocidad. Para tareas triviales, usa el sentido común.

---

## Parte 1 — Karpathy Guidelines (adaptado, MIT)

### 1. Pensar antes de programar

**No asumas. No ocultes confusión. Saca a la luz los compromisos.**

Antes de implementar:
- Enuncia tus supuestos. Si dudas, pregunta.
- Si hay varias interpretaciones posibles, preséntalas — no elijas en silencio.
- Si existe una alternativa más simple, dilo. Empuja cuando esté justificado.
- Si algo no está claro, para. Nombra lo que te confunde. Pregunta.

### 2. Simplicidad primero

**El mínimo código que resuelve el problema. Nada especulativo.**

- Ningún feature más allá de lo pedido.
- Sin abstracciones para código de un solo uso.
- Sin "flexibilidad" o "configurabilidad" que no se haya pedido.
- Sin manejo de errores para escenarios imposibles.
- Si escribes 200 líneas y podían ser 50, reescríbelo.

Pregúntate: "¿Un ingeniero senior diría que esto está sobrecomplicado?". Si sí, simplifica.

### 3. Cambios quirúrgicos

**Toca solo lo que debas. Limpia solo tu propio desorden.**

Al editar código existente:
- No "mejores" código adyacente, comentarios o formato.
- No refactorices lo que no está roto.
- Imita el estilo existente, aunque tú lo harías de otra manera.
- Si ves código muerto no relacionado, menciónalo — no lo borres.

Cuando tus cambios crean huérfanos:
- Elimina imports/variables/funciones que TUS cambios dejaron sin usar.
- No elimines código muerto preexistente salvo que se pida.

*test:* cada línea modificada debe trazar directamente a la petición del usuario.

### 4. Ejecución guiada por objetivo

**Define criterios de éxito. Itera hasta verificar.**

Transforma tareas en metas verificables:
- "Añadir validación" → "Escribe tests para inputs inválidos y haz que pasen".
- "Arregla el bug" → "Escribe un test que lo reproduzca y haz que pase".
- "Refactoriza X" → "Asegura que los tests pasan antes y después".

Para tareas multipaso, enuncia un plan breve:
```
1. [Paso] → verifica: [check]
2. [Paso] → verifica: [check]
3. [Paso] → verifica: [check]
```

Criterios fuertes te permiten iterar sin supervisión. Criterios débiles ("haz que funcione") obligan a aclarar todo el rato.

---

## Parte 2 — Convenciones del pipeline vigia

Comunes a todos los bots. Ordenadas por frecuencia de tropiezo en sesiones reales.
Los ejemplos concretos provienen del bot original (enfermería); el principio aplica
a cualquier perfil.

### 5. El estado vive en GitHub, no en disco

**El `seen.db` local casi nunca refleja producción.** Cada bot persiste su estado
SQLite en su **rama `state`** y el dashboard en su **rama `gh-pages`**, vía GitHub
Actions. El directorio local de estado lo fija `VIGIA_STATE_DIR`.

- Para diagnosticar: `git fetch origin state` y luego `git show FETCH_HEAD:state/seen.db > /tmp/prod.db`.
- Para ver el dashboard real: `git show origin/gh-pages:data/items.json`.
- No pushees `state/` local a la rama `state` ni edites la BD local sin restaurarla primero.

*test:* antes de afirmar "el item está/no está en BD", confirma contra la rama remota, nunca contra disco.

### 6. Verifica el daño real antes de proponer arreglo

**Un warning en logs no implica BD contaminada.**

- El parser puede emitir un `RawItem` que el extractor descarte aguas abajo (un
  "fallback a `today()`" ruidoso puede acabar en 0 daño si esos items eran falsos
  positivos descartados después).
- El `conclusion: success` del workflow puede esconder errores acumulados en
  `last_errors` por fuente.

*test:* localiza el `id_hash` del ítem sospechoso en `data/items.json`. Si no está, el daño es solo log noise.

### 7. Segmenta backfills

**`since` con rango grande revienta el runner de Actions.**

- Un `since` de semanas/meses puede exceder el límite de tiempo del runner y
  abortarse: boletines con paginación completa (`max_pages=None`) × 100+ días = miles
  de PDFs grandes; el BOE = miles de items con bodies + anexos.
- `dry_run=true` **no acorta** el pipeline (sigue fetchando todo). Solo evita persistencia y Telegram.
- Para histórico amplio: rangos mensuales (`since=2025-12-01`, luego `2026-01-01`…) o ejecución local.

*test:* si `since` es >30 días, divide en lotes mensuales o no lances el `daily.yml`.

### 8. Si lo cambias en una fuente, busca en las hermanas

**Los patrones se repiten en todas las fuentes; los fixes también.**

- Timeouts, `fast_keywords`, cascadas de fecha con fallback a `today()`,
  `FALSE_POSITIVE_PATTERNS` — viven duplicados en varias fuentes
  (`boe.py / bocm.py / comunidad_madrid.py / ciemat.py / universidades_madrid.py / sap_successfactors.py`).
- Subir el timeout en una fuente y dejar la hermana atrás reproduce el mismo síntoma
  en la otra; crear un helper de fechas para una y no para su gemela deja el bug vivo.

*test:* al cerrar un fix de una fuente, lanza `grep -nE "timeout=|fallback a today\(\)" vigia/sources/*.py` para localizar gemelos.

### 9. Probe ≠ runtime

**Una fuente puede dar `probe 200 OK` y aun así perder items por timeouts en GETs concretos.**

- El dashboard refleja solo el resultado del probe. La degradación silenciosa
  (timeouts en items individuales, listados perdidos por término) queda solo en logs del workflow.
- Síntoma típico: `<fuente> 2 raw items, 1 errores` con probe verde — el "1 errores" es la rama perdida.

*test:* después de un fix, lee `gh run view <id> --log | grep -E "WARNING|errores"`, no solo el `conclusion: success`.

---

## Parte 3 — Cómo crear un nuevo bot/perfil

El núcleo es **agnóstico al perfil**. Un bot nuevo = un repo fino que instala
`vigia-core` por pip, define su `Profile` y aporta solo sus fuentes propias. El
pipeline (extractor, enricher, notifier, dashboard, watchers y las fuentes
genéricas) se reutiliza entero. Referencia viva: el repo `vigia-docencia`.

### 3.1 El contrato `Profile`

`@dataclass(frozen=True)` en `vigia/profile.py`. Encapsula **todo** lo específico de
un perfil. El core lo lee en tiempo de llamada con `get_active_profile()`:

| Grupo | Campos |
|---|---|
| Identidad / branding | `slug`, `display_name`, `dashboard_url`, `test_message` |
| Matching (extractor) | `strong_patterns`, `weak_context_patterns`, `false_positive_patterns`, `fast_keywords`, `category_hints` |
| Watchlist (dashboard) | `watchlist_orgs`, `watchlist_recency_days` |
| Enricher / diff (LLM) | `enricher_system_prompt`, `enricher_snippet_keywords_high/low`, `enricher_allowed_fetch_hosts`, `diff_system_prompt` |
| Fuentes | `sources_enabled`, `extra_sources`, `source_params` |
| Sanitización LLM | `valid_process_types` (default = 6 genéricos; cada bot puede ampliarlos) |

Se quedan en el core (genéricos, no son del perfil): `normalize()`, esquema SQLite,
credenciales Telegram, `USER_AGENT`, fases de proceso.

### 3.2 El modelo "un proceso = un bot = un perfil"

El extractor y el enricher compilan sus patrones/enums **en import-time** leyendo el
perfil activo. Por eso el bot debe fijar su perfil **antes** de importar el pipeline.
El entrypoint canónico (`vigia_<bot>/__main__.py`):

```python
from vigia.profile import set_active_profile
from vigia_<bot>.profile import PERFIL_<BOT>

set_active_profile(PERFIL_<BOT>)        # 1) ANTES de tocar el pipeline

def main() -> None:
    from vigia.main import main as _core_main   # 2) import diferido
    _core_main()
```

Si nadie fija perfil, el core carga de forma perezosa el de Enfermería del Trabajo
(`vigia/_default_profile.py`), de modo que el bot histórico sigue igual. Ese módulo
es el **ejemplo completo** de cómo se rellena un `Profile`.

### 3.3 Estructura de un repo fino

```
vigia_<bot>/
  profile.py      PERFIL_<BOT> = Profile(...)   (keywords/prompts/watchlist/branding)
  __main__.py     entrypoint: set_active_profile + import diferido
  sources/        fuentes propias del perfil (clase Source registrada en extra_sources)
requirements.txt  vigia-core @ git+https://github.com/tragabytes/vigia-core.git@vX.Y.Z
.github/workflows/daily.yml   cron + VIGIA_STATE_DIR + `python -m vigia_<bot>`
web/              dashboard (frontend agnóstico; rebrand por meta.json)
tests/            tests del bot (offline)
```

- **Fuente custom:** una clase `Source` en `vigia_<bot>/sources/`, registrada en
  `Profile.extra_sources={"<id>": MiFuente}`. Si el id coincide con una fuente del
  core (p.ej. `bocm`), la **sobrescribe** para ese bot.
- **Parametrizar una fuente del core** (en vez de reescribirla): pásale overrides por
  `Profile.source_params={"boe": {...}}`. Los defaults equivalen al perfil enfermería.
- **Estado aislado:** cada bot fija `VIGIA_STATE_DIR` para que su `seen.db` viva en su
  propio directorio/rama `state`. Nunca comparten estado.
- **Secrets (3):** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ANTHROPIC_API_KEY` (esta
  activa el enricher; sin ella el bot corre sin enriquecer).

### 3.4 ¿Fuente al core o al bot?

- **Genérica** (un boletín autonómico, un portal que sirve a varios perfiles) → **al core**
  (`vigia/sources/` + `CORE_SOURCES` en `registry.py`): beneficia a todos los bots.
- **De perfil** (portal de un nicho concreto) → **al repo del bot**, vía `extra_sources`.

### 3.5 Cutover: sustituir a un bot anterior

Si el bot nuevo reemplaza a uno ya desplegado, **migra el estado** para no re-alertar
de lo ya visto (lección de la Fase 4):

1. Copia el `seen.db` del bot viejo a la rama `state` del nuevo.
2. Primer run real esperando **0 re-alertas** (los matches existentes → 0 nuevos).
3. Verifica Telegram con `send_test` (workflow de ping manual).
4. Apaga el cron del bot viejo (y archiva su repo) — si comparten bot/chat, no hay duplicados.

### 3.6 Tocar el core: contratos que NO se rompen

Cambios al core = **aditivos** y con la suite verde (**472 passed, 2 skipped**) sin tocar
los tests existentes. Fijados por los tests:

- `extract(raw)` mantiene su firma (regex cacheada por perfil; se recompila al cambiar de perfil).
- `vigia.main.SOURCE_REGISTRY` y `vigia.main.SOURCES_ENABLED` siguen siendo **atributos de módulo** (varios tests los monkeypatchean).
- `normalize` sigue importable desde `vigia.config`.

### 3.7 Mantenimiento / publicación del core

`vigia-core` se publica **por copia manual** (snapshot, sin script de sync). Al tocar el core:

1. Commit en el repo del core + **nuevo tag** `vX.Y.Z` (semver; aditivo = minor).
2. **Bumpea** el `requirements.txt` de cada bot al nuevo tag.
3. Re-verifica el CI de cada bot (instala el tag, tests, dry-run real).

---

## Gotchas de entorno

- **Python 3.9** (`requires-python = ">=3.9"`): el código debe ser 3.9-compatible —
  nada de `X | Y` en runtime; usa `from __future__ import annotations`.
- **Windows:** `--probe`/`--dry-run` revientan con `UnicodeEncodeError` (cp1252) al
  imprimir `→`; exporta `PYTHONIOENCODING=utf-8` para esas verificaciones.
- **pytest:** en shells que rompen la captura por descriptores de fichero, usa
  `python -m pytest tests --capture=no`.

---

**Estas reglas funcionan si:** menos cambios innecesarios en los diffs, menos
rebobinados por sobrecomplicación, y las preguntas aclaratorias llegan antes de
implementar — no después de un error.
