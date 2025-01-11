from pantheum.smart_func import smart_func


async def test_smart_func():
    @smart_func(model="gpt-4o-mini")
    async def translate(text: str) -> str:
        """Translate the given text to English."""

    assert await translate("你好，世界！") == "Hello, world!"


def test_smart_func_sync():
    @smart_func(model="gpt-4o-mini")
    def translate(text: str) -> str:
        """Translate the given text to English."""

    assert translate("你好，世界！") == "Hello, world!"
