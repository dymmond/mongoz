# Signals

Sometimes you might want to *listen* to a document event upon the save, meaning, you want to do a
specific action when something happens in the models.

Django for instance has this mechanism called `Signals` which can be very helpful for these cases
and to perform extra operations once an action happens in your document.

Other ORMs did a similar approach to this and a fantastic one was Ormar which took the Django approach
to its own implementation.

Mongoz being the way it is designed, got the inspiration from both of these approaches and also
supports the `Signal`.

## What are Signals

Signals are a mechanism used to trigger specific actions upon a given type of event happens within
the Mongoz models.

The same way Django approaches signals in terms of registration, Mongoz does it in the similar fashion.

## Default signals

Mongoz has default receivers for each document created within the ecosystem. Those can be already used
out of the box by you at any time.

There are also [custom signals](#custom-signals) in case you want an "extra" besides the defaults
provided.

### How to use them

The signals are inside the `mongoz.core.signals` and to import them, simply run:

``` python
from mongoz.core.signals import (
    post_delete,
    post_save,
    post_update,
    pre_delete,
    pre_save,
    pre_update,
)
```

#### pre_save

The `pre_save` is used when a document is about to be saved and triggered on `Document.save()` and
`Document.objects.create` functions.

```python
pre_save(send: Type["Document"], instance: "Document")
```

#### post_save

The `post_save` is used after the document is already created and stored in the database, meaning,
when an instance already exists after `save`. This signal is triggered on `Document.save()` and
`Document.objects.create` functions.

```python
post_save(send: Type["Document"], instance: "Document")
```

#### pre_update

The `pre_update` is used when a document is about to receive the updates and triggered on `Document.update()`
and `Document.objects.update` functions.

```python
pre_update(send: Type["Document"], instance: "Document")
```

#### post_update

The `post_update` is used when a document **already performed the updates** and triggered on `Document.update()`
and `Document.objects.update` functions.

```python
post_update(send: Type["Document"], instance: "Document")
```

#### pre_delete

The `pre_delete` is used when a document is about to be deleted and triggered on `Document.delete()`
and `Document.objects.delete` functions.

```python
pre_delete(send: Type["Document"], instance: "Document")
```

#### post_delete

The `post_update` is used when a document **is already deleted** and triggered on `Document.delete()`
and `Document.objects.delete` functions.

```python
post_update(send: Type["Document"], instance: "Document")
```

## Receiver

The receiver is the function or action that you want to perform upon a signal being triggered,
in other words, **it is what is listening to a given event**.

Let us see an example. Given the following document.

```python
{!> ../../../docs_src/signals/receiver/document.py !}
```

You can set a trigger to send an email to the registered user upon the creation of the record by
using the `post_save` signal. The reason for the `post_save` it it because the notification must
be sent **after** the creation of the record and not before. If it was before, the `pre_save` would
be the one to use.

```python hl_lines="11-12"
{!> ../../../docs_src/signals/receiver/post_save.py !}
```

As you can see, the `post_save` decorator is pointing the `User` document, meaning, it is "listing"
to events on that same document.

This is called **receiver**.

You can use any of the [default signals](#default-signals) available or even create your own
[custom signal](#custom-signals).

### Requirements

When defining your function or `receiver` it must have the following requirements:

* Must be a **callable**.
* Must have `sender` argument as first parameter which corresponds to the document of the sending object.
* Must have ****kwargs** argument as parameter as each document can change at any given time.
* Must be `async` because Mongoz document operations are awaited.

### Multiple receivers

What if you want to use the same receiver but for multiple models? Let us now add an extra `Profile`
document.

```python
{!> ../../../docs_src/signals/receiver/multiple.py !}
```

The way you define the receiver for both can simply be achieved like this:

```python hl_lines="11"
{!> ../../../docs_src/signals/receiver/post_multiple.py !}
```

This way you can match and do any custom logic without the need of replicating yourself too much and
keeping your code clean and consistent.

### Multiple receivers for the same document

What if now you want to have more than one receiver for the same document? Practically you would put all
in one place but you might want to do something else entirely and split those in multiple.

You can easily achieve this like this:

```python
{!> ../../../docs_src/signals/receiver/multiple_receivers.py !}
```

This will make sure that every receiver will execute the given defined action.


### Disconnecting receivers

If you wish to disconnect the receiver and stop it from running for a given document, you can also
achieve this in a simple way.

```python hl_lines="20 23"
{!> ../../../docs_src/signals/receiver/disconnect.py !}
```

## Custom Signals

This is where things get interesting. A lot of time you might want to have your own `Signal` and
not relying only on the [default](#default-signals) ones and this perfectly natural and common.

Mongoz allows the custom signals to take place per your own design.

Let us continue with the same example of the `User` document.

```python
{!> ../../../docs_src/signals/receiver/document.py !}
```

Now you want to have a custom signal called `on_verify` specifically tailored for your `User` needs
and logic.

So define it, you can simply do:

```python hl_lines="17"
{!> ../../../docs_src/signals/custom.py !}
```

Yes, this simple. You simply need to add a new signal `on_verify` to the document signals and the
`User` document from now on has a new signal ready to be used.

!!! Danger
    Keep in mind **signals are class level type**, which means it will affect all of the derived
    instances coming from it. Be mindful when creating a custom signal and its impacts.

Now you want to create a custom functionality to be listened in your new Signal.

```python hl_lines="21 30"
{!> ../../../docs_src/signals/register.py !}
```

Now not only you created the new receiver `trigger_notifications` but also connected it to the
the new `on_verify` signal.

### How to use it

Now it is time to use the signal in a custom logic, after all it was created to make sure it is
custom enough for the needs of the business logic.

For simplification, the example below will be a very simple logic.

```python hl_lines="17"
{!> ../../../docs_src/signals/logic.py !}
```

As you can see, the `on_verify`, it is only triggered if the user is verified and not anywhere else.

### Disconnect the signal

The process of disconnecting the signal is exactly the [same as before](#disconnecting-receivers).

```python hl_lines="10"
{!> ../../../docs_src/signals/disconnect.py !}
```
