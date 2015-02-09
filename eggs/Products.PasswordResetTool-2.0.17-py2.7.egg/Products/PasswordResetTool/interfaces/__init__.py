# Interface definitions
from zope.interface import Interface

class IPasswordResetToolView(Interface):
    """ BrowserView with utility methods """

    def encode_mail_header(text):
        """ Encodes text into correctly encoded email header """

    def encoded_mail_sender():
        """ returns encoded version of Portal name <portal_email> """

    def registered_notify_subject():
        """ returns encoded version of registered notify template subject line """

    def mail_password_subject():
        """ returns encoded version of mail password template subject line """
