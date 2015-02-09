##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Queue processor thread

This module contains the queue processor thread.

$Id: queue.py 126451 2012-05-23 12:23:18Z tseaver $
"""
__docformat__ = 'restructuredtext'

import atexit
import ConfigParser
import logging
import os
import smtplib
import stat
import threading
import time

from zope.sendmail.maildir import Maildir
from zope.sendmail.mailer import SMTPMailer

import sys
if sys.platform == 'win32':
    import win32file
    _os_link = lambda src, dst: win32file.CreateHardLink(dst, src, None)
else:
    _os_link = os.link

# The longest time sending a file is expected to take.  Longer than this and
# the send attempt will be assumed to have failed.  This means that sending
# very large files or using very slow mail servers could result in duplicate
# messages sent.
MAX_SEND_TIME = 60*60*3

# The below diagram depicts the operations performed while sending a message in
# the ``run`` method of ``QueueProcessorThread``.  This sequence of operations
# will be performed for each file in the maildir each time the thread "wakes
# up" to send messages.
#
# Any error conditions not depected on the diagram will provoke the catch-all
# exception logging of the ``run`` method.
#
# In the diagram the "message file" is the file in the maildir's "cur" directory
# that contains the message and "tmp file" is a hard link to the message file
# created in the maildir's "tmp" directory.
#
#           ( start trying to deliver a message )
#                            |
#                            |
#                            V
#            +-----( get tmp file mtime )
#            |               |
#            |               | file exists
#            |               V
#            |         ( check age )-----------------------------+
#   tmp file |               |                       file is new |
#   does not |               | file is old                       |
#   exist    |               |                                   |
#            |      ( unlink tmp file )-----------------------+  |
#            |               |                      file does |  |
#            |               | file unlinked        not exist |  |
#            |               V                                |  |
#            +---->( touch message file )------------------+  |  |
#                            |                   file does |  |  |
#                            |                   not exist |  |  |
#                            V                             |  |  |
#            ( link message file to tmp file )----------+  |  |  |
#                            |                 tmp file |  |  |  |
#                            |           already exists |  |  |  |
#                            |                          |  |  |  |
#                            V                          V  V  V  V
#                     ( send message )             ( skip this message )
#                            |
#                            V
#                 ( unlink message file )---------+
#                            |                    |
#                            | file unlinked      | file no longer exists
#                            |                    |
#                            |  +-----------------+
#                            |  |
#                            |  V
#                  ( unlink tmp file )------------+
#                            |                    |
#                            | file unlinked      | file no longer exists
#                            V                    |
#                  ( message delivered )<---------+

class QueueProcessorThread(threading.Thread):
    """This thread is started at configuration time from the
    `mail:queuedDelivery` directive handler if processorThread is True.
    """

    log = logging.getLogger("QueueProcessorThread")
    _stopped = False
    interval = 3.0   # process queue every X second

    def __init__(self, interval=3.0):
        threading.Thread.__init__(self)
        self.interval = interval
        self._lock = threading.Lock()
        self.setDaemon(True)

    def setMaildir(self, maildir):
        """Set the maildir.

        This method is used just to provide a `maildir` stubs ."""
        self.maildir = maildir

    def setQueuePath(self, path):
        self.maildir = Maildir(path, True)

    def setMailer(self, mailer):
        self.mailer = mailer

    def _parseMessage(self, message):
        """Extract fromaddr and toaddrs from the first two lines of
        the `message`.

        Returns a fromaddr string, a toaddrs tuple and the message
        string.
        """

        fromaddr = ""
        toaddrs = ()
        rest = ""

        try:
            first, second, rest = message.split('\n', 2)
        except ValueError:
            return fromaddr, toaddrs, message

        if first.startswith("X-Zope-From: "):
            i = len("X-Zope-From: ")
            fromaddr = first[i:]

        if second.startswith("X-Zope-To: "):
            i = len("X-Zope-To: ")
            toaddrs = tuple(second[i:].split(", "))

        return fromaddr, toaddrs, rest

    def run(self, forever=True):
        atexit.register(self.stop)
        while not self._stopped:
            for filename in self.maildir:
                # if we are asked to stop while sending messages, do so
                if self._stopped:
                    break

                fromaddr = ''
                toaddrs = ()
                head, tail = os.path.split(filename)
                tmp_filename = os.path.join(head, '.sending-' + tail)
                rejected_filename = os.path.join(head, '.rejected-' + tail)
                try:
                    # perform a series of operations in an attempt to ensure
                    # that no two threads/processes send this message
                    # simultaneously as well as attempting to not generate
                    # spurious failure messages in the log; a diagram that
                    # represents these operations is included in a
                    # comment above this class
                    try:
                        # find the age of the tmp file (if it exists)
                        age = None
                        mtime = os.stat(tmp_filename)[stat.ST_MTIME]
                        age = time.time() - mtime
                    except OSError, e:
                        if e.errno == 2: # file does not exist
                            # the tmp file could not be stated because it
                            # doesn't exist, that's fine, keep going
                            pass
                        else:
                            # the tmp file could not be stated for some reason
                            # other than not existing; we'll report the error
                            raise

                    # if the tmp file exists, check it's age
                    if age is not None:
                        try:
                            if age > MAX_SEND_TIME:
                                # the tmp file is "too old"; this suggests
                                # that during an attemt to send it, the
                                # process died; remove the tmp file so we
                                # can try again
                                os.unlink(tmp_filename)
                            else:
                                # the tmp file is "new", so someone else may
                                # be sending this message, try again later
                                continue
                            # if we get here, the file existed, but was too
                            # old, so it was unlinked
                        except OSError, e:
                            if e.errno == 2: # file does not exist
                                # it looks like someone else removed the tmp
                                # file, that's fine, we'll try to deliver the
                                # message again later
                                continue

                    # now we know that the tmp file doesn't exist, we need to
                    # "touch" the message before we create the tmp file so the
                    # mtime will reflect the fact that the file is being
                    # processed (there is a race here, but it's OK for two or
                    # more processes to touch the file "simultaneously")
                    try:
                        os.utime(filename, None)
                    except OSError, e:
                        if e.errno == 2: # file does not exist
                            # someone removed the message before we could
                            # touch it, no need to complain, we'll just keep
                            # going
                            continue

                    # creating this hard link will fail if another process is
                    # also sending this message
                    try:
                        #os.link(filename, tmp_filename)
                        _os_link(filename, tmp_filename)
                    except OSError, e:
                        if e.errno == 17: # file exists, *nix
                            # it looks like someone else is sending this
                            # message too; we'll try again later
                            continue
                    except Exception, e:
                        if e[0] == 183 and e[1] == 'CreateHardLink':
                            # file exists, win32
                            continue

                    # read message file and send contents
                    file = open(filename)
                    message = file.read()
                    file.close()
                    fromaddr, toaddrs, message = self._parseMessage(message)
                    # The next block is the only one that is sensitive to
                    # interruptions.  Everywhere else, if this daemon thread
                    # stops, we should be able to correctly handle a restart.
                    # In this block, if we send the message, but we are
                    # stopped before we unlink the file, we will resend the
                    # message when we are restarted.  We limit the likelihood
                    # of this somewhat by using a lock to link the two
                    # operations.  When the process gets an interrupt, it
                    # will call the atexit that we registered (``stop``
                    # below).  This will try to get the same lock before it
                    # lets go.  Because this can cause the daemon thread to
                    # continue (that is, to not act like a daemon thread), we
                    # still use the _stopped flag to communicate.
                    self._lock.acquire()
                    try:
                        try:
                            self.mailer.send(fromaddr, toaddrs, message)
                        except smtplib.SMTPResponseException, e:
                            if 500 <= e.smtp_code <= 599:
                                # permanent error, ditch the message
                                self.log.error(
                                    "Discarding email from %s to %s due to"
                                    " a permanent error: %s",
                                    fromaddr, ", ".join(toaddrs), str(e))
                                #os.link(filename, rejected_filename)
                                _os_link(filename, rejected_filename)
                            else:
                                # Log an error and retry later
                                raise
                        except smtplib.SMTPRecipientsRefused, e:
                            # All recipients are refused by smtp
                            # server. Dont try to redeliver the message.
                            self.log.error("Email recipients refused: %s",
                                           ', '.join(e.recipients))
                            _os_link(filename, rejected_filename)

                        try:
                            os.unlink(filename)
                        except OSError, e:
                            if e.errno == 2: # file does not exist
                                # someone else unlinked the file; oh well
                                pass
                            else:
                                # something bad happend, log it
                                raise
                    finally:
                        self._lock.release()
                    try:
                        os.unlink(tmp_filename)
                    except OSError, e:
                        if e.errno == 2: # file does not exist
                            # someone else unlinked the file; oh well
                            pass
                        else:
                            # something bad happend, log it
                            raise

                    # TODO: maybe log the Message-Id of the message sent
                    self.log.info("Mail from %s to %s sent.",
                                  fromaddr, ", ".join(toaddrs))
                    # Blanket except because we don't want
                    # this thread to ever die
                except:
                    if fromaddr != '' or toaddrs != ():
                        self.log.error(
                            "Error while sending mail from %s to %s.",
                            fromaddr, ", ".join(toaddrs), exc_info=True)
                    else:
                        self.log.error(
                            "Error while sending mail : %s ",
                            filename, exc_info=True)
            else:
                if forever:
                    time.sleep(self.interval)

            # A testing plug
            if not forever:
                break

    def stop(self):
        self._stopped = True
        self._lock.acquire()
        self._lock.release()


def boolean(s):
    s = str(s).lower()
    return s.startswith("t") or s.startswith("y") or s.startswith("1")


def string_or_none(s):
    if s == 'None':
        return None
    return s


class ConsoleApp(object):
    """Allows running of Queue Processor from the console."""

    _usage = """%(script_name)s [OPTIONS] path/to/maildir

    OPTIONS:

        --daemon            Run in daemon mode, periodically checking queue
                            and sending messages.  Default is to send all
                            messages in queue once and exit.

        --interval <#secs>  How often to check queue when in daemon mode.
                            Default is 3 seconds.

        --hostname          Name of smtp host to use for delivery.  Default is
                            localhost.

        --port              Which port on smtp server to deliver mail to.
                            Default is 25.

        --username          Username to use to log in to smtp server.  Default
                            is none.

        --password          Password to use to log in to smtp server.  Must be
                            specified if username is specified.

        --force-tls         Do not connect if TLS is not available.  Not
                            enabled by default.

        --no-tls            Do not use TLS even if is available.  Not enabled
                            by default.

        --config <inifile>  Get configuration from specificed ini file; it must
                            contain a section [app:zope-sendmail].

    """

    _error = False
    daemon = False
    interval = 3
    hostname = 'localhost'
    port = 25
    username = None
    password = None
    force_tls = False
    no_tls = False
    queue_path = None

    def __init__(self, argv=sys.argv, verbose=True):
        self.script_name = argv[0]
        self.verbose = verbose
        self._process_args(argv[1:])
        self.mailer = SMTPMailer(self.hostname, self.port, self.username,
            self.password, self.no_tls, self.force_tls)

    def main(self):
        if self._error:
            return
        queue = QueueProcessorThread(self.interval)
        queue.setMailer(self.mailer)
        queue.setQueuePath(self.queue_path)
        queue.run(forever=self.daemon)

    def _process_args(self, args):
        got_queue_path = False
        while args:
            arg = args.pop(0)
            if arg == "--daemon":
                self.daemon = True
            elif arg == "--interval":
                try:
                    self.interval = float(args.pop(0))
                except:
                    self._error_usage()
            elif arg == "--hostname":
                if not args:
                    self._error_usage()
                self.hostname = args.pop(0)
            elif arg == "--port":
                try:
                    self.port = int(args.pop(0))
                except:
                    self._error_usage()
            elif arg == "--username":
                if not args:
                    self._error_usage()
                self.username = args.pop(0)
            elif arg == "--password":
                if not args:
                    self._error_usage()
                self.password = args.pop(0)
            elif arg == "--force-tls":
                self.force_tls = True
            elif arg == "--no-tls":
                self.no_tls = True
            elif arg == "--config":
                if not args:
                    self._error_usage()
                self._load_config(args.pop(0))
            elif arg.startswith("-") or got_queue_path:
                self._error_usage()
            else:
                self.queue_path = arg
                got_queue_path = True
        if not self.queue_path:
            self._error_usage()
        if (self.username or self.password) and \
           not (self.username and self.password):
            if self.verbose:
                print >>sys.stderr, "Must use username and password together."
            self._error = True
        if self.force_tls and self.no_tls:
            if self.verbose:
                print >>sys.stderr, \
                    "--force-tls and --no-tls are mutually exclusive."
            self._error = True

    def _load_config(self, path):
        section = "app:zope-sendmail"
        names = [
            "interval",
            "hostname",
            "port",
            "username",
            "password",
            "force_tls",
            "no_tls",
            "queue_path",
        ]
        defaults = dict([(name, str(getattr(self, name))) for name in names])
        config = ConfigParser.ConfigParser(defaults)
        config.read(path)
        self.interval = float(config.get(section, "interval"))
        self.hostname = config.get(section, "hostname")
        self.port = int(config.get(section, "port"))
        self.username = string_or_none(config.get(section, "username"))
        self.password = string_or_none(config.get(section, "password"))
        self.force_tls = boolean(config.get(section, "force_tls"))
        self.no_tls = boolean(config.get(section, "no_tls"))
        self.queue_path = string_or_none(config.get(section, "queue_path"))

    def _error_usage(self):
        if self.verbose:
            print >>sys.stderr, self._usage % {"script_name": self.script_name,}
        self._error = True


def run():
    logging.basicConfig()
    app = ConsoleApp()
    app.main()


if __name__ == "__main__":
    run_console()
