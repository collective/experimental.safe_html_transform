import os
import shutil
import sys
import tempfile
import webbrowser
from unittest import TestCase

from createcoverage import script


executed = []


def mock_sys_exit(exit_code):
    raise RuntimeError("MOCK sys.exit(%s)" % exit_code)


def mock_webbrowser_open(path):
    global executed
    executed.append("Opened %s in webbrowser" % path)


def mock_system(command):
    global executed
    executed.append("Executed %s" % command)


class TestSystemCommand(TestCase):

    def setUp(self):
        self.orig_exit = sys.exit
        sys.exit = mock_sys_exit

    def tearDown(self):
        sys.exit = self.orig_exit

    def test_correct_command(self):
        script.system("more")

    def test_failing_command(self):
        self.assertRaises(RuntimeError, script.system, "non_existing_command")


class TestCoverage(TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.orig_dir = os.getcwd()
        self.orig_webbrowser_open = webbrowser.open
        webbrowser.open = mock_webbrowser_open
        self.orig_system = script.system
        script.system = mock_system
        os.chdir(self.tempdir)
        global executed
        executed = []
        self.orig_sysargv = sys.argv[1:]
        sys.argv[1:] = []

    def tearDown(self):
        webbrowser.open = self.orig_webbrowser_open
        script.system = self.orig_system
        os.chdir(self.orig_dir)
        shutil.rmtree(self.tempdir)
        sys.argv[1:] = self.orig_sysargv

    def test_missing_bin_test(self):
        self.assertRaises(RuntimeError, script.main)

    def test_missing_bin_coverage(self):
        bindir = os.path.join(self.tempdir, 'bin')
        testbinary = os.path.join(bindir, 'test')
        os.mkdir(bindir)
        open(testbinary, 'w').write('hello')
        script.main()
        self.assertTrue('Executed coverage run' in executed[0])

    def test_normal_run(self):
        bindir = os.path.join(self.tempdir, 'bin')
        testbinary = os.path.join(bindir, 'test')
        coveragebinary = os.path.join(bindir, 'coverage')
        os.mkdir(bindir)
        open(testbinary, 'w').write('hello')
        open(coveragebinary, 'w').write('hello')
        script.main()
        self.assertTrue('bin/coverage run' in executed[0])
        self.assertTrue(
            'bin/coverage html --directory=htmlcov' in executed[1])
        self.assertTrue('Opened' in executed[2])
        script.main()

    def test_options(self):
        bindir = os.path.join(self.tempdir, 'bin')
        testbinary = os.path.join(bindir, 'test')
        coveragebinary = os.path.join(bindir, 'coverage')
        os.mkdir(bindir)
        open(testbinary, 'w').write('hello')
        open(coveragebinary, 'w').write('hello')
        sys.argv[1:] = ['-v', '-d', 'output']
        script.main()
        self.assertTrue('bin/coverage run' in executed[0])
        self.assertTrue(
            'bin/coverage html --directory=output' in executed[1])
        self.assertTrue(len(executed), 1)  # No "opened in webbrowser"!
        script.main()

    def test_test_args(self):
        bindir = os.path.join(self.tempdir, 'bin')
        testbinary = os.path.join(bindir, 'test')
        coveragebinary = os.path.join(bindir, 'coverage')
        os.mkdir(bindir)
        open(testbinary, 'w').write('hello')
        open(coveragebinary, 'w').write('hello')
        sys.argv[1:] = ['-t', '-m dummy']
        script.main()
        self.assertTrue('bin/coverage run' in executed[0])
        self.assertTrue('{} -m dummy'.format(testbinary) in executed[0])
