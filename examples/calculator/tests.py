'''Tests the RPC "calculator" example.'''
from pulsar import send
from pulsar.apps import rpc
from pulsar.apps.test import unittest

from .manage import server


class TestRpcOnThread(unittest.TestCase):
    app = None
    client_timeout = 10
    concurrency = 'thread'
    
    @classmethod
    def setUpClass(cls):
        name = 'calc_' + cls.concurrency
        s = server(bind='127.0.0.1:0', name=name, concurrency=cls.concurrency)
        outcome = send('arbiter', 'run', s)
        yield outcome
        app = outcome.result
        cls.app = app
        cls.uri = 'http://{0}:{1}'.format(*app.address)
        
    @classmethod
    def tearDownClass(cls):
        if cls.app:
            return send('arbiter', 'kill_actor', cls.app.mid)
        
    def setUp(self):
        self.p = rpc.JsonProxy(self.uri, timeout=self.client_timeout)
        
    def testHandler(self):
        s = self.app
        self.assertTrue(s.callable)
        middleware = s.callable
        root = middleware.handler
        self.assertEqual(root.content_type, 'application/json')
        self.assertEqual(middleware.path,'/')
        self.assertTrue(middleware.raise404)
        self.assertEqual(len(root.subHandlers), 1)
        hnd = root.subHandlers['calc']
        self.assertFalse(hnd.isroot())
        self.assertEqual(hnd.subHandlers, {})
        self.assertTrue(s.mid)
        
    # Pulsar server commands
    def testPing(self):
        result = self.p.ping()
        self.assertEqual(result, 'pong')
        
    def testListOfFunctions(self):
        result = self.p.functions_list()
        self.assertTrue(result)
        
    # Test Object method
    def test_check_request(self):
        result = self.p.check_request('check_request')
        self.assertTrue(result)
        
    def testAdd(self):
        result = self.p.calc.add(3,7)
        self.assertEqual(result, 10)
        
    def testSubtract(self):
        result = self.p.calc.subtract(546, 46)
        self.assertEqual(result, 500)
        
    def testMultiply(self):
        result = self.p.calc.multiply(3, 9)
        self.assertEqual(result, 27)
        
    def testDivide(self):
        result = self.p.calc.divide(50, 25)
        self.assertEqual(result, 2)
        
    def testInfo(self):
        result = self.p.server_info()
        self.assertTrue('server' in result)
        server = result['server']
        self.assertTrue('version' in server)
        
    def testInvalidParams(self):
        self.assertRaises(rpc.InvalidParams, self.p.calc.add, 50, 25, 67)
        
    def testInvalidParamsFromApi(self):
        self.assertRaises(rpc.InvalidParams, self.p.calc.divide, 50, 25, 67)
        
    def testInvalidFunction(self):
        self.assertRaises(rpc.NoSuchFunction, self.p.foo, 'ciao')
        
    def testInternalError(self):
        self.assertRaises(rpc.InternalError, self.p.calc.divide, 'ciao', 'bo')
        
    def testCouldNotserialize(self):
        self.assertRaises(rpc.InternalError, self.p.dodgy_method)
        
    def testpaths(self):
        '''Fetch a sizable ammount of data'''
        result = self.p.calc.randompaths(num_paths=20, size=100,
                                         mu=1, sigma=2)
        self.assertTrue(result)
        

class TestRpcOnProcess(TestRpcOnThread):
    concurrency = 'process'