# ADR-0005 · Mantener max_model_len en 32k
**Decisión:** no subir a 128k en la POC.
**Por qué:** el peor caso estimado usa ~14k tokens; 128k consume mucha más memoria de KV cache en GPU
y los modelos pequeños pierden precisión con contextos largos. Los límites (ventana, chunks, paneles,
muestreo) ya acotan el contexto.
**Revisar si:** el experimento de series demuestra que hace falta más detalle.