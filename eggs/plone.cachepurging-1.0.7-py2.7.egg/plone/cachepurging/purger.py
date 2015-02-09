"""The following is borrowed heavily from Products.CMFSquidTool. That code
is ZPL licensed.

Asynchronous purging works as follows:

* Each remote host gets a queue and a worker thread.

* Each worker thread manages its own connection.  The queue is not processed
  until it can establish a connection.  Once a connection is established, the
  queue is purged one item at a time. Should the connection fail, the worker
  thread again waits until a connection can be re-established.
"""

import atexit
import httplib
import logging
import Queue
import socket
import sys
import threading
import time
import urlparse

from App.config import getConfiguration
from zope.interface import implements

from plone.cachepurging.interfaces import IPurger

logger = logging.getLogger('plone.cachepurging')


class Connection(httplib.HTTPConnection):
    """A connection that can handle either HTTP or HTTPS
    """

    def __init__(self, host, port=None, strict=None, scheme="http", timeout=5):
        self.scheme = scheme
        if scheme == "http":
            self.default_port = httplib.HTTP_PORT
        elif scheme == "https":
            self.default_port = httplib.HTTPS_PORT
        else:
            raise ValueError("Invalid scheme '%s'" % scheme)
        httplib.HTTPConnection.__init__(self, host, port, strict,
            timeout=timeout)
        self.timeout = timeout

    def connect(self):
        if self.scheme == "http":
            httplib.HTTPConnection.connect(self)
        elif self.scheme == "https":
            import ssl # import here in case python has no ssl support
            # Clone of httplib.HTTPSConnection.connect
            sock = socket.create_connection((self.host, self.port),
                timeout=self.timeout)
            key_file = cert_file = None
            self.sock = ssl.wrap_socket(sock, key_file, cert_file)
        else:
            raise ValueError("Invalid scheme '%s'" % self.scheme)


class DefaultPurger(object):

    implements(IPurger)

    def __init__(self, factory=Connection, timeout=30, backlog=200,
            errorHeaders=('x-squid-error', ), http_1_1=True):
        self.factory = factory
        self.timeout = timeout
        self.queues = {}
        self.workers = {}
        self.backlog = backlog
        self.queueLock = threading.Lock()
        self.errorHeaders = errorHeaders
        self.http_1_1 = http_1_1

    def purgeAsync(self, url, httpVerb='PURGE'):
        (scheme, host, path, params, query, fragment) = urlparse.urlparse(url)
        __traceback_info__ = (url, httpVerb, scheme, host,
                              path, params, query, fragment)

        q, w = self.getQueueAndWorker(url)
        try:
            q.put((url, httpVerb), block=False)
            logger.debug('Queued %s' % url)
        except Queue.Full:
            # Make a loud noise. Ideally the queue size would be
            # user-configurable - but the more likely case is that the purge
            # host is down.
            if not getConfiguration().debug_mode:
                logger.warning("The purge queue for the URL %s is full - the "
                               "request will be discarded.  Please check the "
                               "server is reachable, or disable this purge "
                               "host", url)

    def purgeSync(self, url, httpVerb='PURGE'):
        try:
            conn = self.getConnection(url)
            try:
                resp, xcache, xerror = self._purgeSync(conn, url, httpVerb)
                status = resp.status
            finally:
                conn.close()
        except:
            status = "ERROR"
            err, msg, tb = sys.exc_info()
            from traceback import format_exception
            xerror = '\n'.join(format_exception(err, msg, tb))
            # Avoid leaking a ref to traceback.
            del err, msg, tb
            xcache = ''
        logger.debug('Finished %s for %s: %s %s'
                     % (httpVerb, url, status, xcache))
        if xerror:
            logger.debug('Error while purging %s:\n%s' % (url, xerror))
        logger.debug("Completed synchronous purge of %s", url)
        return status, xcache, xerror

    def stopThreads(self, wait=False):
        for w in self.workers.itervalues():
            w.stopping = True
        # in case the queue is empty, wake it up so the .stopping flag is seen
        for q in self.queues.values():
            try:
                q.put(None, block=False)
            except Queue.Full:
                # no problem - self.stopping should be seen.
                pass
        ok = True
        if wait:
            for w in self.workers.itervalues():
                w.join(5)
                if w.isAlive():
                    logger.warning("Worker thread %s failed to terminate", w)
                    ok = False
        return ok

    def getConnection(self, url):
        """Creates a new connection - returns a connection object that is
        already connected. Exceptions raised by that connection are not
        trapped.
        """

        (scheme, host, path, params, query, fragment) = urlparse.urlparse(url)
        #
        # process.
        conn = self.factory(host, scheme=scheme, timeout=self.timeout)
        conn.connect()
        logger.debug("established connection to %s", host)
        return conn

    def getQueueAndWorker(self, url):
        """Create or retrieve a queue and a worker thread instance for the
        given URL.
        """

        (scheme, host, path, params, query, fragment) = urlparse.urlparse(url)
        key = (host, scheme)
        if key not in self.queues:
            self.queueLock.acquire()
            try:
                if key not in self.queues:
                    logger.debug("Creating worker thread for %s://%s",
                                 scheme, host)
                    assert key not in self.workers
                    self.queues[key] = queue = Queue.Queue(self.backlog)
                    self.workers[key] = worker = Worker(
                        queue, host, scheme, self)
                    worker.start()
            finally:
                self.queueLock.release()
        return self.queues[key], self.workers[key]

    def _purgeSync(self, conn, url, httpVerb):
        """Perform the purge request. Returns a triple
        ``(resp, xcache, xerror)`` where ``resp`` is the response object for
        the connection, ``xcache`` is the contents of the X-Cache header,
        and ``xerror`` is the contents of the first header found of the
        header list in ``self.errorHeaders``.
        """

        (scheme, host, path, params, query, fragment) = urlparse.urlparse(url)
        __traceback_info__ = (url, httpVerb, scheme, host,
                              path, params, query, fragment)

        if self.http_1_1:
            conn._http_vsn = 11
            conn._http_vsn_str = 'HTTP/1.1'
        else:
            conn._http_vsn = 10
            conn._http_vsn_str = 'HTTP/1.0'
            # When using HTTP 1.0, to make up for the lack of a 'Host' header
            # we use the full url as the purge path, to allow for virtual
            # hosting in squid
            path = url

        purge_path = urlparse.urlunparse(
            ('', '', path, params, query, fragment))
        logger.debug('making %s request to %s for %s.',
            httpVerb, host, purge_path)
        conn.putrequest(httpVerb, purge_path, skip_accept_encoding=True)
        conn.endheaders()
        resp = conn.getresponse()

        xcache = resp.getheader('x-cache', '')
        xerror = ''
        for header in self.errorHeaders:
            xerror = resp.getheader(header, '')
            if xerror:
                # Break on first found.
                break
        resp.read()
        logger.debug("%s of %s: %s %s",
            httpVerb, url, resp.status, resp.reason)
        return resp, xcache, xerror


class Worker(threading.Thread):
    """Worker thread for purging.
    """

    def __init__(self, queue, host, scheme, producer):
        self.host = host
        self.scheme = scheme
        self.producer = producer
        self.queue = queue
        self.stopping = False
        super(Worker, self).__init__(
            name="PurgeThread for %s://%s" % (scheme, host))

    def stop(self):
        self.stopping = True

    def run(self):
        logger.debug("%s starting", self)
        # Queue should always exist!
        q = self.producer.queues[(self.host, self.scheme)]
        connection = None
        atexit.register(self.stop)
        try:
            while not self.stopping:
                item = q.get()
                if self.stopping or item is None: # Shut down thread signal
                    logger.debug('Stopping worker thread for '
                                 '(%s, %s).' % (self.host, self.scheme))
                    break
                url, httpVerb = item

                # Loop handling errors (other than connection errors) doing
                # the actual purge.
                for i in range(5):
                    if self.stopping:
                        break
                    # Get a connection.
                    if connection is None:
                        connection = self.getConnection(url)
                        if connection is None: # stopping
                            break
                    # Got an item, purge it!
                    try:
                        resp, msg, err = self.producer._purgeSync(connection,
                                                                 url, httpVerb)
                        # worked! See if we can leave the connection open for
                        # the next item we need to process
                        # NOTE: If we make a HTTP 1.0 request to IIS, it
                        # returns a HTTP 1.1 request and closes the
                        # connection.  It is not clear if IIS is evil for
                        # not returning a "connection: close" header in this
                        # case (ie, assuming HTTP 1.0 close semantics), or
                        # if httplib.py is evil for not detecting this
                        # situation and flagging will_close.
                        if not self.producer.http_1_1 or resp.will_close:
                            connection.close()
                            connection = None
                        break # all done with this item!

                    except (httplib.HTTPException, socket.error), e:
                        # All errors 'connection' related errors are treated
                        # the same - simply drop the connection and retry.
                        # the process for establishing the connection handles
                        # other bad things that go wrong.
                        logger.debug('Transient failure on %s for %s, '
                                     're-establishing connection and '
                                     'retrying: %s' % (httpVerb, url, e))
                        connection.close()
                        connection = None
                    except Exception:
                        # All other exceptions are evil - we just disard the
                        # item.  This prevents other logic failures etc being
                        # retried.
                        connection.close()
                        connection = None
                        logger.exception('Failed to purge %s', url)
                        break
        except:
            logger.exception('Exception in worker thread '
                             'for (%s, %s)' % (self.host, self.scheme))
        logger.debug("%s terminating", self)

    def getConnection(self, url):
        """Get a connection to the given URL.

        Blocks until either a connection is established, or we are asked to
        shut-down. Includes a simple strategy for slowing down the retry rate,
        retrying from 5 seconds to 20 seconds until the connection appears or
        we waited a full minute.
        """
        wait_time = 2.5
        while not self.stopping:
            try:
                return self.producer.getConnection(url)
            except socket.error as e:
                wait_time = int(min(wait_time * 2, 21))
                if wait_time > 20:
                    # we waited a full minute, we assume a permanent failure
                    logger.debug("Error %s connecting to %s - reconnect "
                                 "failed.", e, url)
                    self.stopping = True
                    break
                logger.debug("Error %s connecting to %s - will "
                             "retry in %d second(s)", e, url, wait_time)
                for i in xrange(wait_time):
                    if self.stopping:
                        break
                    time.sleep(1)
        return None # must be stopping!

DEFAULT_PURGER = DefaultPurger()


def stopThreads():
    purger = DEFAULT_PURGER
    purger.stopThreads()

from zope.testing.cleanup import addCleanUp
addCleanUp(stopThreads)
del addCleanUp
