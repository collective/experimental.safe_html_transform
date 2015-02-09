import shutil
import tempfile

import zope.component.testing
import zope.configuration.xmlconfig


def setUp(test):
    zope.component.testing.setUp(test)

    import z3c.jbot
    zope.configuration.xmlconfig.XMLConfig('configure.zcml', z3c.jbot)()

    # enable five.pt if present
    try:
        import five.pt
    except ImportError:
        pass
    else:
        zope.configuration.xmlconfig.XMLConfig('configure.zcml', five.pt)()

    test.tempdir = tempfile.tempdir
    tempfile.tempdir = tempfile.mkdtemp()


def tearDown(test):
    zope.component.testing.tearDown(test)

    try:
        tempdir = test.tempdir
    except AttributeError:
        pass
    else:
        try:
            shutil.rmtree(tempfile.tempdir)
        finally:
            tempfile.tempdir = tempdir
