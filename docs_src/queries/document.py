import mongoz

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri)


class Role(mongoz.Document):
    code: str = mongoz.String(max_length=50)
    name: str = mongoz.String(max_length=100)

    class Meta:
        registry = registry
        database = "my_db"


class User(mongoz.Document):
    is_active: bool = mongoz.Boolean(default=True)
    first_name: str = mongoz.String(max_length=50)
    last_name: str = mongoz.String(max_length=50)
    email: str = mongoz.Email(max_lengh=100)
    role_id: mongoz.ObjectId = mongoz.ForeignKey(Role, null=True)
    password: str = mongoz.String(max_length=1000)

    class Meta:
        registry = registry
        database = "my_db"
