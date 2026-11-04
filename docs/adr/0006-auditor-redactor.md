# ADR-0006 · Nodo F dividido en Auditor y Redactor
**Decisión:** F1 valida (JSON, temperatura 0); F2 redacta (streaming, temperatura 0.3).
**Por qué:** naturalezas opuestas; solo el Redactor debe emitir tokens al usuario.
**Consecuencia:** el Auditor solo marca qué repetir; las instrucciones nuevas las escribe el Estratega.