##############################################################################
##                                                                          ##
##                               G N A T h u b                              ##
##                                                                          ##
##                     Copyright (C) 2013-2014, AdaCore                     ##
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

"""Helper module to factorize shared components between SonarConfig and
SonarRunner.
"""

import collections
import logging
import os

import GNAThub


class SonarQube(object):
    """Provides a set of helper static methods used by both the SonarQube
    Runner plug-in and the SonarConfig plug-in.

    """

    EXEC_DIRECTORY = 'sonar'
    CONFIGURATION = 'sonar-project.properties'

    @staticmethod
    def workdir():
        """Returns the sonar execution directory located within GNAThub's root
        directory:

            ``<project_object_dir>/gnathub/sonar``

        :return: The path to the working directory.
        :rtype: str

        """

        return os.path.join(GNAThub.root(), SonarQube.EXEC_DIRECTORY)

    @staticmethod
    def configuration():
        """Returns the path to the SonarQube Runner configuration file located
        in the Sonar-specific directory:

            ``<project_object_dir>/gnathub/sonar/sonar-project.properties``

        :return: The path to the configuration file.
        :rtype: str

        """

        return os.path.join(SonarQube.workdir(), SonarQube.CONFIGURATION)

    @staticmethod
    def make_workdir():
        """Creates the Sonar execution directory if it does not exist."""

        if not os.path.exists(SonarQube.workdir()):
            os.makedirs(SonarQube.workdir())


# pylint: disable=too-few-public-methods
class SonarRunnerProperties(object):
    """Builder object for the sonar-runner configuration file."""

    def __init__(self, logger=None):
        self.log = logger or logging.getLogger(self.__class__.__name__)
        self.attributes = collections.OrderedDict()

        # Generate the configuration
        self._generate()

    @staticmethod
    def _key(key, module=None):
        """Generates the full key.

        :param str key: Property key.
        :param str module: Module to which belongs the key. If ``None``, use
            the default sonar module.
        :return: The key.
        :rtype: str

        """

        return '%s.%s' % ('%s.sonar' % module if module else 'sonar', key)

    def _set(self, key, value, module=None):
        """Adds property in the sonar-runner configuration.

        :param str key: Property key.
        :param str value: Property value.
        :param str module: Module to which belongs the key. If ``None``, use
            the default sonar module.

        """

        self.attributes[SonarRunnerProperties._key(key, module)] = value

    def _set_dict(self, attributes, module=None):
        """Adds properties in the sonar-runner configuration.

        :param dict[str, str] attributes: Attributes to set.
        :param str module: Module to which belongs the key. If ``None``, use
            the default sonar module.

        """

        for key, value in attributes.iteritems():
            self.log.debug('%s = %s', key, value)
            self._set(key, value, module)

    def _set_project_customizable_dict(self, attributes, module=None):
        """Adds properties in the sonar-runner configuration.

        Those properties can be user-customizable via the project file.

        :param dict[str, (str, str)] attributes: Attributes to set.
        :param str module: Module to which belongs the key. If ``None``, use
            the default sonar module.

        """

        for key, value in attributes.iteritems():
            # Unpack the tuple containing the default value and the custom
            # project attribute for this key.
            value, attribute = value

            assert attribute, 'use SonarRunnerProperties._set_dict instead'
            project_property = GNAThub.Project.property_as_string(attribute)

            if project_property:
                self.log.debug('%s = %s (overriding default)', key, value)
            else:
                self.log.debug('%s = %s', key, value)

            self._set(key, project_property or value, module)

    def _get(self, key, module=None):
        """Returns the property in the sonar-runner configuration.

        :param str key: Property key.
        :param str module: Module to which belongs the key. If ``None``, use
            the default sonar module.
        :return: The value of the property ``key``.
        :rtype: str

        """

        return self.attributes.get(SonarRunnerProperties._key(key, module))

    def _generate(self):
        """Generates the content of the sonar-runner.properties file.

        Do not create the file yet. See :meth:`write` for this.

        """

        kwargs = {
            'db': GNAThub.database().replace('\\', '\\\\'),
            'project_name': GNAThub.Project.name(),
            'suffixes': [s[1:] if s.startswith('.') else s
                         for s in GNAThub.Project.source_suffixes('Ada')]
        }

        # pylint: disable=star-args
        if len(GNAThub.Project.source_dirs()) == 1:
            self._generate_single_module(**kwargs)
        else:
            self._generate_multi_module(**kwargs)

    @staticmethod
    def _generate_customizable_attr(project_name):
        """A dictionary of customizable attributes for the
        :file:`sonar-project.properties`.

        :param str project_name: The project name.
        :return: The attributes and their value.
        :rtype: collections.OrderedDict

        """

        return collections.OrderedDict([
            ('projectName', (project_name, 'Project_Name')),
            ('projectKey', (project_name, 'Project_Key')),
            ('projectVersion', ('unknown', 'Project_Version')),
            ('sourceEncoding', ('UTF-8', 'Source_Encoding'))
        ])

    def _generate_single_module(self, db_path, name, suffixes):
        """Generates the content of the sonar-runner.properties file.

        Do not create the file yet. See :meth:`write` for this.

        :param str db_path: Full path to the DB.
        :param str name: Project name.
        :param list[str] suffixes: List of Ada extensions.

        """

        project_source_dirs = GNAThub.Project.source_dirs()[name]

        non_customizable_attributes = collections.OrderedDict([
            ('language', 'ada'),
            ('sources', ','.join(project_source_dirs)),
            ('ada.gnathub.db', db_path),
            ('ada.file.suffixes', ','.join(suffixes))
        ])

        # Set project properties
        self._set_project_customizable_dict(
            SonarRunnerProperties._generate_customizable_attr(name))
        self._set_dict(non_customizable_attributes)

    def _generate_multi_module(self, db_path, name, suffixes):
        """Generates the content of the sonar-runner.properties file.

        Do not create the file yet. See :meth:`write` for this.

        :param str db_path: Full path to the DB.
        :param str name: Project name.
        :param list[str] suffixes: List of Ada extensions.

        """

        modules = {k: v for k, v in GNAThub.Project.source_dirs().items() if v}

        non_customizable_attributes = collections.OrderedDict([
            ('language', 'ada'),
            ('ada.gnathub.db', db_path),
            ('ada.file.suffixes', ','.join(suffixes)),
            ('modules', ','.join([m.lower() for m in modules.keys()]))
        ])

        # Set project properties
        self._set_project_customizable_dict(
            SonarRunnerProperties._generate_customizable_attr(name))
        self._set_dict(non_customizable_attributes)

        project_key = self._get('projectKey')

        # Set modules properties
        for subproject_name, sources in modules.iteritems():
            module_attributes = collections.OrderedDict([
                ('projectName', subproject_name),
                ('projectKey', '%s::%s' % (project_key, subproject_name)),
                ('projectBaseDir', os.path.commonprefix(sources)),
                ('sources', ','.join(sources))
            ])

            self._set_dict(module_attributes, module=subproject_name.lower())

    def write(self, filename):
        """Dumps sonar-project.properties in filename.

        :param str filename: The configuration file name.

        """

        with open(filename, 'w') as configuration:
            for key, value in self.attributes.iteritems():
                configuration.write('%s = %s\n' % (key, value))
