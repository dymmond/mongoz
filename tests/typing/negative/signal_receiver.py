import mongoz


def sync_receiver(sender: type[mongoz.Document], **kwargs: object) -> None:
    del sender, kwargs


mongoz.Signal().connect(sync_receiver)
