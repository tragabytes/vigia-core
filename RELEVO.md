# Mensaje de arranque para una sesión nueva

Abre la sesión en `C:\Users\Laureano de Tomas\proyectos\vigia-core` y pega esto:

---

Seguimos con vigia. Todo en español, también tu razonamiento y las descripciones de los comandos.

Lee, por este orden:
1. `CLAUDE.md` (mapa y reglas propias).
2. `DECISIONES.md`, sobre todo lo que lleva ❓.
3. El `RELEVO.md` del bot que toque (`vigia-enfermeria`, `vigia-docencia`): ahí están sus pendientes.
4. `MANTENIMIENTO.md`, según lo que toque.

**Estado (16/10, noche).**
- Núcleo en **v0.16.0**, con los dos bots pineados a esa versión. Ventana de 3 días desde v0.9.0 (D22).
- Uso de la API (spec 002): el gasto queda en el log de cada run (`Enricher uso:`) y se reintentan las convocatorias que se quedaron sin resumir (v0.15.0). **Docencia prueba Haiku 5.5 hasta el 30/10** con Sonnet 4.6 de testigo (D36-D38): cada lunes hay que buscar `Testigo:` en el log del daily.
- Docencia lee 10 fuentes nuevas desde el 16/10 (spec 001 de docencia, D28-D33). Su relevo dice qué comprobar el lunes 19/10.
- Los tres repos trabajan con la forma de temario-eir.

**Por comprobar** (los puntos 1-5 ya salieron bien el 15/10; se dejan como lista de qué mirar si algo vuelve a fallar) (cómo: `MANTENIMIENTO.md` §3):
1. **UAH (v0.8.4)**: el probe de `universidades_madrid` debe salir `ok` en vigia-enfermeria. Si sale `error`, el aviso ya dirá qué listado está vacío.
2. **Comunidad de Madrid (v0.8.4)**: `comunidad_madrid … 0 errores` la mayoría de los días; algún `Read timed out` suelto puede seguir, pero ya no el 70 % de los días. Ojo: al no cortarse, ahora lee más páginas (en el CI del 14/10, 19 items en vez de 0-9) y salen más avisos de «detalle 404» y «sin fecha → today()» de ofertas viejas. Es ruido: el extractor las descarta (comprobado: solo pasó el proceso de Enfermería del Trabajo de 2025, que ya está en producción desde abril). Si algún día llega a Telegram un aviso de un proceso viejo de la Comunidad, la causa es esta. En ese CI hubo también un 404 pasajero en la página 2 de «salud laboral» (desde local responde bien).
3. **Telegram (v0.8.5)**: cuando haya avisos, el log debe tener `Telegram: mensaje enviado a N/N destinatarios`.
4. **Dashboards**: las tarjetas deben decir `AI SUMMARY (claude-sonnet-4-6)`, no `pending enrichment`.
5. El issue abierto en vigia-enfermeria («Fuentes con error en el probe») debería cerrarse cuando el probe salga limpio.

**Por dónde seguir:**
0. **Uso de la API de Anthropic** ([`specs/002-uso-api-anthropic/`](specs/002-uso-api-anthropic/tasks.md)): lunes 19/10, comprobar en el daily de los dos bots las líneas `Enricher uso:` (con `caché leída` > 0) y, en docencia, `Testigo:`. El 30/10 se decide la prueba de Haiku. Pendiente de Laureano: espacio de trabajo y clave propios con límite.
1. **v0.9.0**: en el primer daily, `since_date` debe ser hoy menos 3 (lunes: menos 5) y no deben llegar avisos de cosas ya vistas.
2. **v0.10.0**: `epreselec … 3 empresas` sin `bloqueado por el anti-robots`; si sale a diario, añadir una pausa entre empresas (D25).
3. Pendientes de cada bot en su `RELEVO.md`.
