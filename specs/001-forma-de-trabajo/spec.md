# Especificación: trabajar en vigia como en temario-eir

**Carpeta**: `specs/001-forma-de-trabajo/` · **Fecha**: 2026-10-01 · **Estado**: borrador, hecho de noche, **sin fusionar**

**Lo que se pidió** (Laureano, noche del 30/09 al 1/10): «Las instrucciones que tenías para trabajar son antiguas y ya no me gustan, no sé si puedes también copiarte la manera de trabajar que tengo en proyectos más recientes como "temario-eir". Me refiero a claude.md, las specs y esas cosas». Antes: «documenta las decisiones y sigue por tu cuenta».

## Qué cambia

Hoy el `CLAUDE.md` de vigia-core son 280 líneas: repite las reglas generales de trabajo (que ya están en tus instrucciones globales), mezcla las reglas del pipeline con procedimientos paso a paso y no dice dónde está lo pendiente. Lo pendiente vive en la memoria de Claude o en ficheros sueltos de los bots (`BACKLOG.md`, `PLAN_MAESTRO.md`, `ROADMAP.md`), algunos sin tocar desde junio.

Con la forma de temario-eir queda así:

| Fichero | Para qué |
|---|---|
| `CLAUDE.md` | Corto: qué es vigia-core, una tabla de «qué mirar para qué» y las reglas propias del pipeline |
| `specs/NNN-nombre/spec.md` | Una por cada cosa nueva: qué se pidió, historias, criterios de aceptación, casos raros, qué queda fuera |
| `specs/NNN-nombre/tasks.md` | El estado de esa cosa, con casillas |
| `DECISIONES.md` | Lo que Claude decide sin ti: qué, por qué y cómo se deshace. Las que necesitan tu respuesta, con ❓ |
| `RELEVO.md` | El mensaje para arrancar la sesión siguiente: estado, qué comprobar, por dónde seguir |
| `MANTENIMIENTO.md` | Los procedimientos paso a paso: diagnosticar producción, publicar el núcleo, crear un bot, etc. |

## Historias

### H1 — Saber qué queda pendiente sin preguntarme (P1)

Al abrir una sesión, basta con leer `RELEVO.md` para saber el estado y qué toca. Nada importante vive solo en la memoria de Claude.

**Criterios**: `RELEVO.md` existe y lista lo pendiente de verdad (comprobado contra GitHub, no de memoria).

### H2 — Ver lo que decidí mientras dormías (P1)

Cada decisión tomada en tu ausencia está en `DECISIONES.md`, con su motivo y cómo se deshace.

**Criterios**: las decisiones de esta noche están ahí, numeradas.

### H3 — Un CLAUDE.md que se lee en un minuto (P1)

- Fuera las reglas generales de trabajo que repiten tus instrucciones globales (la antigua «Parte 1»).
- Las reglas propias del pipeline se quedan, más cortas, cada una con su comprobación.
- Los procedimientos (crear un bot, publicar el núcleo, diagnosticar el estado real) pasan a `MANTENIMIENTO.md`, sin perder ningún paso.

**Criterios**: no se pierde ninguna regla ni ningún paso del documento antiguo (se revisa uno a uno en `tasks.md`).

### H4 — Lo mismo en los dos bots (P2) · después de tu visto bueno

`vigia-enfermeria` y `vigia-docencia` pasan a la misma forma. Sus pendientes sueltos (`BACKLOG.md`, `PLAN_MAESTRO.md`, `ROADMAP.md`) se revisan y lo que siga vivo pasa a su `RELEVO.md` o a una spec.

**No se hace esta noche**: depende de cómo quede el núcleo cuando lo revises.

## Casos raros

- **Los bots enlazan al CLAUDE.md del núcleo** («maestro §3.6-3.7»). Al moverse esas secciones, el enlace sigue funcionando (va al fichero), pero los números de sección dejan de existir. Hasta que se haga H4, el nuevo CLAUDE.md dice dónde ha ido cada parte.
- **Memoria de Claude**: lo que estaba solo en la memoria (la comprobación pendiente de la UAM) pasa a `RELEVO.md`; la memoria se queda para preferencias tuyas, no para el estado del trabajo.

## Fuera de alcance

- Cambiar el código o el comportamiento del pipeline.
- Tus instrucciones globales (`~/.claude/CLAUDE.md`): ya tienen la forma nueva.
