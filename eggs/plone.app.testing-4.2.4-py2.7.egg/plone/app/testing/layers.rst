Plone testing layers
--------------------

There are various layers used to set up test fixtures containing a Plone
site. They are all importable from ``plone.app.testing`` directly, or from
their canonical locations at ``plone.app.testing.layers``.

    >>> from plone.app.testing import layers

For testing, we need a testrunner

    >>> from zope.testing.testrunner import runner

Plone site fixture
~~~~~~~~~~~~~~~~~~

The ``PLONE_FIXTURE`` layer extends ``STARTUP`` from ``plone.testing.z2`` to
set up a Plone site.

**Note:** This layer should only be used as a base layer, and not directly in
tests, since it does not manage the test lifecycle. To run a simple
integration test with this fixture, use the ``PLONE_INTEGRATION_TESTING``
layer described below. To run a simple functional test, use the
``PLONE_FUNCTIONAL_TESTING`` layer. Both of these have ``PLONE_FIXTURE`` as
a base. You can also extend ``PLONE_FIXTURE`` with your own fixture layer,
instantiating the ``IntegrationTesting`` or ``FunctionalTesting``classes
as appropriate. See this package's ``README`` file for details.

On layer setup, a new ``DemoStorage`` is stacked on top of the ``zodbDB``
resource (see ``plone.testing.zodb``). A fresh Plone with no default content
is created and added to the application root in this storage. The various
old-style products that Plone depends on are loaded, as is Plone's ZCML and
that of its direct dependencies. Before loading any ZCML, a new global
component registry is stacked on top of the default one (see
``plone.testing.zca``).

**Note**: A ZCML feature ``disable-autoinclude`` is set before Plone's ZCML is
loaded. This means that Plone will *not* automatically load the ZCML of
installed packages that use the ``z3c.autoinclude.plugin`` entry point. If you
want to use such packages, you should load their configuration explicitly.

Let's set up the fixture layer and inspect the state of the site.

    >>> options = runner.get_options([], [])
    >>> setupLayers = {}
    >>> runner.setup_layer(options, layers.PLONE_FIXTURE, setupLayers)
    Set up plone.testing.zca.LayerCleanup in ... seconds.
    Set up plone.testing.z2.Startup in ... seconds.
    Set up plone.app.testing.layers.PloneFixture in ... seconds.

The application root's ``acl_users`` folder will have one user, whose name and
password are found in the constants ``SITE_OWNER_NAME`` and
``SITE_OWNER_PASSWORD``, in ``plone.app.testing.interfaces``. This user
has the ``Manager`` role, and is the owner of the site object. You should not
normally use this for testing, unless you need to manipulate the site itself.

    >>> from plone.testing import z2, zca
    >>> from plone.app.testing.interfaces import SITE_OWNER_NAME

    >>> with z2.zopeApp() as app:
    ...     print app['acl_users'].getUser(SITE_OWNER_NAME)
    ...     print app['acl_users'].getUser(SITE_OWNER_NAME).getRolesInContext(app)
    admin
    ['Manager', 'Authenticated']

Inside the Plone site, the default theme is installed

    >>> from plone.app.testing import helpers
    >>> with helpers.ploneSite() as portal:
    ...     print portal['portal_skins'].getDefaultSkin()
    Sunburst Theme

**Note:** Here, we have used the ``ploneSite`` context manager to get hold of
the Plone site root. Like ``z2.zopeApp()``, this is intended for use during
layer setup and tear-down, and will automatically commit any changes unless an
error is raised.

There is one user, whose user id, login name name and password are found in the
constants ``TEST_USER_ID``, ``TEST_USER_NAME`` and ``TEST_USER_PASSWORD`` in
the module ``plone.app.testing.interfaces``.

    >>> from plone.app.testing.interfaces import TEST_USER_NAME
    >>> with helpers.ploneSite() as portal:
    ...     print portal['acl_users'].getUser(TEST_USER_NAME).getId()
    ...     print portal['acl_users'].getUser(TEST_USER_NAME).getUserName()
    ...     print portal['acl_users'].getUser(TEST_USER_NAME).getRolesInContext(portal)
    test_user_1_
    test-user
    ['Member', 'Authenticated']

There is no default workflow or content:

    >>> with helpers.ploneSite() as portal:
    ...     print portal['portal_workflow'].getDefaultChain()
    ()

Layer tear-down resets the environment.

    >>> runner.tear_down_unneeded(options, [], setupLayers)
    Tear down plone.app.testing.layers.PloneFixture in ... seconds.
    Tear down plone.testing.z2.Startup in ... seconds.
    Tear down plone.testing.zca.LayerCleanup in ... seconds.

Integration testing
~~~~~~~~~~~~~~~~~~~

``PLONE_INTEGRATION_TESTING`` can be used to run integration tests against the
fixture set up by the ``PLONE_FIXTURE`` layer.

    >>> "%s.%s" % (layers.PLONE_INTEGRATION_TESTING.__module__, layers.PLONE_INTEGRATION_TESTING.__name__,)
    'plone.app.testing.layers.Plone:Integration'

    >>> layers.PLONE_INTEGRATION_TESTING.__bases__
    (<Layer 'plone.app.testing.layers.PloneFixture'>,)

Let's set up the layers and attempt to run a test.

    >>> options = runner.get_options([], [])
    >>> setupLayers = {}
    >>> runner.setup_layer(options, layers.PLONE_INTEGRATION_TESTING, setupLayers)
    Set up plone.testing.zca.LayerCleanup in ... seconds.
    Set up plone.testing.z2.Startup in ... seconds.
    Set up plone.app.testing.layers.PloneFixture in ... seconds.
    Set up plone.app.testing.layers.Plone:Integration in ... seconds.

Let's now simulate a test

    >>> zca.LAYER_CLEANUP.testSetUp()
    >>> z2.STARTUP.testSetUp()
    >>> layers.PLONE_FIXTURE.testSetUp()
    >>> layers.PLONE_INTEGRATION_TESTING.testSetUp()

The portal is available as the resource ``portal``:

    >>> layers.PLONE_INTEGRATION_TESTING['portal'] # would normally be self.layer['portal']
    <PloneSite at /plone>

The local component site is set to the Plone site for the test:

    >>> from zope.component import getSiteManager
    >>> getSiteManager()
    <PersistentComponents /plone>

During the test, we are logged in as the test user:

    >>> from AccessControl import getSecurityManager
    >>> getSecurityManager().getUser()
    <PloneUser 'test-user'>

A new transaction is begun and aborted for each test, so we can create
content safely (so long as we don't commit):

    >>> from plone.app.testing.interfaces import TEST_USER_ID
    >>> portal = layers.PLONE_INTEGRATION_TESTING['portal'] # would normally be self.layer['portal']
    >>> helpers.setRoles(portal, TEST_USER_ID, ['Manager'])
    >>> portal.invokeFactory('Document', 'd1')
    'd1'
    >>> 'd1' in portal.objectIds()
    True

Let's now simulate test tear-down.

    >>> layers.PLONE_INTEGRATION_TESTING.testTearDown()
    >>> layers.PLONE_FIXTURE.testTearDown()
    >>> z2.STARTUP.testTearDown()
    >>> zca.LAYER_CLEANUP.testTearDown()

At this point, our transaction has been rolled back:

    >>> with helpers.ploneSite() as portal:
    ...     'd1' in portal.objectIds()
    False

We are also logged out again:

    >>> getSecurityManager().getUser()
    <SpecialUser 'Anonymous User'>

And the component site has been reset:

    >>> getSiteManager()
    <BaseGlobalComponents test-stack-2>

Layer tear-down resets the environment.

    >>> runner.tear_down_unneeded(options, [], setupLayers)
    Tear down plone.app.testing.layers.Plone:Integration in ... seconds.
    Tear down plone.app.testing.layers.PloneFixture in ... seconds.
    Tear down plone.testing.z2.Startup in ... seconds.
    Tear down plone.testing.zca.LayerCleanup in ... seconds.

Functional testing
~~~~~~~~~~~~~~~~~~

``PLONE_FUNCTIONAL_TESTING`` can be used to run functional tests against the
fixture set up by the ``PLONE_FIXTURE`` layer.

    >>> "%s.%s" % (layers.PLONE_FUNCTIONAL_TESTING.__module__, layers.PLONE_FUNCTIONAL_TESTING.__name__,)
    'plone.app.testing.layers.Plone:Functional'

    >>> layers.PLONE_FUNCTIONAL_TESTING.__bases__
    (<Layer 'plone.app.testing.layers.PloneFixture'>,)

Let's set up the layers and attempt to run a test.

    >>> options = runner.get_options([], [])
    >>> setupLayers = {}
    >>> runner.setup_layer(options, layers.PLONE_FUNCTIONAL_TESTING, setupLayers)
    Set up plone.testing.zca.LayerCleanup in ... seconds.
    Set up plone.testing.z2.Startup in ... seconds.
    Set up plone.app.testing.layers.PloneFixture in ... seconds.
    Set up plone.app.testing.layers.Plone:Functional in ... seconds.

Let's now simulate a test

    >>> zca.LAYER_CLEANUP.testSetUp()
    >>> z2.STARTUP.testSetUp()
    >>> layers.PLONE_FIXTURE.testSetUp()
    >>> layers.PLONE_FUNCTIONAL_TESTING.testSetUp()

    >>> layers.PLONE_FUNCTIONAL_TESTING['portal'] # would normally be self.layer['portal']
    <PloneSite at /plone>

    >>> from zope.component import getSiteManager
    >>> getSiteManager()
    <PersistentComponents /plone>

    >>> from AccessControl import getSecurityManager
    >>> getSecurityManager().getUser()
    <PloneUser 'test-user'>

A new ``DemoStorage`` is stacked for each test, so we can safely commit during
test execution.

    >>> portal = layers.PLONE_FUNCTIONAL_TESTING['portal'] # would normally be self.layer['portal']
    >>> helpers.setRoles(portal, TEST_USER_ID, ['Manager'])
    >>> portal.invokeFactory('Document', 'd1')
    'd1'
    >>> import transaction; transaction.commit()
    >>> 'd1' in portal.objectIds()
    True

Let's now simulate test tear-down.

    >>> layers.PLONE_FUNCTIONAL_TESTING.testTearDown()
    >>> layers.PLONE_FIXTURE.testTearDown()
    >>> z2.STARTUP.testTearDown()
    >>> zca.LAYER_CLEANUP.testTearDown()

The previous database state should have been restored.

    >>> with helpers.ploneSite() as portal:
    ...     'd1' in portal.objectIds()
    False

Along with the rest of the state:

    >>> getSecurityManager().getUser()
    <SpecialUser 'Anonymous User'>

    >>> getSiteManager()
    <BaseGlobalComponents test-stack-2>

Layer tear-down resets the environment.

    >>> runner.tear_down_unneeded(options, [], setupLayers)
    Tear down plone.app.testing.layers.Plone:Functional in ... seconds.
    Tear down plone.app.testing.layers.PloneFixture in ... seconds.
    Tear down plone.testing.z2.Startup in ... seconds.
    Tear down plone.testing.zca.LayerCleanup in ... seconds.

HTTP server
~~~~~~~~~~~

The ``PLONE_ZSERVER`` layer instantiates the ``FunctionalTesting`` class with
two bases: ``PLONE_FIXTURE``, as shown above, and ``ZSERVER_FIXTURE`` from
``plone.testing``, which starts up a ZServer thread.

    >>> "%s.%s" % (layers.PLONE_ZSERVER.__module__, layers.PLONE_ZSERVER.__name__,)
    'plone.app.testing.layers.Plone:ZServer'

    >>> layers.PLONE_ZSERVER.__bases__
    (<Layer 'plone.app.testing.layers.PloneFixture'>, <Layer 'plone.testing.z2.ZServer'>)

    >>> options = runner.get_options([], [])
    >>> setupLayers = {}
    >>> runner.setup_layer(options, layers.PLONE_ZSERVER, setupLayers)
    Set up plone.testing.zca.LayerCleanup in ... seconds.
    Set up plone.testing.z2.Startup in ... seconds.
    Set up plone.app.testing.layers.PloneFixture in ... seconds.
    Set up plone.testing.z2.ZServer in ... seconds.
    Set up plone.app.testing.layers.Plone:ZServer in ... seconds.

After layer setup, the resources ``host`` and ``port`` are available, and
indicate where Zope is running.

    >>> host = layers.PLONE_ZSERVER['host']
    >>> host
    'localhost'

    >>> port = layers.PLONE_ZSERVER['port']
    >>> import os
    >>> port == int(os.environ.get('ZSERVER_PORT', 55001))
    True

Let's now simulate a test. Test setup does nothing beyond what the base layers
do.

    >>> zca.LAYER_CLEANUP.testSetUp()
    >>> z2.STARTUP.testSetUp()
    >>> layers.PLONE_FIXTURE.testSetUp()
    >>> z2.ZSERVER_FIXTURE.testSetUp()
    >>> layers.PLONE_ZSERVER.testSetUp()

It is common in a test to use the Python API to change the state of the server
(e.g. create some content or change a setting) and then use the HTTP protocol
to look at the results. Bear in mind that the server is running in a separate
thread, with a separate security manager, so calls to ``helpers.login()`` and
``helpers.logout()``, for instance, do not affect the server thread.

    >>> portal = layers.PLONE_ZSERVER['portal'] # would normally be self.layer['portal']
    >>> helpers.setRoles(portal, TEST_USER_ID, ['Manager'])
    >>> portal.invokeFactory('Folder', 'folder1', title=u"Folder 1")
    'folder1'

Note that we need to commit the transaction before it will show up in the
other thread.

    >>> import transaction; transaction.commit()

We can now look for this new object through the server.

    >>> portal_url = portal.absolute_url()
    >>> portal_url.split(':')[:-1]
    ['http', '//localhost']

    >>> import urllib2
    >>> conn = urllib2.urlopen(portal_url + '/folder1', timeout=10)
    >>> responseBody = conn.read()
    >>> "Folder 1" in responseBody
    True
    >>> conn.close()

Test tear-down does nothing beyond what the base layers do.

    >>> layers.PLONE_ZSERVER.testTearDown()
    >>> z2.ZSERVER_FIXTURE.testTearDown()
    >>> layers.PLONE_FIXTURE.testTearDown()
    >>> z2.STARTUP.testTearDown()
    >>> zca.LAYER_CLEANUP.testTearDown()

    >>> 'portal' in layers.PLONE_ZSERVER
    False

    >>> 'app' in layers.PLONE_ZSERVER
    False

    >>> 'request' in layers.PLONE_ZSERVER
    False

    >>> with helpers.ploneSite() as portal:
    ...     print 'folder1' in portal.objectIds()
    False

When the server is torn down, the ZServer thread is stopped.

    >>> runner.tear_down_unneeded(options, [], setupLayers)
    Tear down plone.app.testing.layers.Plone:ZServer in ... seconds.
    Tear down plone.app.testing.layers.PloneFixture in ... seconds.
    Tear down plone.testing.z2.ZServer in ... seconds.
    Tear down plone.testing.z2.Startup in ... seconds.
    Tear down plone.testing.zca.LayerCleanup in ... seconds.

    >>> conn = urllib2.urlopen(portal_url + '/folder1', timeout=5)
    Traceback (most recent call last):
    ...
    URLError: <urlopen error [Errno ...] Connection refused>

FTP server with Plone site
~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``PLONE_FTP_SERVER`` layer instantiates the ``FunctionalTesting`` class
with two bases: ``PLONE_FIXTURE``, as shown above, and ``FTP_SERVER_FIXTURE``
from ``plone.testing``, which starts up an FTP server thread.

    >>> "%s.%s" % (layers.PLONE_FTP_SERVER.__module__, layers.PLONE_FTP_SERVER.__name__,)
    'plone.app.testing.layers.Plone:FTPServer'

    >>> layers.PLONE_FTP_SERVER.__bases__
    (<Layer 'plone.app.testing.layers.PloneFixture'>, <Layer 'plone.testing.z2.FTPServer'>)

    >>> options = runner.get_options([], [])
    >>> setupLayers = {}
    >>> runner.setup_layer(options, layers.PLONE_FTP_SERVER, setupLayers)
    Set up plone.testing.zca.LayerCleanup in ... seconds.
    Set up plone.testing.z2.Startup in ... seconds.
    Set up plone.app.testing.layers.PloneFixture in ... seconds.
    Set up plone.testing.z2.FTPServer in ... seconds.
    Set up plone.app.testing.layers.Plone:FTPServer in ... seconds.

After layer setup, the resources ``host`` and ``port`` are available, and
indicate where Zope is running.

    >>> host = layers.PLONE_FTP_SERVER['host']
    >>> host
    'localhost'

    >>> port = layers.PLONE_FTP_SERVER['port']
    >>> port
    55002

Let's now simulate a test. Test setup does nothing beyond what the base layers
do.

    >>> zca.LAYER_CLEANUP.testSetUp()
    >>> z2.STARTUP.testSetUp()
    >>> layers.PLONE_FIXTURE.testSetUp()
    >>> z2.FTP_SERVER_FIXTURE.testSetUp()
    >>> layers.PLONE_FTP_SERVER.testSetUp()

It is common in a test to use the Python API to change the state of the server
(e.g. create some content or change a setting) and then use the FTP protocol
to look at the results. Bear in mind that the server is running in a separate
thread, with a separate security manager, so calls to ``helpers.login()`` and
``helpers.logout()``, for instance, do not affect the server thread.

    >>> portal = layers.PLONE_FTP_SERVER['portal'] # would normally be self.layer['portal']
    >>> helpers.setRoles(portal, TEST_USER_ID, ['Manager'])
    >>> portal.invokeFactory('Folder', 'folder1')
    'folder1'

Note that we need to commit the transaction before it will show up in the
other thread.

    >>> import transaction; transaction.commit()

    >>> folder_path = portal.absolute_url_path() + '/folder1'

    >>> import ftplib
    >>> ftpClient = ftplib.FTP()
    >>> ftpClient.connect(host, port, timeout=5)
    '220 ... FTP server (...) ready.'

    >>> from plone.app.testing.interfaces import SITE_OWNER_NAME
    >>> from plone.app.testing.interfaces import SITE_OWNER_PASSWORD

    >>> ftpClient.login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
    '230 Login successful.'

    >>> ftpClient.cwd(folder_path)
    '250 CWD command successful.'

    >>> ftpClient.retrlines('LIST')
    drwxrwx---   1 test_user_1_ Zope            0 ... .
    d---------   1 admin        Zope            0 ... ..
    '226 Transfer complete'

    >>> ftpClient.quit()
    '221 Goodbye.'

Test tear-down does nothing beyond what the base layers do.

    >>> layers.PLONE_FTP_SERVER.testTearDown()
    >>> z2.FTP_SERVER_FIXTURE.testTearDown()
    >>> layers.PLONE_FIXTURE.testTearDown()
    >>> z2.STARTUP.testTearDown()
    >>> zca.LAYER_CLEANUP.testTearDown()

    >>> 'portal' in layers.PLONE_FTP_SERVER
    False

    >>> 'app' in layers.PLONE_FTP_SERVER
    False

    >>> 'request' in layers.PLONE_FTP_SERVER
    False

    >>> with helpers.ploneSite() as portal:
    ...     print 'folder1' in portal.objectIds()
    False

When the server is torn down, the FTP server thread is stopped.

    >>> runner.tear_down_unneeded(options, [], setupLayers)
    Tear down plone.app.testing.layers.Plone:FTPServer in ... seconds.
    Tear down plone.app.testing.layers.PloneFixture in ... seconds.
    Tear down plone.testing.z2.FTPServer in ... seconds.
    Tear down plone.testing.z2.Startup in ... seconds.
    Tear down plone.testing.zca.LayerCleanup in ... seconds.

    >>> ftpClient.connect(host, port, timeout=5)
    Traceback (most recent call last):
    ...
    error: [Errno ...] Connection refused
