from os.path import dirname, join
from plone.app.imaging import tests


def getData(filename):
    """ return contents of the file with the given name """
    filename = join(dirname(tests.__file__), filename)
    return open(filename, 'r').read()
