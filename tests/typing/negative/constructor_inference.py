import mongoz


class Person(mongoz.EmbeddedDocument):
    age: int = mongoz.Integer()


person: str = Person(age=42)
