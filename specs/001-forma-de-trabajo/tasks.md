# Tareas — 001 Forma de trabajo de temario-eir

Noche del 30/09 al 1/10, autónomo (DECISIONES D5-D8). **PR en borrador, sin fusionar.**

## Núcleo (vigia-core)
- [x] Spec
- [x] `CLAUDE.md` corto: qué es, tabla de ficheros, 8 reglas propias
- [x] `MANTENIMIENTO.md` con los procedimientos
- [x] `DECISIONES.md` con las decisiones de esta noche
- [x] `RELEVO.md` con el estado real (comprobado en GitHub, no de memoria)
- [x] Nada perdido del CLAUDE.md antiguo, parte por parte:
  - Parte 1 (reglas generales) → fuera; están en las instrucciones globales (D7)
  - §5 estado en GitHub → regla 1 + MANTENIMIENTO §2
  - §6 daño real → regla 2 + MANTENIMIENTO §2
  - §7 backfills → regla 3 + MANTENIMIENTO §4
  - §8 fuentes hermanas → regla 4
  - §9 probe ≠ runtime → regla 5 + MANTENIMIENTO §3
  - §3.1-3.5 crear bot, fuente al núcleo o al bot, cutover → MANTENIMIENTO §6 y §7
  - §3.6 contratos → regla 6
  - §3.7 publicar el núcleo → MANTENIMIENTO §5
  - Gotchas de entorno → regla 8 + MANTENIMIENTO §1
- [ ] **Visto bueno de Laureano** y fusionar

## Bots (después del visto bueno)
- [ ] vigia-enfermeria: CLAUDE.md corto; revisar `BACKLOG.md` (812 líneas), `PLAN.md`, `PLAN_MAESTRO.md` e `incidents/`; lo vivo al relevo o a una spec
- [ ] vigia-docencia: CLAUDE.md corto (y quitar el `v0.4.4` desfasado); revisar `ROADMAP.md`
- [ ] Cambiar en los dos las referencias a «maestro §3.6-3.7» por `MANTENIMIENTO.md` §5-6
