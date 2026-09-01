import mongoz


class InvalidField(mongoz.EmbeddedDocument):
    age: str = mongoz.Integer()
