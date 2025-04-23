from logging import getLogger

import pydantic
import pytest

import mongoz
from mongoz import Document, Q
from mongoz.core.signals import (
    Broadcaster,
    post_delete,
    post_save,
    post_update,
    pre_delete,
    pre_save,
    pre_update,
)
from mongoz.exceptions import SignalError
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]

logger = getLogger(__name__)


class User(Document):
    name: str = mongoz.String(max_length=100)
    language = mongoz.String(max_length=200, null=True)

    class Meta:
        registry = client
        database = "test_db"


class Profile(Document):
    name: str = mongoz.String(max_length=100)

    class Meta:
        registry = client
        database = "test_db"


class Log(Document):
    signal = mongoz.String(max_length=255)
    instance = mongoz.Object()

    class Meta:
        registry = client
        database = "test_db"


@pytest.mark.parametrize("func", ["bad", 1, 3, [3], {"name": "test"}])
def test_passing_not_callable(func):
    with pytest.raises(SignalError):
        pre_save(User)(func)


def test_passing_no_kwargs():
    with pytest.raises(SignalError):

        @pre_save(User)
        def execute(sender, instance): ...


def test_invalid_signal():
    broadcaster = Broadcaster()
    with pytest.raises(SignalError):
        broadcaster.save = 1


async def test_signals():
    @pre_save(User)
    async def pre_saving(sender, instance, **kwargs):
        await Log(signal="pre_save", instance=instance.model_dump()).create()
        logger.info(f"pre_save signal broadcasted for {instance.get_instance_name()}")

    @post_save(User)
    async def post_saving(sender, instance, **kwargs):
        await Log(signal="post_save", instance=instance.model_dump()).create()
        logger.info(f"post_save signal broadcasted for {instance.get_instance_name()}")

    @pre_update(User)
    async def pre_updating(sender, instance, **kwargs):
        await Log(signal="pre_update", instance=instance.model_dump()).create()
        logger.info(f"pre_update signal broadcasted for {instance.get_instance_name()}")

    @post_update(User)
    async def post_updating(sender, instance, **kwargs):
        await Log(signal="post_update", instance=instance.model_dump()).create()
        logger.info(f"post_update signal broadcasted for {instance.get_instance_name()}")

    @pre_delete(User)
    async def pre_deleting(sender, instance, **kwargs):
        await Log(signal="pre_delete", instance=instance.model_dump()).create()
        logger.info(f"pre_delete signal broadcasted for {instance.get_instance_name()}")

    @post_delete(User)
    async def post_deleting(sender, instance, **kwargs):
        await Log(signal="post_delete", instance=instance.model_dump()).create()
        logger.info(f"post_delete signal broadcasted for {instance.get_instance_name()}")

    # Signals for the create
    user = await User(name="Mongoz").create()
    logs = await Log.query().all()

    assert len(logs) == 2
    assert logs[0].signal == "pre_save"
    assert logs[0].instance["name"] == user.name
    assert logs[1].signal == "post_save"

    user = await User(name="Esmerald").create()
    logs = await Log.query().all()

    assert len(logs) == 4
    assert logs[2].signal == "pre_save"
    assert logs[2].instance["name"] == user.name
    assert logs[3].signal == "post_save"

    # For the updates
    user = await user.update(name="Saffier")
    logs = await Log.query(Q.contains(Log.signal, "update")).all()

    assert len(logs) == 2
    assert logs[0].signal == "pre_update"
    assert logs[1].signal == "post_update"

    user.signals.pre_update.disconnect(pre_updating)
    user.signals.post_update.disconnect(post_updating)

    # Disconnect the signals
    user = await user.update(name="Saffier")
    logs = await Log.query(Q.contains(Log.signal, "update")).all()
    assert len(logs) == 2

    # Delete
    await user.delete()
    logs = await Log.query(Q.contains(Log.signal, "delete")).all()
    assert len(logs) == 2

    user.signals.pre_delete.disconnect(pre_deleting)
    user.signals.post_delete.disconnect(post_deleting)
    user.signals.pre_save.disconnect(pre_saving)
    user.signals.post_save.disconnect(post_saving)

    users = await User.query().all()
    assert len(users) == 1


async def test_staticmethod_signals():
    class Static:
        @staticmethod
        @pre_save(User)
        async def pre_save_one(sender, instance, **kwargs):
            await Log(signal="pre_save_one", instance=instance.model_dump_json()).create()

        @staticmethod
        @pre_save(User)
        async def pre_save_two(sender, instance, **kwargs):
            await Log(signal="pre_save_two", instance=instance.model_dump_json()).create()

    # Signals for the create
    user = await User(name="Mongoz").create()
    logs = await Log.query().all()

    assert len(logs) == 2

    user.signals.pre_save.disconnect(Static.pre_save_one)
    user.signals.pre_save.disconnect(Static.pre_save_two)


async def test_multiple_senders():
    @pre_save([User, Profile])
    async def pre_saving(sender, instance, **kwargs):
        await Log(signal="pre_save", instance=instance.model_dump_json()).create()

    user = await User(name="Mongoz").create()
    profile = await User(name="Profile Mongoz").create()

    logs = await Log.query().all()
    assert len(logs) == 2

    user.signals.pre_save.disconnect(pre_saving)
    profile.signals.pre_save.disconnect(pre_saving)


async def test_custom_signal():
    async def processing(sender, instance, **kwargs):
        instance.name = f"{instance.name} ODM"
        await instance.save()

    User.meta.signals.custom.connect(processing)

    user = User(name="Mongoz")
    await User.meta.signals.custom.send(sender=User, instance=user)

    assert user.name == "Mongoz ODM"

    User.meta.signals.custom.disconnect(processing)
