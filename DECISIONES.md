# Decisiones de vigia

Lo que Claude decide mientras Laureano no está, para que lo revise. Cada entrada dice **qué** se decidió, **por qué** y **cómo se deshace**. Las marcadas con ❓ necesitan su respuesta.

## Para leer primero (noche del 14 al 15/10)

- **La Universidad de Alcalá llevaba cuatro semanas sin leerse** (desde el ~17/09): su web cambió de estructura. Arreglado. **No se perdió nada**: lo último que publicó en esos listados es de julio (D11).
- **El agente semanal de salud no lo vio** porque el aviso enseñaba la URL de la Complutense, que funciona. Ahora el aviso dice qué listado está vacío (D12).
- **La Comunidad de Madrid perdía páginas** del buscador 7 de cada 10 días por lentitud. Arreglado con más margen y un reintento (D13). No se ha perdido ninguna oferta de Enfermería del Trabajo: lo he comprobado contra lo que hay hoy en el buscador.
- **Hoy (14/10) hay novedad en la oposición de Enfermería del Trabajo de la Comunidad de Madrid (2025)**: el BOCM publica una relación complementaria de aprobados, se vuelven a ofertar 2 plazas sin cubrir y hay **10 días hábiles desde el 14/10** para elegir destino y acreditar requisitos ([BOCM](https://www.bocm.es/bocm-20261014-4)). El bot lo detectó por tres vías (BOCM, ficha y buscador de la Comunidad) y lo mandó a Telegram.
- Publicado todo como **v0.8.4** en los dos bots (D14), y dos detalles más en **v0.8.5** (D16, D21).
- **Los dashboards marcaban «pending enrichment» en casi todo**; arreglado (D18).
- **Los dos bots ya trabajan como temario-eir** (D19): cada uno con su `RELEVO.md` de pendientes.
- **Una pregunta para ti** sobre cuántos días hacia atrás mira el bot cada día (❓ D15).

## Para leer primero (noche del 30/09 al 1/10)

- **La UAM ya no se repite**: comprobado en los runs del 21/09 al 30/09 y en el dashboard (1 item de la UAM). Cerrado.
- **Arreglado el error diario de RTVE** en el dashboard y publicado como v0.8.3 en los dos bots (D2-D4). Queda comprobarlo en el daily del 1/10.
- **Nueva forma de trabajar, como en temario-eir** (D5-D7): está en un PR en borrador **sin fusionar**. Necesita tu visto bueno (❓ D8).

## Noche del 30/09 al 1/10

| # | Decisión | Motivo | Cómo se deshace |
|---|---|---|---|
| D1 | **CLAUDE.md: la suite pasa de «472» a «546 passed, 2 skipped»** y se anota que en Windows hace falta `PYTHONIOENCODING=utf-8` también para pytest. Fusionado (PR #26) | Era lo único pendiente además de la UAM; el número estaba mal desde agosto | Revertir el PR #26 |
| D2 | **El vigilante de cambios deja de mirar `convocatorias.rtve.es`** (lista `_SPA_HOSTS`). Sigue mirando el PDF de bases de RTVE | Desde al menos el 10/09, cada daily daba «cuerpo vacío tras limpieza» con esa URL y el dashboard marcaba a RTVE con error. Esa web es una aplicación que llega vacía si no la ejecuta un navegador (lo decía ya el código de la fuente): vigilarla no puede funcionar nunca. Saltarla solo a ella es lo más estrecho; excluir toda la fuente RTVE habría dejado sin vigilar el PDF | Quitar el host de `_SPA_HOSTS` en `vigia/watchers/detail_watcher.py` |
| D3 | **Publicado como v0.8.3** (PR #27, test nuevo que falla sin el arreglo, suite 547 en verde) y **fusionado sin esperar**, igual que los bumps de los bots | Pediste seguir por tu cuenta; el cambio solo quita una URL de la vigilancia, y se deshace volviendo a v0.8.2. No hay nada que borrar en producción: con el cuerpo vacío nunca se guardó ninguna foto de esa página | Volver el `requirements.txt` de cada bot a `@v0.8.2` |
| D4 | **Bots a v0.8.3** (vigia-enfermeria #37, vigia-docencia #21), con el CI en verde | Procedimiento de siempre al publicar el núcleo | Igual que D3 |
| D5 | **Solo vigia-core pasa esta noche a la forma de temario-eir**; los bots quedan como tareas (spec 001, H4) | Los bots enlazan al núcleo; si cambias algo del núcleo al revisarlo, habría que rehacerlos | — |
| D6 | **La forma nueva, en una rama y un PR en borrador, sin fusionar** | Es tu forma de trabajar y la pediste tú, pero es un cambio de cómo trabajo, no un arreglo: igual que en temario-eir 014, se construye de noche y no se da por buena hasta que la ves | Cerrar el PR |
| D7 | **Fuera del CLAUDE.md las reglas generales de trabajo** («Parte 1», adaptadas de Karpathy) **y la regla de fusionar con «sigue»** | Las primeras repiten tus instrucciones globales, que ya tienen la forma nueva. La segunda es sobre cómo trabajo contigo, no sobre el proyecto, y sigue en mi memoria | Recuperarlas del historial de git |
| D9 | **Referencias actualizadas en el mismo PR**: cuatro comentarios del código citaban «regla 6/8/9 del CLAUDE.md» (ahora 2/4/5) y el agente semanal de salud citaba «§3.7» (ahora `MANTENIMIENTO.md` §5). Solo cambian comentarios y un texto del prompt; ningún comportamiento | Si no, el código apuntaría a reglas que ya no existen o que dicen otra cosa | Van con el PR: cerrarlo lo deshace todo |
| D10 | **Pega a tener en cuenta**: el agente semanal de salud trabaja en GitHub **sin tus instrucciones globales**, así que la «Parte 1» (cambios quirúrgicos, simplicidad) sí le llegaba a él. Su prompt ya exige «cambios quirúrgicos, no romper contratos ni tests» y tiene sus propias reglas duras, por eso la he quitado igualmente | Mantener el CLAUDE.md corto | Si prefieres blindarlo, copio esas 4 reglas dentro del prompt del agente (no en el CLAUDE.md) |
| D8 ✅ | **¿Te vale la forma nueva?** Respondida el 14/10: «adelante con la fusión» (PR #28 fusionado). Si sí, fusiono el PR y hago lo mismo con los dos bots (con sus `BACKLOG.md`, `PLAN_MAESTRO.md` y `ROADMAP.md`: lo vivo pasa al relevo o a una spec y lo cerrado se archiva) | — | — |

## Noche del 14 al 15/10

| # | Decisión | Motivo | Cómo se deshace |
|---|---|---|---|
| D11 | **UAH funcionario y laboral: selector nuevo** (`div.tab-content blockquote`) **sin quitar el antiguo**, y el título se toma del `<h3>` (PR #29) | La web pasó a pestañas por año y el selector daba 0. Mantener también el antiguo deja intactos los tests que ya había y aguanta si la web vuelve atrás. Comprobado contra la web real: las fechas se leen bien, así que no se vuelve a avisar de convocatorias antiguas | Revertir el PR #29 |
| D12 | **El aviso del probe dice qué listado está vacío** cuando una fuente tiene varios (PR #30). Solo afecta a `universidades_madrid`, la única que combina listados | El agente de salud corrió el 5 y el 12/10 (unos 0,75 $ cada vez) y no abrió PR: con la URL de la Complutense no había nada roto que encontrar | Revertir el PR #30 |
| D13 | **Comunidad de Madrid: límite del buscador de 30 a 60 s y un reintento** solo si se pasa de tiempo (PR #31). El detalle de cada oferta no se toca | Medido: en frío tarda 13-43 s; repetida, 0,5 s porque el servidor la guarda en caché. Ninguna otra fuente tuvo timeouts en las dos semanas (regla 4) | Revertir el PR #31 |
| D14 | **v0.8.4 publicada y bots actualizados** (enfermería #38, docencia #22). También corregido el README, que mandaba instalar `@v0.4.4` | Para que el daily de mañana ya lo use | Volver los `requirements.txt` a `@v0.8.3` |
| D15 ❓ | **No he cambiado cuántos días mira hacia atrás el bot.** Hoy es «ayer» (el viernes, si es lunes). Si un día falla una fuente, lo publicado ese día con fecha de ayer **se pierde**, no se retrasa: al día siguiente ya queda fuera. Ampliarlo a 3 días lo evitaría (no habría avisos repetidos: el bot ya recuerda lo visto) | Cambia cómo funciona todo el pipeline en los dos bots, y el primer día podría mandar a Telegram algún aviso de algo de hace 2-3 días que antes se colaba. Es decisión tuya. En estas dos semanas no he encontrado ninguna pérdida real | Si me dices que sí: una línea en `vigia/main.py` (`_default_since`) y se prueba una semana; si llegan avisos que no quieres, se vuelve a «ayer» |
| D16 | **Dos arreglos pequeños más en el núcleo**: el notificador deja en el log cada envío a Telegram que sale bien (PR #33) y el contador «hoy» del dashboard usa la fecha UTC del run (PR #34; era el test que fallaba de madrugada) | Lo primero, porque hoy no había forma de confirmar desde el log que tu aviso llegó; lo segundo, porque estaba anotado en el relevo | Revertir el PR correspondiente |
| D17 | **No he actualizado las acciones de GitHub con Node 20** (`checkout@v4`, `setup-python@v5`) | GitHub ya las ejecuta con Node 24 y funcionan; solo avisan. Las versiones nuevas (v7) cambian cómo se guardan las credenciales de git, y el daily las usa para guardar la base de datos: si fallara, al día siguiente se repetirían avisos. Probarlo de verdad exige lanzar el daily real, que manda Telegram. La versión mínima que quita el aviso es `checkout@v5` y `setup-python@v6` | Cuando estés: cambiarlo y lanzar un daily vigilado |
| D18 | **Dashboards: «pending enrichment» salía en 113 de 115 tarjetas** aunque estaban resumidas. Arreglado en los dos bots (enfermería #39, docencia #23) | La web solo conocía las versiones 1 y 2 del enricher y va por la 6 | Revertir esos PRs |
| D19 | **Los dos bots pasan a la forma de temario-eir** (enfermería #40, docencia #24). Sus documentos antiguos (`BACKLOG`, `PLAN`, `PLAN_MAESTRO`, `incidents`, `ROADMAP`) van **sin cambios** a `historico/`; lo que sigue vivo, comprobado contra el código, está en el `RELEVO.md` de cada bot. Las decisiones de los tres repos se apuntan solo aquí | Tu «adelante» a la spec 001. Mover en vez de borrar conserva las notas técnicas de cada web | Revertir esos PRs |
| D20 | **El agente semanal de salud falló el 21 y el 28/09** sin llegar a empezar (la API lo rechazó en 0,3 s, sin mensaje) y volvió a funcionar solo el 5/10. No he tocado nada | No hay causa que arreglar; si se repite, mirar el saldo o la clave de la API | — |
| D21 | **v0.8.5 con D16** y bots actualizados | Para que el daily de mañana registre ya los envíos a Telegram | Volver los `requirements.txt` a `@v0.8.4` |

