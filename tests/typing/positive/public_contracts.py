"""Consumer-side typing contracts that must remain accepted by ty."""

from __future__ import annotations

from typing import Any, ClassVar, Dict, Mapping, Optional

from pymongo import AsyncMongoClient, InsertOne
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.results import BulkWriteResult
from typing_extensions import assert_type

import mongoz
from mongoz import Database, Document, IndexPlan, Manager, QuerySet, Registry
from mongoz.core.connection.collections import Collection

registry = Registry("mongodb://localhost:27017")
database = registry.get_database("typing")
collection = database.get_collection("users")


class Address(mongoz.EmbeddedDocument):
    city: str = mongoz.String()
    postal_code: int = mongoz.Integer()


class NamedDocument(Document):
    name: str = mongoz.String()

    class Meta:
        abstract = True
        registry = registry


class User(NamedDocument):
    age: int = mongoz.Integer(minimum=0)
    address: Address = mongoz.Embed(Address)
    aliases: list[str] = mongoz.Array(str, default=[])
    nickname: Optional[str] = mongoz.String(null=True)

    class Meta:
        registry = registry
        database = database


class ManagedUserManager(Manager["ManagedUser"]):
    def adults(self) -> ManagedUserManager:
        return self.filter(age__gte=18)


class ManagedUser(Document):
    name: str = mongoz.String()
    objects: ClassVar[ManagedUserManager] = ManagedUserManager()

    class Meta:
        registry = registry
        database = database


address = Address(city="Zurich", postal_code=8000)
user = User(name="Ada", age=37, address=address, aliases=["A"], nickname=None)

assert_type(address, Address)
assert_type(user, User)
assert_type(user.name, str)
assert_type(user.age, int)
assert_type(user.address, Address)
assert_type(user.aliases, list[str])
assert_type(User.query(), QuerySet[User])
assert_type(User.query(User.age >= 18).limit(10).skip(1), QuerySet[User])
assert_type(User.objects, Manager[User])
assert_type(ManagedUser.objects, ManagedUserManager)
assert_type(ManagedUser.objects.adults(), ManagedUserManager)
assert_type(registry, Registry)
assert_type(database, Database)
assert_type(collection, Collection)
assert_type(registry.driver, AsyncMongoClient[Dict[str, Any]])
assert_type(database._db, AsyncDatabase[Dict[str, Any]])
assert_type(collection._collection, AsyncCollection[Dict[str, Any]])


async def verify_async_contracts(session: AsyncClientSession) -> None:
    chained = User.objects.filter(age__gte=18).sort("name").using_session(session)
    assert_type(chained, Manager[User])
    assert_type(await chained, list[User])
    assert_type(await chained.first(), Optional[User])
    assert_type(await chained.last(), Optional[User])
    assert_type(await chained.get(), User)
    assert_type(await chained.get_or_none(), Optional[User])
    assert_type(await chained.create(name="Grace", age=30, address=address), User)
    assert_type(await chained.update(age=31), list[User])
    assert_type(await chained.delete(), int)
    assert_type(await chained.values(), list[dict[str, Any]])
    assert_type(await chained.values_list("name", flat=True), list[Any])

    query = User.query().using_session(session)
    assert_type(query, QuerySet[User])
    assert_type(await query.all(), list[User])
    assert_type(await query.first(), Optional[User])
    assert_type(await query.get(), User)
    assert_type(await query.update(age=32), list[User])
    assert_type(await query.delete(), int)
    assert_type(
        await User.aggregate([{"$match": {}}], session=session),
        list[Mapping[str, Any]],
    )
    assert_type(
        await User.bulk_write([InsertOne({"name": "typed"})], session=session),
        BulkWriteResult,
    )
    assert_type(await User.plan_indexes(delete_unmanaged=True, session=session), IndexPlan)
    assert_type(await User.check_indexes(drop_unmanaged=True, session=session), IndexPlan)


async def signal_receiver(sender: type[Document], **kwargs: object) -> None:
    del sender, kwargs


User.signals.pre_save.connect(signal_receiver)
