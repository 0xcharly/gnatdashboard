"""Check the integrity of the GNAThub Python module."""

import GNAThub

import os
import sys

# The base directory for PATH comparisons
BASEDIR = os.path.dirname(os.path.realpath(sys.argv[0]))


def relpath(path):
    """Returns the relative path to :param:`path` from BASEDIR.

    :param str path: The full path.
    :returns: str

    """

    return os.path.relpath(path, BASEDIR)


assert os.path.isdir(GNAThub.root()), '%s: no such directory' % GNAThub.root()
assert relpath(GNAThub.root()) == os.path.join('obj', 'gnathub'), 'unexpected value'

assert os.path.isdir(GNAThub.logs()), '%s: no such directory' % GNAThub.logs()
assert relpath(GNAThub.logs()) == os.path.join('obj', 'gnathub', 'logs'), \
    'unexpected value'

assert not GNAThub.verbose(), 'unexpected activated verbose mode'

assert os.path.isfile(GNAThub.database()), \
    '%s: no such file' % GNAThub.database()
assert relpath(GNAThub.database()) == \
    os.path.join('obj', 'gnathub', 'gnathub.db'), 'unexpected value'

# Default for jobs number is 0
assert GNAThub.jobs() == 0

# The plugin list is expected to be empty
assert len(GNAThub.plugins()) == 0

# We ensure that the core and extra plugins directories exist
repos = GNAThub.repositories()
for kind in ('system', 'global'):
    assert os.path.isdir(repos[kind]), '%s: no such directory' % repos[kind]

# GNAThub.run
TO_BE_ECHOED = 'this is the message to display on the standard output'

process = GNAThub.Run('echo', ['echo', TO_BE_ECHOED])

assert process.wait() == 0, 'process terminated unexpectedly'
assert process.status == 0, 'unexpected process exit code: %d' % process.status
assert process.name == 'echo', 'unexpected process name "%s"' % process.name
assert process.cmdline_image() == "echo '%s'" % TO_BE_ECHOED, \
    'unexpected process command-line image: ' + process.cmdline_image()
assert process.output() == os.path.join(GNAThub.logs(), 'echo.log'), \
    '%s: unexpected process log file' % process.output()

assert os.path.isfile(process.output()), '%s: no such file' % process.output()

with open(process.output(), 'r') as logs:
    content = logs.read().strip()
    assert content == TO_BE_ECHOED, 'unexpected process output: ' + content
