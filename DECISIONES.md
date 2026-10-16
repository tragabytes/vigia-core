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
- **Una pregunta para ti** sobre cuántos días hacia atrás mira el bot cada día (D15, respondida el 16/10: 3 días, ver D22).

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
| D15 ✅ | **Respondida el 16/10: «ampliemos a 3 días»** (ver D22). Texto original: **No he cambiado cuántos días mira hacia atrás el bot.** Hoy es «ayer» (el viernes, si es lunes). Si un día falla una fuente, lo publicado ese día con fecha de ayer **se pierde**, no se retrasa: al día siguiente ya queda fuera. Ampliarlo a 3 días lo evitaría (no habría avisos repetidos: el bot ya recuerda lo visto) | Cambia cómo funciona todo el pipeline en los dos bots, y el primer día podría mandar a Telegram algún aviso de algo de hace 2-3 días que antes se colaba. Es decisión tuya. En estas dos semanas no he encontrado ninguna pérdida real | Si me dices que sí: una línea en `vigia/main.py` (`_default_since`) y se prueba una semana; si llegan avisos que no quieres, se vuelve a «ayer» |
| D16 | **Dos arreglos pequeños más en el núcleo**: el notificador deja en el log cada envío a Telegram que sale bien (PR #33) y el contador «hoy» del dashboard usa la fecha UTC del run (PR #34; era el test que fallaba de madrugada) | Lo primero, porque hoy no había forma de confirmar desde el log que tu aviso llegó; lo segundo, porque estaba anotado en el relevo | Revertir el PR correspondiente |
| D17 | **No he actualizado las acciones de GitHub con Node 20** (`checkout@v4`, `setup-python@v5`) | GitHub ya las ejecuta con Node 24 y funcionan; solo avisan. Las versiones nuevas (v7) cambian cómo se guardan las credenciales de git, y el daily las usa para guardar la base de datos: si fallara, al día siguiente se repetirían avisos. Probarlo de verdad exige lanzar el daily real, que manda Telegram. La versión mínima que quita el aviso es `checkout@v5` y `setup-python@v6` | Cuando estés: cambiarlo y lanzar un daily vigilado |
| D18 | **Dashboards: «pending enrichment» salía en 113 de 115 tarjetas** aunque estaban resumidas. Arreglado en los dos bots (enfermería #39, docencia #23) | La web solo conocía las versiones 1 y 2 del enricher y va por la 6 | Revertir esos PRs |
| D19 | **Los dos bots pasan a la forma de temario-eir** (enfermería #40, docencia #24). Sus documentos antiguos (`BACKLOG`, `PLAN`, `PLAN_MAESTRO`, `incidents`, `ROADMAP`) van **sin cambios** a `historico/`; lo que sigue vivo, comprobado contra el código, está en el `RELEVO.md` de cada bot. Las decisiones de los tres repos se apuntan solo aquí | Tu «adelante» a la spec 001. Mover en vez de borrar conserva las notas técnicas de cada web | Revertir esos PRs |
| D20 | **El agente semanal de salud falló el 21 y el 28/09** sin llegar a empezar (la API lo rechazó en 0,3 s, sin mensaje) y volvió a funcionar solo el 5/10. No he tocado nada | No hay causa que arreglar; si se repite, mirar el saldo o la clave de la API | — |
| D21 | **v0.8.5 con D16** y bots actualizados | Para que el daily de mañana registre ya los envíos a Telegram | Volver los `requirements.txt` a `@v0.8.4` |

## 16/10

| # | Decisión | Motivo | Cómo se deshace |
|---|---|---|---|
| D22 | **El bot mira 3 días hacia atrás** (entre semana, desde hace 3 días; los lunes, desde el miércoles). Es la ventana de antes más 2 días de margen: si fallan hasta dos runs seguidos, el siguiente lo recupera. Publicado como **v0.9.0** (sube «minor» porque cambia el comportamiento) | Tu «ampliemos a 3 días». **Medido antes de publicar**: dos runs con copias de la base real de cada bot, sin Telegram ni API, uno con la ventana vieja y otro con la nueva. Con la nueva, el doble de material leído (enfermería 49 frente a 24; docencia 76 frente a 45), pero **0 avisos nuevos** en los dos: lo que pasa el filtro ya estaba visto. Duración: enfermería igual (~13 min); docencia de 1,5 a 2,75 min | `_default_since` en `vigia/main.py`: volver a `days=1` / `days=3` |
| D23 | **Acciones de GitHub a `checkout@v5` y `setup-python@v6`** en los tres repos (enfermería #42, docencia #26, núcleo #38). Cierra D17 | Las notas de versión confirman que solo cambian a Node 24; el cambio de credenciales que preocupaba llega en `checkout@v6`. Comprobado con el daily de docencia del 16/10: usa las nuevas y sube el dashboard sin problema | Volver a `@v4` / `@v5` en `.github/workflows/` |
| D24 | **El BOE y el BOCM abren las convocatorias de personal no docente de universidades** (PRs #39, #40) | Hueco real: en 2024 la UPM convocó en el BOE una plaza de Enfermería del Trabajo (BOE-A-2024-18785) que el bot habría perdido. Solo se abren las de personal laboral/PTGAS/escalas (~1 al día), no las de profesorado. Con esto, **URJC y UPM no necesitan fuente propia** (investigado: sus oposiciones salen en el BOE; la URJC solo publica extractos sin especialidad) | Revertir #39 y #40 |
| D25 | **ePreselec: la página del anti-robots cuenta como error** (PR #41) | Bloquea respondiendo 200 y la fuente lo leía como «0 ofertas». Producción no estaba bloqueada; si empieza a salir en los logs, se añade una pausa entre empresas | Revertir #41 |
| D26 | **ePreselec: SPMAS y Applus, solo ofertas de Madrid; y «vigilancia de la salud» + enfermería como señal válida** (PR #42). Tus respuestas del 16/10 | SPMAS tenía «Enfermería del Trabajo – Madrid» (2/10) y Applus «Enfermero/a Especialista en Vigilancia de la Salud», Madrid (11/09). Ninguna de las dos se avisará porque son anteriores a la ventana de 3 días | Quitar las empresas, `provincias` o el patrón en `vigia/_default_profile.py` |
| D27 | **v0.10.0** con D24-D26 y bots actualizados. Docencia fija `univ_staff_title_keywords` vacío para no abrir convocatorias de universidades: su perfil las excluye | Sube «minor» porque amplía la cobertura | Volver los `requirements.txt` a `@v0.9.0` |

## 16/10, tarde: fuentes nuevas de docencia (spec 001 de vigia-docencia)

Lo decidido por Laureano está en la spec de docencia (alcance, InfoJobs pendiente, límite de gasto). Aquí, lo que decidí yo al construir:

| # | Decisión | Motivo | Cómo se deshace |
|---|---|---|---|
| D28 ❓ | **Jooble y LinkedIn, fuera.** Lo recomendé y respondiste «adelante con todo»; lo interpreto como sí a la recomendación | Jooble aporta poco con CEU e ISP ya leídos y está detrás de Cloudflare; LinkedIn prohíbe leerlo así y bloquea servidores. Son la única vía para las academias ELE pequeñas de Madrid: ese hueco queda abierto | Si los quieres, se prueban en una rama con criterio de abandono escrito |
| D29 | **«Parte de las clases en inglés» vale; «enteramente en inglés» no** | Tu respuesta fue sobre colegios con parte en inglés; el perfil siempre excluyó los puestos solo en inglés. Ninguna regla los tira: no pasan porque sus títulos no dicen «Historia» ni «Spanish», y el enricher decide | Si también valen, se cambia una línea del prompt del enricher de docencia |
| D30 | **Las fuentes de colegios filtran materias del perfil en la propia fuente** (Colejobs, Workday, SuccessFactors, Teamtailor) | La simulación con la web real coló conserjes y profesores de Religión, Lengua o Alemán por el patrón «profesor de secundaria» (pensado para el BOE). Cada uno habría costado una llamada al enricher | Quitar `palabras` / `_MATERIA_RE` de la fuente |
| D31 | **Arreglo en el núcleo: SuccessFactors lee las palabras rápidas al usarlas** (v0.11.1) y regla 7 del CLAUDE.md ampliada | Al importar `SapEmpresa` desde el perfil docente, el lector se quedaba con las palabras de enfermería: 0 ofertas, 0 errores | Revertir #46 |
| D32 | **Lectores genéricos de Workday (v0.12.0) y Teamtailor (v0.14.0) en el núcleo**; búsqueda en la URL y palabras por empresa en SuccessFactors (v0.13.0) | Regla 2 de docencia: lo que sirve a varios perfiles va al núcleo. Enfermería no los activa | Revertir #47, #48, #49 |
| D33 | **Límites aceptados**: Inspired solo para sus colegios de Madrid (su búsqueda por palabra no filtra); TES solo las 20 más recientes (ignora la paginación por URL); Cervantes sin las convocatorias internas (restringidas, traslados) | Son límites de las webs; están anotados en cada fuente y en el relevo de docencia | — |
| D34 | **Quitado `t.html` del núcleo** (#45): una página que un agente de investigación descargó en la raíz y se coló en el commit de v0.11.0 | No es código ni entra en el paquete | — |
| D35 | **Bots**: docencia en **v0.14.0**, enfermería en **v0.11.1** (no usa Workday ni Teamtailor; v0.12-v0.14 no le cambian nada) | Subir enfermería a v0.14.0 no aporta nada y sería otro run de CI de 10 min | Subirlo cuando haga falta |

