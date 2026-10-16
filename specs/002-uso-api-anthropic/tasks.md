# Tareas — 002 Uso de la API de Anthropic

Spec: [`spec.md`](spec.md). Aprobada por Laureano el 16/10/2026, con el gasto de la comparación.

## H1 · Medir y no quedarse sin servicio
- [x] Registrar en el log los tokens de cada llamada (enricher y resumidor) y el total del run — v0.15.0
- [x] Caché de prompts en el enricher (comprobar `cache_read_input_tokens` > 0 en el log) — v0.15.0
- [x] Reintentar en el siguiente run las convocatorias sin resumir (incluidas las 16 de septiembre) — v0.15.0
- [ ] **Laureano**: espacio de trabajo y clave propios para vigia, con límite y aviso por email
- [ ] **Parar y validar**: gasto real de una semana

## H2 · Elegir el modelo con datos
- [x] Banco de prueba de ~40 convocatorias reales con la respuesta correcta — 39 casos en `evals/enricher/casos.json`, etiquetados con sus criterios (pendiente que Laureano revise las etiquetas dudosas)
- [x] Correr Sonnet 4.6, Sonnet 5.5 y Haiku 5.5 — tres rondas, ~3,4 $
- [x] Tabla de resultados: [`resultados.md`](resultados.md)
- [ ] **Laureano**: decidir modelo y casos en disputa
- [ ] Si se cambia: migración (pensamiento, `fallbacks`, salidas estructuradas), simulación con copia de la base, nueva versión del núcleo

## H3 · Agente de salud
- [x] Sonnet 5 → Sonnet 5.5 — PR #54
- [x] Copia del agente en vigia-docencia para sus fuentes propias — docencia PR #45
- [x] Que lea también el log del último daily — PR #54; su informe sale en la página del run (`display_report`, PR #56 y docencia #47)

## H4 · Re-enriquecidos por lotes
- [ ] `enrich_pending` por la API de Batch cuando cambie `ENRICHMENT_VERSION`

## Cierre
- [ ] Tests de lo que pueda romperse en silencio (un fallo de la API no deja convocatorias sin resumir; el filtro de dominios sigue)
- [ ] Suite en verde; primer daily vigilado; `RELEVO.md` al día
