=================================
Translations For aws.zope2zcmldoc
=================================

The updatelocales.py script rebuilds the .pot files and synchronizes the
.po files.

Requirements
============

Of course, we assume that you know basics about Zope 3 style
internationalisation and localisation, as well as the gettext standard (.po
files, ...) otherwise, ask Google.

You need i18ndude (from the cheeseshop) to run this script. As installing
i18ndude makes a huge mess in the standard Python "site-packages" that may
conflict with the Zope bundle, it is strongly recommanded to install i18ndude in
a dedicated virtualenv::

  $ easy_install virtualenv
    ...
  $ cd /where/you/want
  $ virtualenv --no-site-packages i18ndude
  $ cd i18ndude
  $ . bin/activate
  (i18ndude)$ easy_install i18ndude
    ...

You're done. In the future, you'll need to activate that virtualenv
before running i18ndude or updatelocales.py. After you're done, you might
run::

  $ deactivate

...to leave the virtual Python environment for i18ndude

Updating the catalogs
=====================

First, edit the "updatelocales.py" file and fix "PLONEPOTPATH" value as
described in the comment. No do not "svn commit" this ;o)

i18ndude cannot find all msgids. After changing Python code or
templates, you may need to run::

  $ . /where/you/want/i18ndude/bin/activate
  (i18ndude)$ cd .../aws.zope2zcmldoc/locales
  (i18ndude)$ python updatelocales.py

If some msgids are missing from the synched ".po" files, you may need to add
these msgids to "aws.zope2zcmldoc-manual.pot" (for 'aws.zope2zcmldoc'
domain). Then re-run the above commands.

Having aws.zope2zcmldoc in your language
===================================

Let's say your language nick is "xx" as "fr" stands for "French".

Easy::

  $ cd .../aws.zope2zcmldoc/iw/sitestat/locales # Here ;)
  $ mkdir -p xx/LC_MESSAGES
  $ cp aws.zope2zcmldoc.pot xx/LC_MESSAGES/aws.zope2zcmldoc.po
  $ $EDITOR xx/LC_MESSAGES/aws.zope2zcmldoc.po

Fill the metadata and msgstrs of your catalog. When ready::

  $ . /where/you/want/i18ndude/bin/activate
  (i18ndude)$ python updatelocales.py

Don't forget to add that new directory to the subversion reposo if you got
aws.zope2zcmldoc with a subversion checkout.

More information
================

* http://pypi.python.org/pypi/virtualenv
* http://pypi.python.org/pypi/i18ndude
