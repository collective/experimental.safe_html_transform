=========================
 Local roles PAS plug-in
=========================

This PAS_ plug-in can be used to assign local roles in a particular context,
by adapter. It can be installed via the GenericSetup_ profile in this product.

  .. _PAS: http://www.zope.org/Products/PluggableAuthService
  .. _GenericSetup: http://www.zope.org/Products/GenericSetup

The plug-in should be installed when this doc-test is run. Please see
``workspace.py`` for more comprehensive tests.

    >>> 'borg_localroles' in self.portal.acl_users.objectIds()
    True
