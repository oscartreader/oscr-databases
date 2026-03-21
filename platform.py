from platformio.public import PlatformBase # pyright: ignore[reportMissingImports]

class CrdbPlatform(PlatformBase):
    PACKAGES = {}

    def is_embedded(self):
        return False
