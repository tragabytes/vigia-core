# Resultados del banco de prueba (H2) — 16/10/2026

39 convocatorias reales (16 de enfermería y 23 de docencia), con la respuesta correcta puesta
por Claude según los criterios de Laureano. Tres rondas en la página de Actions
(`eval-enricher`), más una cuarta con los criterios nuevos. Gasto total: unos 4,3 $.

## Relevancia

| Ronda | Sonnet 4.6 (actual) | Sonnet 5.5 | Haiku 5.5 |
|---|---|---|---|
| 1 · como producción, esfuerzo bajo | 35/39 · 1 «no» de más | 34/39 · 4 «no» de más | 35/39 · 1 «no» de más |
| 2 · esfuerzo medio | — | 36/39 · 2 «no» de más | 35/39 · 1 «no» de más |
| 3 · con la página descargada de antemano | 33/39 · 3 «no» de más | 33/39 · 5 «no» de más | 33/39 · 3 «no» de más |
| 4 · con la página descargada y los prompts nuevos (Laureano, 16/10) | 36/39 · 1 «no» de más | — | **37/39 · 0 «no» de más** |
| **Coste por convocatoria** | **0,021 $** | 0,014 $ | **0,001 $** |

Un «no» de más es lo grave: la convocatoria que debía avisar y no avisa.

## Lo que se aprendió

1. **Haiku 5.5 acierta lo mismo que el modelo actual y cuesta 20 veces menos.** Falla en
   casos distintos, pero en el mismo número en las tres rondas.
2. **Sonnet 5.5 es más estricto.** Descarta lo que ve como fase final (nombramientos) y el
   «Spanish teacher» de colegios británicos. Sale más caro que Haiku y no acierta más.
3. **Los modelos nuevos no abren la página de la oferta.** En los portales de empleo (TodoELE,
   TES, Colegios.es…) el texto que llega es de unos 100 caracteres. Sonnet 4.6 abre la página
   y encuentra el plazo; los nuevos no la abren aunque piensen más, y se quedan sin plazo. Si el
   programa descarga la página antes de preguntar (ronda 3), coinciden en el plazo 34-35 de
   39 veces.
4. **Ruido:** el mismo modelo cambia 2 aciertos de una ronda a otra. Las diferencias de ±2 no
   significan nada.

## Casos en disputa (los decide Laureano)

- **Nombramientos de procesos de Enfermería del Trabajo ya resueltos** (concurso de méritos y
  estabilización del SERMAS: la página es el nombramiento final). Se marcaron como relevantes;
  los modelos nuevos dicen que no lo son porque ya no hay plazas abiertas. ¿Quieres aviso de
  esto?
- **«Spanish teacher» en colegios del Reino Unido** (español como lengua extranjera a alumnos
  británicos). Según tu criterio cuenta como ELE, pero Sonnet 5.5 dice que no. Si se cambia de
  modelo, el perfil tiene que decirlo de forma explícita.
- **Lengua española para nativos en un colegio británico de Barcelona**: probablemente estaba
  mal etiquetado (no es ELE y está fuera de Madrid).
