import uuid


class Guid:
    def __init__(self, guid: uuid.UUID | str):
        if isinstance(guid, uuid.UUID):
            self._uuid = guid
        elif isinstance(guid, str):
            g = str(guid).strip()
            if g.startswith('{') and g.endswith('}'):
                g = g[1:-1]
            self._uuid = uuid.UUID(g)

    @property
    def value(self) -> str:
        return str(self._uuid)
