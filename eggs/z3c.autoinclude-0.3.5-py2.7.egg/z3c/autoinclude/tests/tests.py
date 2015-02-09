import os
import doctest
import unittest

from zc.buildout import testing

projects_dir = os.path.dirname(__file__)
    
# this is the list of test packages that we'll temporarily install
# for the duration of the tests; you MUST add your test package name
# to this list if you want it to be available for import in doctests!
test_packages = ['APackage', 'BCPackage', 'XYZPackage',
                 'SiblingPackage', 'BasePackage', 'FooPackage',
                 'base2', 'base2_plug', 'TestDirective',
                 'enolp.ppa.foo', 'enolp.ppa.bar']


from zc.buildout.easy_install import install
from pkg_resources import working_set
def install_projects(projects, target_dir):
    links = []
    for project in projects:
        project_dir = os.path.join(projects_dir, project)
        dist_dir = os.path.join(project_dir, 'dist')
        if os.path.isdir(dist_dir):
            testing.rmdir(dist_dir)
        dummy = testing.system("%s setup %s bdist_egg" % (
                os.path.join('bin', 'buildout'), project_dir))
        links.append(dist_dir)

    new_working_set = install(projects, target_dir, links=links,
                              working_set=working_set)

    # we must perform a magical incantation on each distribution
    for dist in new_working_set:
        dist.activate()
    return new_working_set


def interactive_testing_env():
    """ an interactive debugger with the testing environment set up for free """

    import tempfile
    target_dir = tempfile.mkdtemp('.z3c.autoinclude.test-installs')
    install_projects(test_packages, target_dir)
    import code
    code.interact()


def testSetUp(test):
    """
    install test packages so that they can be imported
    and their egg info examined in test runs
    """
    
    testing.buildoutSetUp(test)
    import tempfile
    target_dir = tempfile.mkdtemp('.z3c.autoinclude.test-installs')
    install_projects(test_packages, target_dir)


def testTearDown(test):
    from testdirective.zcml import clear_test_log
    clear_test_log()

    testing.buildoutTearDown(test)


IGNORECASE = doctest.register_optionflag('IGNORECASE')

class IgnoreCaseChecker(doctest.OutputChecker):
    def check_output(self, want, got, optionflags):
        if optionflags & IGNORECASE:
            want, got = want.lower(), got.lower()
            #print repr(want), repr(got), optionflags, IGNORECASE
        return doctest.OutputChecker.check_output(self, want, got, optionflags)

def test_suite():

    from pprint import pprint
    suite = doctest.DocFileSuite('../utils.txt',
                                 '../dependency.txt',
                                 '../plugin.txt',
                                 setUp=testSetUp,
                                 tearDown=testTearDown,
                                 globs={'pprint':pprint},
                                 checker=IgnoreCaseChecker(),
                                 optionflags=doctest.ELLIPSIS)

    return unittest.TestSuite((suite,))

if __name__ == '__main__':
    import zope.testing.testrunner
    zope.testing.testrunner.run([
  '--test-path', '/home/egj/z3c.autoinclude/src',
  ])
