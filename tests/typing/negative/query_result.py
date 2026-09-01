import mongoz


class Person(mongoz.Document):
    age: int = mongoz.Integer()


async def invalid_result() -> None:
    _name: str = await Person.query().get()
