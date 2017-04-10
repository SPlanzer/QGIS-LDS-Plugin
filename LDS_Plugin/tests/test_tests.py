import unittest   

class test_tests(unittest.TestCase):
    
    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')
        

def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(test_tests, 'test'))
    return suite

def run_tests():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())
