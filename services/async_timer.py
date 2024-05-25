import asyncio

class AsyncTimer:
    """This creates an async timer that can be used to schedule periodic tasks.  It will begin running on creation."""
    def __init__(self,interval_seconds:int,async_func):
        self.interval = interval_seconds
        self.callback = async_func
        self._task = asyncio.create_task(self._run())

    async def _run(self):
        while True:
            await asyncio.sleep(self.interval)
            await self.callback()

    def stop(self):
        self._task.cancel()