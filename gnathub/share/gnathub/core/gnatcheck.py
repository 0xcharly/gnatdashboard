############################################################################
#                                                                          #
#                               G N A T h u b                              #
#                                                                          #
#                     Copyright (C) 2013-2014, AdaCore                     #
#                                                                          #
# This is free software;  you can redistribute it  and/or modify it  under #
# terms of the  GNU General Public License as published  by the Free Soft- #
# ware  Foundation;  either version 3,  or (at your option) any later ver- #
# sion.  This software is distributed in the hope  that it will be useful, #
# but WITHOUT ANY WARRANTY;  without even the implied warranty of MERCHAN- #
# TABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public #
# License for  more details.  You should have  received  a copy of the GNU #
# General  Public  License  distributed  with  this  software;   see  file #
# COPYING3.  If not, go to http://www.gnu.org/licenses for a complete copy #
# of the license.                                                          #
#                                                                          #
############################################################################

"""GNAThub plug-in for the GNATcheck command-line tool

It exports the GNATcheck class which implements the :class:`GNAThub.Plugin`
interface. This allows GNAThub's plug-in scanner to automatically find this
module and load it as part of the GNAThub default execution.
"""

import os
import re

from _gnat import SLOC_PATTERN

import GNAThub
from GNAThub import Console


class GNATcheck(GNAThub.Plugin):
    """GNATcheck plugin for GNAThub

    Configures and executes GNATcheck, then analyzes the output.
    """

    # Regex to identify lines that contain messages
    _RULE_PATTERN = r'(?P<message>.+)\s\[(?P<rule>[A-Za-z_]+)\]$'

    # Regular expression to match GNATcheck output and extract all relevant
    # information stored in it.
    _MESSAGE = re.compile(r'%s:\s%s' % (SLOC_PATTERN, _RULE_PATTERN))

    # GNATcheck exits with an error code of 1 even on a successful run
    VALID_EXIT_CODES = (0, 1)

    def __init__(self):
        super(GNATcheck, self).__init__()

        self.tool = None
        self.report = os.path.join(GNAThub.Project.object_dir(),
                                   '%s.out' % self.name)

    def __cmd_line(self):
        """Creates GNATcheck command line arguments list

        :return: the GNATcheck command line
        :rtype: list[str]
        """

        return ['gnatcheck', '--show-rule', '-o', self.report,
                '-P', GNAThub.Project.path(),
                '-j%d' % GNAThub.jobs()] + GNAThub.Project.scenario_switches()

    def execute(self):
        """Executes GNATcheck

        :meth:`postprocess()` is called upon process completion.
        """

        proc = GNAThub.Run(self.name, self.__cmd_line())
        self.postprocess(proc.status)

    def postprocess(self, exit_code):
        """Parses the output report if GNATcheck completed successfully

        Sets the ``exec_status`` property according to the success of the
        analysis:

            * ``GNAThub.EXEC_SUCCESS``: on successful execution and analysis
            * ``GNAThub.EXEC_FAILURE``: on any error
        """

        if exit_code not in GNATcheck.VALID_EXIT_CODES:
            self.exec_status = GNAThub.EXEC_FAILURE
            return

        self.__parse_report()

    def __parse_report(self):
        """Parses GNATcheck output file report

        Sets the exec_status property according to the success of the
        analysis:

            * ``GNAThub.EXEC_SUCCESS``: on successful execution and analysis
            * ``GNAThub.EXEC_FAILURE``: on any error

        Identify two type of messages with different format:

            * basic message
            * message for package instantiation
        """

        self.info('analyse report')

        self.tool = GNAThub.Tool(self.name)
        self.log.debug('parse report: %s', self.report)

        if not os.path.exists(self.report):
            self.exec_status = GNAThub.EXEC_FAILURE
            self.error('no report found')
            return

        try:
            with open(self.report, 'r') as output:
                lines = output.readlines()
                total = len(lines)

                for index, line in enumerate(lines, start=1):
                    self.log.debug('parse line: %s', line)

                    match = self._MESSAGE.match(line)

                    if match:
                        self.log.debug('matched: %s', str(match.groups()))
                        self.__parse_line(match)

                    Console.progress(index, total, new_line=(index == total))

        except IOError as why:
            self.exec_status = GNAThub.EXEC_FAILURE
            self.log.exception('failed to parse GNATcheck report')
            self.error(str(why))

        else:
            self.exec_status = GNAThub.EXEC_SUCCESS

    def __parse_line(self, regex):
        """Parses a GNATcheck message line

        Add the message to the current database session.

        Retrieves following information:

            * source basename
            * line in source
            * rule identification
            * message description

        :param regex: the result of the MSG_RE regex
        :type regex: re.RegexObject
        """

        # The following Regex results are explained using this example.
        # 'input.adb:3:19: use clause for package [USE_PACKAGE_Clauses]'

        # Extract each component from the message:
        #       ('input.adb', '3', '19', 'use clause for package',
        #        'USE_PACKAGE_Clauses')
        base = regex.group('file')
        src = GNAThub.Project.source_file(base)
        line = regex.group('line')
        column = regex.group('column')
        message = regex.group('message')
        rule = regex.group('rule')

        self.__add_message(src, line, column, rule, message)

    def __add_message(self, src, line, col_begin, rule_id, msg):
        """Adds GNATcheck message to current session database

        :param src: Message source file.
        :type src: str
        :param line: Message line number.
        :type line: str
        :param col_begin: Message column number.
        :type col_begin: str
        :param rule_id: Message's rule identifier.
        :type rule_id: str
        :param msg: Description of the message.
        :type msg: str
        """

        rule = GNAThub.Rule(rule_id, rule_id, GNAThub.RULE_KIND, self.tool)
        message = GNAThub.Message(rule, msg)
        resource = GNAThub.Resource.get(src)

        if resource:
            resource.add_message(message, int(line), int(col_begin))
