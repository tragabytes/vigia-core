# Mensaje de arranque para una sesión nueva

Abre la sesión en `C:\Users\Laureano de Tomas\proyectos\vigia-core` y pega esto:

---

Seguimos con vigia. Todo en español, también tu razonamiento y las descripciones de los comandos.

Lee, por este orden:
1. `CLAUDE.md` (mapa y reglas propias).
2. `DECISIONES.md`, sobre todo lo que lleva ❓.
3. El `RELEVO.md` del bot que toque (`vigia-enfermeria`, `vigia-docencia`): ahí están sus pendientes.
4. `MANTENIMIENTO.md`, según lo que toque.

**Estado (14/10, noche).**
- Núcleo en **v0.8.5**; los dos bots, pineados a v0.8.5.
- Los tres repos trabajan ya con la forma de temario-eir (spec 001 cerrada).

**Por comprobar en el primer daily del 15/10 o posterior** (cómo: `MANTENIMIENTO.md` §3):
1. **UAH (v0.8.4)**: el probe de `universidades_madrid` debe salir `ok` en vigia-enfermeria. Si sale `error`, el aviso ya dirá qué listado está vacío.
2. **Comunidad de Madrid (v0.8.4)**: `comunidad_madrid … 0 errores` la mayoría de los días; algún `Read timed out` suelto puede seguir, pero ya no el 70 % de los días. Ojo: al no cortarse, ahora lee más páginas (en el CI del 14/10, 19 items en vez de 0-9) y salen más avisos de «detalle 404» y «sin fecha → today()» de ofertas viejas. Es ruido: el extractor las descarta (comprobado: solo pasó el proceso de Enfermería del Trabajo de 2025, que ya está en producción desde abril). Si algún día llega a Telegram un aviso de un proceso viejo de la Comunidad, la causa es esta. En ese CI hubo también un 404 pasajero en la página 2 de «salud laboral» (desde local responde bien).
3. **Telegram (v0.8.5)**: cuando haya avisos, el log debe tener `Telegram: mensaje enviado a N/N destinatarios`.
4. **Dashboards**: las tarjetas deben decir `AI SUMMARY (claude-sonnet-4-6)`, no `pending enrichment`.
5. El issue abierto en vigia-enfermeria («Fuentes con error en el probe») debería cerrarse cuando el probe salga limpio.

**Por dónde seguir:**
1. Responder ❓ D15 (días hacia atrás que mira el bot) con Laureano.
2. Acciones de GitHub con Node 20 (D17), con Laureano delante.
3. Pendientes de cada bot en su `RELEVO.md`.
