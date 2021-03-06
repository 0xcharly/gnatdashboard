# GNAThub (GNATdashboard)
# Copyright (C) 2017, AdaCore
#
# This is free software;  you can redistribute it  and/or modify it  under
# terms of the  GNU General Public License as published  by the Free Soft-
# ware  Foundation;  either version 3,  or (at your option) any later ver-
# sion.  This software is distributed in the hope  that it will be useful,
# but WITHOUT ANY WARRANTY;  without even the implied warranty of MERCHAN-
# TABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for  more details.  You should have  received  a copy of the GNU
# General  Public  License  distributed  with  this  software;   see  file
# COPYING3.  If not, go to http://www.gnu.org/licenses for a complete copy
# of the license.

"""GNAThub plug-in for the SPARK2014 command-line tool.

It exports the SPARK2014 class which implements the :class:`GNAThub.Plugin`
interface. This allows GNAThub's plug-in scanner to automatically find this
module and load it as part of the GNAThub default execution.
"""

import GNAThub

import collections
import json
import os
import os.path
import re

from GNAThub import Console, Plugin, Reporter, Runner, ToolArgsPlaceholder

from _gnat import SLOC_PATTERN
from itertools import chain


class SPARK2014(Plugin, Runner, Reporter):
    """SPARK2014 plugin for GNAThub.

    Configures and executes GNATprove, then analyzes the output.
    """

    # Regex to identify lines that contain messages
    _MSG_PATTERN = \
        r'(?P<category>.+):\s(?P<message>.+)\[#(?P<msg_id>[0-9]+)\]$'

    # Regular expression to match GNATcheck output and extract all relevant
    # information stored in it.
    _MESSAGE = re.compile(r'%s:\s%s' % (SLOC_PATTERN, _MSG_PATTERN))

    def __init__(self):
        super(SPARK2014, self).__init__()

        self.tool = None

        self.output_dir = os.path.join(
            GNAThub.Project.object_dir(), 'gnatprove')
        self.output = os.path.join(
            GNAThub.Project.object_dir(), 'gnatprove-gnathub.out')

        # Map of message ID (couple (filename, msg_id): dict[*])
        self.msg_ids = {}

        # Map of rules (couple (name, rule): dict[str,Rule])
        self.rules = {}

        # Map of categories (couple (name, category): dict[str,Category])
        self.categories = {}

        # Map of messages (couple (rule, message): dict[str,Message])
        self.messages = {}

        # Map of bulk data (couple (source, message_data): dict[str,list])
        self.bulk_data = collections.defaultdict(list)

    @staticmethod
    def __cmd_line():
        """Create GNATprove command line arguments list.

        :return: the GNATprove command line
        :rtype: collections.Iterable[str]
        """
        return [
            'gnatprove', '-P', GNAThub.Project.path(), '--report=all',
            '-j', str(GNAThub.jobs())
        ] + GNAThub.Project.scenario_switches()

    @staticmethod
    def __msg_reader_cmd_line():
        """Create GNATprove Message Reader command line arguments list.

        :return: the GNATprove message reader command line
        :rtype: collections.Iterable[str]
        """

        return [
            'gnatprove', '-P', GNAThub.Project.path(), '--report=all',
            '-j', str(GNAThub.jobs()), '--output-msg-only',
            '--ide-progress-bar'
        ] + GNAThub.Project.scenario_switches()

    def run(self):
        """Execute GNATprove.

        Sets the exec_status property according to the success of the
        execution of the tool:

            * ``GNAThub.EXEC_SUCCESS``: on successful execution
            * ``GNAThub.EXEC_FAILURE``: on any error
        """

        return GNAThub.EXEC_SUCCESS if GNAThub.Run(
            self.name, self.__cmd_line()
        ).status == 0 else GNAThub.EXEC_FAILURE

    def report(self):
        """Execute GNATprove message reader and parses the output.

        Sets the exec_status property according to the success of the analysis:

            * ``GNAThub.EXEC_SUCCESS``: on successful execution and analysis
            * ``GNAThub.EXEC_FAILURE``: on any error
        """

        self.info('clear existing results if any')
        GNAThub.Tool.clear_references(self.name)

        self.info('extract results with msg_reader')
        proc = GNAThub.Run(
            self.name, self.__msg_reader_cmd_line(), out=self.output)

        if proc.status != 0:
            return GNAThub.EXEC_FAILURE

        self.info('analyse report')
        self.tool = GNAThub.Tool(self.name)

        self.log.debug('parse report: %s', self.output_dir)

        if not os.path.isdir(self.output_dir):
            self.error('no report found')
            return GNAThub.EXEC_FAILURE

        for entry in os.listdir(self.output_dir):
            filename, ext = os.path.splitext(entry)
            if not ext == '.spark':
                continue

            self.log.debug('parse file: %s', entry)
            try:
                with open(os.path.join(self.output_dir, entry), 'rb') as spark:
                    results = json.load(spark)
                    for record in chain(results['flow'], results['proof']):
                        if 'msg_id' not in record or 'file' not in record:
                            continue
                        self.log.debug('found record %s', json.dumps(record))

                        msg_id = record['msg_id']
                        filename = record['file']
                        self.msg_ids[(filename, msg_id)] = record

            except IOError as why:
                self.log.exception('failed to parse GNATprove .spark file')
                self.error('%s (%s:%d)' % (
                    why, os.path.basename(self.output), total))

        try:
            with open(self.output, 'rb') as fdin:
                # Compute the total number of lines for progress report
                lines = fdin.readlines()
                index, total = 0, len(lines)

                for index, line in enumerate(lines, start=1):
                    self.log.debug('parse line: %r', line)
                    match = self._MESSAGE.match(line)

                    if match:
                        self.log.debug('matched: %s', str(match.groups()))
                        self.__parse_line(match)

                    Console.progress(index, total, new_line=(index == total))

        except IOError as why:
            self.log.exception('failed to parse GNATprove output')
            self.error('%s (%s:%d)' % (
                why, os.path.basename(self.output), total))
            return GNAThub.EXEC_FAILURE

        else:
            self.__do_bulk_insert()
            return GNAThub.EXEC_SUCCESS

    def __parse_line(self, regex):
        """Parse a GNATprove message line.

        Adds the message to the current database session.

        Retrieves following information:

            * source basename
            * line in source
            * rule identification
            * message description

        :param re.RegexObject regex: the result of the _MESSAGE regex
        """

        filename = regex.group('file')
        src = GNAThub.Project.source_file(filename)
        line = regex.group('line')
        column = regex.group('column')
        message = regex.group('message')
        msg_id = regex.group('msg_id')
        category = regex.group('category').lower()

        record = self.msg_ids.get((filename, int(msg_id)))

        if record is None:
            self.log.warn(
                '%s: failed to get record for msg_id #%s', filename, msg_id)
            return

        rule_id = record['rule'].lower()
        self.__add_message(src, line, column, rule_id, message, category)

    def __add_message(self, src, line, column, rule_id, msg, category):
        """Add GNATprove message to current session database.

        :param str src: message source file
        :param str line: message line number
        :param str column: message column number
        :param str rule_id: message rule identifier
        :param str msg: description of the message
        :param str category: the category of the message
        """

        # Cache the rules
        if rule_id in self.rules:
            rule = self.rules[rule_id]
        else:
            rule = GNAThub.Rule(rule_id, rule_id, GNAThub.RULE_KIND, self.tool)
            self.rules[rule_id] = rule

        # Cache the categories
        if category in self.categories:
            cat = self.categories[category]
        else:
            cat = GNAThub.Category(category)
            self.categories[category] = cat

        # Cache the messages
        if (rule, msg, cat) in self.messages:
            message = self.messages[(rule, msg, cat)]
        else:
            message = GNAThub.Message(rule, msg, cat)
            self.messages[(rule, msg, cat)] = message

        # Add the message to the given resource
        self.bulk_data[src].append(
            [message, int(line), int(column), int(column)])

    def __do_bulk_insert(self):
        """Insert the codepeer messages in bulk on each resource."""

        for src in self.bulk_data:
            base = GNAThub.Project.source_file(os.path.basename(src))
            resource = GNAThub.Resource.get(base)

            if resource:
                resource.add_messages(self.bulk_data[src])
