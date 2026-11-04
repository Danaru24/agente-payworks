# Aprende · El State y los reducers
El **state** es la memoria de trabajo del grafo: un diccionario que cada nodo lee y al que devuelve
*solo los campos que cambia*. LangGraph mezcla esa actualización con el state.
 
¿Qué pasa si dos nodos corren en paralelo y escriben el mismo campo? Sin reglas, uno pisaría al otro.
Un **reducer** define cómo combinarlos:
```python
observaciones: Annotated[list[str], operator.add]  # concatena en vez de reemplazar
```
En este proyecto, `completadas` usa un reducer propio que además permite *reiniciar* la lista
al comenzar una ronda nueva (`[RESET]`).