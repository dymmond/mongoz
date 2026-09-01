import mongoz


class Person(mongoz.Document):
    age: int = mongoz.Integer()


async def invalid_projection() -> None:
    await Person.query().values(fields=[1])
