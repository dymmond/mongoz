import asyncio

import mongoz

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri, event_loop=asyncio.get_running_loop)


class User(mongoz.Document):
    name: str = mongoz.String(max_length=255)
    email: str = mongoz.Email(max_length=255)
    is_verified: bool = mongoz.Boolean(default=False)

    class Meta:
        registry = registry
        database = "my_db"


# Create the custom signal
User.meta.signals.on_verify = mongoz.Signal()


# Create the receiver
async def trigger_notifications(sender, instance, **kwargs):
    """
    Sends email and push notification
    """
    send_email(instance.email)
    send_push_notification(instance.email)


# Register the receiver into the new Signal.
User.meta.signals.on_verify.connect(trigger_notifications)
