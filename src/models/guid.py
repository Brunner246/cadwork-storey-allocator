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

    @property
    def value_with_braces(self) -> str:
        return f'{{{self._uuid}}}'


def create_guid() -> Guid:
    return Guid(uuid.uuid4())


if __name__ == "__main__":
    g = create_guid()
    print(g.value)
    print(g.value_with_braces)