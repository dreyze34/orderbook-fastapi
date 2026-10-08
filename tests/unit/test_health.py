import unittest
from app.main import health


class TestHealthUnit(unittest.IsolatedAsyncioTestCase):
    async def test_health(self):
        self.assertEqual(await health(), {"status": "ok"})
