async with registry.driver.start_session() as session:
    async with await session.start_transaction():
        users = User.objects.using_session(session)
        created = await users.create(name="Ada")
        await created.update(active=True, session=session)
