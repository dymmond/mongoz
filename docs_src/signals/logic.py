async def create_user(**kwargs):
    """
    Creates a user
    """
    await User.query.create(**kwargs)


async def is_verified_user(id: str):
    """
    Checks if user is verified and sends notification
    if true.
    """
    user = await User.get_document_by_id(id))

    if user.is_verified:
        # triggers the custom signal
        await User.meta.signals.on_verify.send(sender=User, instance=user)
