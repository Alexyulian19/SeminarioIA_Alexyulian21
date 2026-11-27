"""Cliente de Claude falso: devuelve respuestas guionadas y guarda lo que recibe."""

from types import SimpleNamespace


def texto(contenido: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=contenido)


def herramienta(id_: str, nombre: str, entrada: dict) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=id_, name=nombre, input=entrada)


def respuesta(stop_reason: str, *bloques) -> SimpleNamespace:
    return SimpleNamespace(stop_reason=stop_reason, content=list(bloques))


class ClienteFalso:
    """Imita cliente.beta.messages.create con una lista de respuestas."""

    def __init__(self, *respuestas) -> None:
        self.respuestas = list(respuestas)
        self.llamadas: list[dict] = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._crear))

    def _crear(self, **parametros):
        # Copia la lista: el agente la sigue modificando después.
        self.llamadas.append({**parametros, "messages": list(parametros["messages"])})
        siguiente = self.respuestas.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente
