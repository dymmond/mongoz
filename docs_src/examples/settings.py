from mongoz import MongozSettings


class ApplicationMongozSettings(MongozSettings):
    lookup_prefix: str = "joined_"


configured = ApplicationMongozSettings()
assert configured.lookup_prefix == "joined_"
