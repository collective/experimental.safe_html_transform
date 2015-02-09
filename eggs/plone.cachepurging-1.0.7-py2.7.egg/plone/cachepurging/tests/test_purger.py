"""This test is borrwed heavily from Products.CMFSquidTool. That code is ZPL
licensed.
"""

import os
import threading
import unittest
import Queue
import time

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from plone.cachepurging.purger import DefaultPurger

# Define a test HTTP server that returns canned responses

SERVER_PORT = int(os.environ.get('ZSERVER_PORT', 8765))


class TestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def do_PURGE(self):
        # Get the pre-defined response from the server's queue.
        try:
            nr = self.server.response_queue.get(block=False)
        except Queue.Empty:
            print "Unexpected connection from the purge tool"
            print self.command, self.path, self.protocol_version
            for h, v in self.headers.items():
                print "%s: %s" % (h,v)
            raise RuntimeError, "Unexpected connection"

        # We may have a function to call to check things.
        validator = nr.get('validator')
        if validator:
            validator(self)

        # We may have to wake up some other code now the test connection
        # has been made, but before the response is sent.
        waiter = nr.get('waiter')
        if waiter:
            waiter.acquire()
            waiter.release()

        # for now, response=None means simulate an unexpected error.
        if nr['response'] is None:
            self.rfile.close()
            return

        # Send the response.
        self.send_response(nr['response'])
        headers = nr.get('headers', None)
        if headers:
            for h, v in headers.items():
                self.send_header(h, v)
        data = nr.get('data', '')
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

class TestHTTPServer(HTTPServer):

    def __init__(self, address, handler):
        HTTPServer.__init__(self, address, handler)
        self.response_queue = Queue.Queue()

    def queue_response(self, **kw):
        self.response_queue.put(kw)

# Finally the test suites.

class TestCase(unittest.TestCase):

    def setUp(self):
        self.purger = DefaultPurger()
        self.httpd, self.httpt = self.startServer()

    def tearDown(self):
        try:
            # If anything remains in our response queue, it means the test
            # failed (but - we give it a little time to stop.)
            if self.httpd is not None:
                for i in range(10):
                    if self.httpd.response_queue.empty():
                        break
                    time.sleep(0.1)
                self.assertTrue(self.httpd.response_queue.empty(), "response queue not consumed")
            if not self.purger.stopThreads(wait=True):
                self.fail("The purge threads did not stop")
        finally:
            if self.httpd is not None:
                self.httpd.shutdown()

                if self.httpt.isAlive():
                    self.httpt.join(5)

                if self.httpt.isAlive():
                    self.fail("Thread failed to shut down")

                self.purger = None
                self.httpd, self.httpt = None, None

    def startServer(self, port=SERVER_PORT, start=True):
        """Start a TestHTTPServer in a separate thread, returning a tuple
        (server, thread). If start is true, the thread is started.
        """
        server_address = ('localhost', port)
        httpd = TestHTTPServer(server_address, TestHandler)
        t = threading.Thread(target=httpd.serve_forever)
        if start:
            t.start()
        return httpd, t

class TestSync(TestCase):

    def setUp(self):
        super(TestSync, self).setUp()
        self.purger.http_1_1 = True

    def tearDown(self):
        super(TestSync, self).tearDown()

    def dispatchURL(self, path, method="PURGE", port=SERVER_PORT):
        url = "http://localhost:%s%s" % (port, path)
        return self.purger.purgeSync(url, method)

    def testSimpleSync(self):
        self.httpd.queue_response(response=200)
        resp = self.dispatchURL("/foo")
        self.assertEqual((200, '', ''), resp)

    def testHeaders(self):
        headers = {'X-Squid-Error': 'error text',
                   'X-Cache': 'a message',
        }
        self.httpd.queue_response(response=200, headers=headers)
        status, msg, err = self.dispatchURL("/foo")
        self.assertEqual(msg, 'a message')
        self.assertEqual(err, 'error text')
        self.assertEqual(status, 200)

    def testError(self):
        self.httpd.queue_response(response=None)
        status, msg, err = self.dispatchURL("/foo")
        self.assertEqual(status, 'ERROR')

class TestSyncHTTP10(TestSync):

    def setUp(self):
        super(TestSync, self).setUp()
        self.purger.http_1_1 = False

class TestAsync(TestCase):

    def dispatchURL(self, path, method="PURGE", port=SERVER_PORT):
        url = "http://localhost:%s%s" % (port, path)
        self.purger.purgeAsync(url, method)

        # Item should now be in the queue!
        q, w = self.purger.getQueueAndWorker(url)
        for i in range(10):
            if q.qsize() == 0:
                break
            time.sleep(0.1)
        else:
            self.fail("Nothing consumed our queued item")
        # Make sure the other thread has actually processed it!
        time.sleep(0.1)

    def testSimpleAsync(self):
        self.httpd.queue_response(response=200)
        self.dispatchURL("/foo")
        # tear-down will complain if nothing was sent

    def testAsyncError(self):
        # In this test we arrange for an error condition in the middle
        # of 2 items - this forces the server into its retry condition.
        self.httpd.queue_response(response=200)
        self.httpd.queue_response(response=None)
        self.httpd.queue_response(response=200)
        self.dispatchURL("/foo") # will consume first.
        self.dispatchURL("/bar") # will consume error, then retry

class TestAsyncConnectionFailure(TestCase):

    def setUp(self):
        # Override setup to not start the server immediately
        self.purger = DefaultPurger()
        self.httpd, self.httpt = self.startServer(start=False)

    def dispatchURL(self, path, method="PURGE", port=SERVER_PORT):
        url = "http://localhost:%s%s" % (port, path)
        self.purger.purgeAsync(url, method)

        # Item should now be in the queue!
        q, w = self.purger.getQueueAndWorker(url)
        for i in range(10):
            if q.qsize() == 0:
                break
            time.sleep(0.1)
        else:
            self.fail("Nothing consumed our queued item")
        # Make sure the other thread has actually processed it!
        time.sleep(0.1)

    def testConnectionFailure(self):
        oldTimeout = self.httpd.socket.gettimeout()
        self.httpd.socket.settimeout(0.1)
        try:
            self.dispatchURL("/foo")
            time.sleep(0.2)
        finally:
            self.httpd.socket.settimeout(oldTimeout)

        self.httpd.queue_response(response=200)
        self.httpt.start()

        # We should have entered the 'connection retry' loop, which
        # will wait 2 seconds before trying again - wait at least that long.
        for i in range(25):
            if self.httpd.response_queue.empty():
                break
            time.sleep(0.1)
        # else - our tearDown will complain about the queue

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

