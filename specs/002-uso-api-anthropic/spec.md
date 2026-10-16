# Especificación: revisar el uso de la API de Anthropic

**Carpeta**: `specs/002-uso-api-anthropic/` · **Fecha**: 2026-10-16 · **Estado**: borrador, para decidir

**Lo que se pidió** (Laureano, 16/10/2026): «el uso de la api lo configuramos hace meses, no sé si hay novedades que merezca la pena evaluar (nuevos modelos, orquestación, etc...)» y «tenemos un agente automático que revisa errores no? Lo revisamos también para ver si hay mejores modelos o sistemas de orquestación».

## Qué hay hoy (comprobado en el código y en las bases de datos el 16/10)

| Pieza | Para qué | Modelo | Cómo trabaja |
|---|---|---|---|
| **Enricher** (los dos bots) | Resume cada convocatoria nueva y decide si es relevante (`is_relevant`). **Si dice «no», el aviso no llega a Telegram** | Sonnet 4.6 | Bucle propio con una herramienta `fetch_url` (abre el BOE, el BOCM, PDF…), hasta 4 vueltas por convocatoria. Sin caché, sin pensamiento, el JSON se extrae del texto. **No registra cuántos tokens gasta** |
| **Resumidor de cambios** | Cuando una página vigilada cambia, decide si es un cambio de fondo o cosmético | Sonnet 4.6 | Una llamada corta (256 tokens de respuesta) |
| **Agente semanal de salud** (núcleo) | Los lunes lee el probe de los dos bots y, si una fuente del núcleo está rota, la arregla y abre un PR | Sonnet 5, en claude-code-action | Hasta 80 pasos; ~0,75 $ por run |

**Volumen**: entre los dos bots, 60-100 convocatorias enriquecidas al mes; con las fuentes nuevas de docencia, unas 100 más. Cada vez que se cambia el prompt (`ENRICHMENT_VERSION`), se re-enriquece el histórico (~430 hoy).

**Coste estimado** (no medido: no hay registro de tokens ni clave en local): 2-13 céntimos por convocatoria según cuántos documentos abra, **~6-12 $ al mes** más **~25-30 $ por cada re-enriquecido**; el agente de salud, ~3 $ al mes.

**Lo que falló**: del 22 al 29/09 se agotó el **límite de gasto** configurado en la cuenta («You have reached your specified API usage limits»). Ese límite es de toda la cuenta o del espacio de trabajo: si otros proyectos usan la misma, también gastan de él. Consecuencias: el enricher no resumió nada esa semana (15 convocatorias de docencia y 1 de enfermería siguen sin resumir; sin un «no relevante», probablemente llegaron a Telegram sin filtrar), y el agente de salud falló dos lunes.

## Qué ha cambiado desde que se configuró

| Modelo | Precio (entrada / salida, por millón de tokens) | Para el bot |
|---|---|---|
| Sonnet 4.6 (el de hoy) | 3 $ / 15 $ | — |
| **Sonnet 5.5** (el Sonnet actual) | **2 $ / 10 $** (un tercio menos) | Mejor y más barato. Piensa por defecto: para extraer datos se usa con esfuerzo `low` |
| **Haiku 5.5** | **0,10 $ / 0,50 $** (~30 veces menos) | Muy barato; para extracción puede bastar, pero **hay que medirlo**: un «no relevante» de más hace perder una convocatoria en silencio |
| Opus 5.5 | 4 $ / 20 $ | Más capaz; no hace falta para resumir convocatorias |

Además, ahora hay herramientas que el bot no usa:
- **Caché de prompts**: el prompt de sistema (~1.700 tokens) y la conversación que se reenvía en cada vuelta del bucle se cobrarían al 10 % al repetirse. Ahorro estimado: 20-40 % de la entrada.
- **Salidas estructuradas**: el modelo devuelve el JSON garantizado, en vez de buscarlo en el texto.
- **Batch**: 50 % más barato, pero asíncrono (minutos u horas). No sirve para el daily (retrasaría los avisos); sí para re-enriquecer el histórico.
- **Fallback por rechazo**: si el modelo declina una petición, se repite sola con otro modelo.

## Historias

### H1 — Saber cuánto se gasta y no volver a quedarse sin servicio (P1)

- El enricher y el resumidor **apuntan en el log los tokens de cada llamada** y el total del día. Así se mide el gasto real sin pagar nada extra.
- **Caché de prompts** en el enricher.
- Las convocatorias que no se pudieron resumir **se reintentan** en el siguiente run (hoy se quedan sin resumir para siempre en docencia).
- **Tarea tuya**: un espacio de trabajo y una clave propios para vigia en la consola de Anthropic, con su límite de gasto y aviso por email al acercarse.

**Criterios**: el log de cada daily dice cuántos tokens se gastaron; un fallo de la API un día no deja convocatorias sin resumir al siguiente.

### H2 — Elegir el modelo con datos (P1)

Un banco de prueba pequeño (~40 convocatorias reales de las bases de los dos bots, incluidas las 25 de la H1 de docencia, con la respuesta correcta de «relevante sí/no») para comparar **Sonnet 4.6** (hoy), **Sonnet 5.5 con esfuerzo bajo** y **Haiku 5.5**. Se mira, por este orden: cuántas relevantes marca como «no» (lo grave), cuántas irrelevantes marca como «sí» (ruido), los campos (plazo, plazas) y el coste.

**Criterios**: una tabla con los tres modelos; se cambia solo si el nuevo no pierde ninguna relevante que el actual acierte. **Coste de la prueba**: ~2-5 $.

### H3 — El agente de salud, al día y cubriendo docencia (P2)

- Pasar de Sonnet 5 a **Sonnet 5.5** (mismo precio, más capaz en tareas de código con herramientas).
- **Hueco nuevo**: 6 de las 10 fuentes nuevas viven en el repo de docencia, y el agente solo puede arreglar el núcleo. Propuesta: una copia del agente en vigia-docencia, limitada a sus fuentes propias.
- Que lea también el log del último daily, no solo el probe (regla 5: un probe en verde puede esconder errores).

### H4 — Re-enriquecidos por lotes (P3)

Cuando cambie el prompt, re-enriquecer el histórico con la **API de Batch** (mitad de precio).

## Lo que no propongo (y por qué)

- **Managed Agents** (agentes alojados por Anthropic con horario propio) para el agente de salud: hoy funciona con GitHub Actions, que ya tiene el repo, los tests y los permisos para abrir PR. Moverlo obligaría a montar credenciales de GitHub fuera y no aporta nada medible.
- **Cambiar el bucle del enricher por la herramienta `web_fetch` de Anthropic**: quitaría código, pero el bucle actual funciona, filtra dominios oficiales y extrae PDF del BOE. Sin ganancia clara.
- **Opus para el enricher**: más caro y no hace falta para esta tarea.

## Qué invariantes toca

| Invariante | Dónde está escrito | ¿Puede romperse en silencio? |
|---|---|---|
| Un «no relevante» del enricher oculta el aviso | `vigia/main.py` (notifier) | **Sí, el más peligroso**: un modelo más barato que diga «no» de más hace perder convocatorias sin que nadie lo vea. Por eso H2 mide primero los falsos «no» |
| Cambios al núcleo aditivos y con la suite en verde | regla 6 del núcleo | No |
| Los errores de fuente no llegan al Telegram | núcleo | No |
| El enricher no abre dominios fuera de la lista blanca | `fetch_url`, perfil | Sí, si se cambiase a `web_fetch` sin `allowed_domains`: por eso no se propone |

## Criterios de éxito

- **E-001**: el gasto real por convocatoria y por mes se lee en los logs.
- **E-002**: cero convocatorias sin resumir más de un día.
- **E-003**: si se cambia de modelo, el banco de prueba no pierde ninguna relevante y el coste baja.

## Supuestos

- El límite de gasto lo gestiona Laureano en la consola de Anthropic (Claude no toca ajustes de cuenta).
- La prueba de H2 se paga con la clave de vigia y se lanza desde GitHub Actions o con una clave que Laureano dé (en local no hay).
- Docencia y enfermería usan el mismo modelo del núcleo; si en la prueba uno de los dos perfiles sale peor con un modelo, se puede elegir modelo por perfil.
