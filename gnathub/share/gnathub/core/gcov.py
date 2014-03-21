##############################################################################
##                                                                          ##
##                               G N A T h u b                              ##
##                                                                          ##
##                        Copyright (C) 2013, AdaCore                       ##
##                                                                          ##
## The QM is free software; you can redistribute it  and/or modify it       ##
## under terms of the GNU General Public License as published by the Free   ##
## Software Foundation; either version 3, or (at your option) any later     ##
## version.  The QM is distributed in the hope that it will be useful,      ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHAN-  ##
## TABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public ##
## License  for more details. You  should  have  received a copy of the GNU ##
## General Public License  distributed with the QM; see file COPYING3. If   ##
## not, write  to  the Free  Software  Foundation,  59 Temple Place - Suite ##
## 330, Boston, MA 02111-1307, USA.                                         ##
##                                                                          ##
##############################################################################

"""GNAThub plug-in for the Gcov command-line tool.

It exports the Gcov Python class which implements the GNAThub.Plugin interface.
This allows GNAThub's plug-in scanner to automatically find this module and
load it as part of the GNAThub default excecution.
"""

import GNAThub

import os

from GNAThub import Log
from GNAThub import db


class Gcov(GNAThub.Plugin):
    """Gcov plugin for GNAThub.

    Retrieves .gcov generated files from teh project root object directory,
    parses them and feeds the database with the data collected from each files.
    """

    TOOL_NAME = 'Gcov'
    GCOV_SUFFIX = '.gcov'

    def __init__(self):
        """Instance constructor."""

        super(Gcov, self).__init__()

    def display_command_line(self):
        """Inherited."""

        return ' '.join(['-P', GNAThub.Project.name()])

    def __add_line_hits(self, resource, line_num, hits):
        """Registers hits count for a specific line in the given file.

        PARAMETERS
            :param resource: the resource object for the file.
            :type resource: a GNAThub.Resource object.
            :param line_num: the line number in the file.
            :type line_num: a number.
            :param hits: the coverage hit for this line.
            :type hits: a string.
        """

        message = GNAThub.Message(self.rule, hits)
        resource.add_message(message, line_num)

    def __parse_gcov_report(self):
        """Analyses the report files generated by Gcov.

        Finds all .gcov files in the object directory and parses them.

        Sets the exec_status property according to the success of the
        analysis:

            GNAThub.EXEC_SUCCESS: on successful execution and analysis
            GNAThub.EXEC_FAIL: on any error
        """

        # Fetch all files in project object directory and retrieve only
        # .gcov files, absolute path
        files = [os.path.join(GNAThub.Project.object_dir(), filename)
                 for filename in os.listdir(GNAThub.Project.object_dir())
                 if filename.endswith(self.GCOV_SUFFIX)]

        # If no .gcov file found, plugin returns on failure
        if not files:
            Log.error('No gcov file found in project root object directory')
            self.exec_status = GNAThub.EXEC_FAIL
            return

        self.tool = GNAThub.Tool(self.name)
        self.rule = GNAThub.Rule('coverage', 'coverage', db.METRIC_KIND,
                                 self.tool)

        total = len(files)

        try:
            for index, filename in enumerate(files, start=1):
                # Retrieve source fullname
                base, _ = os.path.splitext(os.path.basename(filename))
                src = GNAThub.Project.source_file(base)

                resource = GNAThub.Resource.get(src)

                if resource:
                    with open(filename, 'r') as gcov_file:
                        # Retrieve information for every source line
                        # skip first 2 lines
                        for line in gcov_file.readlines()[2:]:

                            # Skip useless line
                            if line.strip()[0] != '-':
                                line_infos = line.split(':', 2)
                                hits = line_infos[0].strip()

                                # Line is not covered
                                if hits == '#####' or hits == '=====':
                                    hits = '0'

                                line_id = line_infos[1].strip()
                                self.__add_line_hits(resource, int(line_id),
                                                     hits)

                Log.progress(index, total, new_line=(index == total))

            self.exec_status = GNAThub.EXEC_SUCCESS

        except IOError as ex:
            Log.error('%s: %s' % (self.fqn, str(ex)))
            self.exec_status = GNAThub.EXEC_FAIL

    def execute(self):
        """Finds the Gcov output files and parses them."""

        Log.info('%s.parse: *%s' % (self.fqn, self.GCOV_SUFFIX))
        self.__parse_gcov_report()
