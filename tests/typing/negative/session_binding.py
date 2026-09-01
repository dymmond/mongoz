import mongoz


class Person(mongoz.EmbeddedDocument):
    age: int = mongoz.Integer()


mongoz.Manager().using_session("not-a-session")
