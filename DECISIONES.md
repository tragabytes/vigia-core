# Decisiones de vigia

Lo que Claude decide mientras Laureano no está, para que lo revise. Cada entrada dice **qué** se decidió, **por qué** y **cómo se deshace**. Las marcadas con ❓ necesitan su respuesta.

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
| D8 ❓ | **¿Te vale la forma nueva?** Si sí, fusiono el PR y hago lo mismo con los dos bots (con sus `BACKLOG.md`, `PLAN_MAESTRO.md` y `ROADMAP.md`: lo vivo pasa al relevo o a una spec y lo cerrado se archiva) | — | — |
