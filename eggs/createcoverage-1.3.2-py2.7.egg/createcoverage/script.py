import logging
import optparse
import os
import subprocess
import sys
import webbrowser

MUST_CLOSE_FDS = not sys.platform.startswith('win')

logger = logging.getLogger(__name__)


def system(command, input=None):
    """commands.getoutput() replacement that also works on windows.

    Code mostly copied from zc.buildout.

    """
    logger.debug("Executing command: %s", command)
    p = subprocess.Popen(command,
                         shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         close_fds=MUST_CLOSE_FDS)
    stdoutdata, stderrdata = p.communicate(input=input)
    result = stdoutdata + stderrdata
    if p.returncode:
        logger.error("Something went wrong when executing '%s'",
                     command)
        logger.error("Returncode: %s", p.returncode)
        logger.error("Output:")
        logger.error(result)
        sys.exit(1)
    logger.info(result)


def main():
    """Create coverage reports and open them in the browser."""
    usage = "Usage: %prog PATH_TO_PACKAGE"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option(
        "-v", "--verbose",
        action="store_true", dest="verbose", default=False,
        help="Show debug output")
    parser.add_option(
        "-d", "--output-dir",
        action="store", type="string", dest="output_dir",
        default='',
        help="")
    parser.add_option(
        "-t", "--test-args",
        action="store", type="string", dest="test_args",
        default='',
        help=("Pass argument on to bin/test. Quote the argument, " +
              "for instance \"-t '-m somemodule'\"."))
    (options, args) = parser.parse_args()
    if options.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level,
                        format="%(levelname)s: %(message)s")

    curdir = os.getcwd()
    testbinary = os.path.join(curdir, 'bin', 'test')
    if not os.path.exists(testbinary):
        raise RuntimeError("Test command doesn't exist: %s" % testbinary)

    coveragebinary = os.path.join(curdir, 'bin', 'coverage')
    if not os.path.exists(coveragebinary):
        logger.debug("Trying globally installed coverage command.")
        coveragebinary = 'coverage'

    logger.info("Running tests in coverage mode (can take a long time)")
    parts = [coveragebinary, 'run', testbinary]
    if options.test_args:
        parts.append(options.test_args)
    system(" ".join(parts))
    logger.debug("Creating coverage reports...")
    if options.output_dir:
        coverage_dir = options.output_dir
        open_in_browser = False
    else:
        coverage_dir = 'htmlcov'  # The default
        open_in_browser = True
    system("%s html --directory=%s" % (coveragebinary, coverage_dir))
    logger.info("Wrote coverage files to %s", coverage_dir)
    if open_in_browser:
        index_file = os.path.abspath(
            os.path.join(coverage_dir, 'index.html'))
        logger.debug("About to open %s in your webbrowser.", index_file)
        webbrowser.open('file://' + index_file)
        logger.info("Opened reports in your browser.")
