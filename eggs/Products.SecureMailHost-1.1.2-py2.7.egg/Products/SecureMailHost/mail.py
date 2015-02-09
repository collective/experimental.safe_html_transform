##############################################################################
#
# Copyright (c) 2004 Christian Heimes and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL). A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
"""
from config import X_MAILER

import os, sys
import smtplib
import email.Message
import email.Utils
import socket
from DateTime import DateTime
from random import randint

from Products.MailHost.MailHost import MailHostError

ssl_support = False
if hasattr(socket, 'ssl'):
    ssl_support = True

class Mail:
    """A email object which knows how to send itself

    mfrom     - mail from tag (only for SMTP server)
    mto       - mail to tag (only for SMTP server)
    message   - The message email.Message.Message based object
    smtp_host - SMTP server address
    smtp_port - SMTP server port
    **kwargs  - additional keywords like userid, password and forceTLS
    """

    def __init__(self, mfrom, mto, message,
                 smtp_host='localhost', smtp_port=25,
                 **kwargs):
        self.mfrom = mfrom
        self.mto = mto
        # message must be email.Message.Message based
        assert(isinstance(message, email.Message.Message))
        # Add some important headers
        if not message.has_key('Date'):
            message['Date'] = DateTime().rfc822()
        if not message.has_key('X-Mailer'):
            message['X-Mailer'] = X_MAILER
        if not message.has_key('Message-Id'):
            fqdn = socket.getfqdn()
            message['Message-Id'] = email.Utils.make_msgid(fqdn)

        self.message = message

        self.host = smtp_host
        self.port = int(smtp_port)

        self.kwargs = kwargs
        self.errors = 0
        self.id = None

    def setId(self, id):
        """Set the unique id of the email
        """
        self.id = id

    def getId(self):
        """Get unique id
        """
        return self.id

    def incError(self):
        """Increase the error counter
        """
        self.errors+=1

    def getErrors(self):
        """Get the error counter
        """
        return self.errors

    def send(self, debug=False):
        """Send email to the SMTP server
        """
        kw = self.kwargs
        userid   = kw.get('userid', None)
        password = kw.get('password', None)
        forceTLS = kw.get('forcetls', False)
        noTLS    = kw.get('notls', False)
        message  = self.message.as_string()

        # connect
        if not self.host:
            raise MailHostError('No mailserver has been configured')

        smtpserver = smtplib.SMTP(self.host, self.port)
        if debug:
            smtpserver.set_debuglevel(1)

        # Try EHLO first, then HELO.
        if not (200 <= smtpserver.ehlo()[0] <= 299):
            (code, resp) = smtpserver.helo()
            if not (200 <= code <= 299):
                raise MailHostError('Host refused to talk to us: %s' % resp)

        # check for ssl encryption
        if smtpserver.has_extn('starttls') and ssl_support and not(noTLS):
            smtpserver.starttls()
            smtpserver.ehlo()
        elif forceTLS:
            if noTLS:
                raise MailHostError('Configured not to try TLS '
                    'but it is required')
            else:
                raise MailHostError('Host does NOT support StartTLS '
                    'but it is required')
        # login
        if smtpserver.does_esmtp:
            if userid:
                smtpserver.login(userid, password)
        elif userid:
            #indicate error here to prevent inadvertent use of spam relay
            raise MailHostError('Host does NOT support ESMTP '
                                'but username/password provided')
        # send and quit
        smtpserver.sendmail(self.mfrom, self.mto, message)
        smtpserver.quit()

    def __str__(self):
        return self.message.as_string()

    def __repr__(self):
        return '<%s (%s) at %s>' % (
            self.__class__.__name__, self.info(),
            id(self))

    def info(self):
        """Return status informations about the email
        """
        return ('From: %(from)s, To: %(to)s, Subject: %(subject)s '
                '(s:%(size)d, e:%(errors)d)' % {
            'id' : self.getId(), 'errors' : self.errors,
            'from' : self.message['From'], 'to' : self.message['To'],
            'subject' : self.message['Subject'], 'size' : len(self.message)
            })
