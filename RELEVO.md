# Mensaje de arranque para una sesión nueva

Abre la sesión en `C:\Users\Laureano de Tomas\proyectos\vigia-core` y pega esto:

---

Seguimos con vigia. Todo en español, también tu razonamiento y las descripciones de los comandos.

Lee, por este orden:
1. `CLAUDE.md` (mapa y reglas propias).
2. `DECISIONES.md`, sobre todo lo que lleva ❓.
3. `MANTENIMIENTO.md`, según lo que toque.

**Estado (1/10, madrugada).**
- Núcleo en **v0.8.3**; los dos bots, pineados a v0.8.3.
- La forma de trabajar de temario-eir (spec 001) está en un **PR en borrador sin fusionar**, esperando el visto bueno de Laureano.

**Por comprobar:**
1. **RTVE (v0.8.3)**: en el primer daily de vigia-enfermeria del 1/10 o posterior, el log debe decir `DetailWatcher: 1 URLs de portal SPA saltadas`, no debe salir la línea `cuerpo vacío tras limpieza` de `convocatorias.rtve.es`, y si no hay otras fuentes con errores, no debe salir `fuentes con errores`. Cómo mirarlo: `MANTENIMIENTO.md` §3.

**Por dónde seguir:**
1. Si Laureano aprueba la spec 001: fusionar su PR y pasar a la misma forma `vigia-enfermeria` y `vigia-docencia` (tareas en `specs/001-forma-de-trabajo/tasks.md`).
2. Datos desactualizados vistos de paso, sin tocar: `README.md` del núcleo dice instalar `@v0.4.4`, y el `CLAUDE.md` de vigia-docencia dice que consume `vigia-core@v0.4.4` (va por v0.8.3).
