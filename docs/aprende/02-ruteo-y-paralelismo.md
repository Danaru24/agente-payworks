# Aprende · Ruteo y paralelismo
Una **arista condicional** es una función que lee el state y decide el siguiente nodo.
Si devuelve una **lista**, esos nodos corren en paralelo y el nodo destino común espera a todos.
```python
def ruta_estratega(state):
    return ["bibliotecario", "catalogador"]   # corren al mismo tiempo
```
El Observador no entra en ese lote porque necesita los UIDs que encuentra el Catalogador:
**paralelizar solo lo que es independiente.**