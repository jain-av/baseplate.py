import importlib
import queue
import unittest

import gevent.monkey
import gevent.queue

from baseplate.server.monkey import gevent_is_patched, patch_stdlib_queues


class MonkeyPatchTests(unittest.TestCase):
    def tearDown(self):
        importlib.reload(queue)
        gevent.monkey.saved.clear()

    def test_patch_stdlib_queues(self):
        self.assertIs(queue.LifoQueue is not gevent.queue.LifoQueue, True)
        patch_stdlib_queues()
        self.assertIs(queue.LifoQueue is gevent.queue.LifoQueue, True)

    def test_is_gevent_patched(self):
        self.assertIs(gevent_is_patched(), False)
        patch_stdlib_queues()
        self.assertIs(gevent_is_patched(), True)
