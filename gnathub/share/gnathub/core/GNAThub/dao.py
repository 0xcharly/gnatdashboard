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

import GPS

from db import Category, Line, Rule, Resource, Tool

## get_or_create_rule #########################################################
##
def get_or_create_rule(session, tool, kind, identifier, name=None):
    """Get rule for the given identifier if exists in the database, if it does
       not, create a new Rule objet in the given session. The rule is not
       persisted to the database. A session.commit() is required for that, this
       call is left for the one that manages the session.

       Parameters:
        - session: sqlachemy session
        - identifier: identifier of the rule
        - name: name of the rule
        - tool: tool which the rule is attached to
    """
    rule = session.query(Rule).filter_by(identifier=identifier, kind=kind).first()
    if not rule:
        if not name:
            name = identifier
        rule = Rule(identifier, name, tool, kind)
    return rule

## get_or_create_category #####################################################
##
def get_or_create_category(session, label):
    category = session.query(Category).filter_by(label=label).first()
    if not category:
        category = Category(label)
    return category

## get_file ###################################################################
##
def get_file(session, file_name):
    """Return the File object for the given file path """

    file = session.query(Resource)\
        .filter_by(kind=2)\
        .filter_by(name=GPS.File(file_name).name())\
        .first()
    return file

## get_file_by_id ##############################################################
##
def get_file_by_id(session, resource_id):
    """Return the File object for the given file path """
    file = session.query(Resource)\
        .filter_by(id=resource_id)\
        .first()
    return file

## get_resource ###############################################################
##
def get_resource(session, name):
    """Return the File object for the given file path """
    resource = session.query(Resource)\
        .filter(Resource.name.like('%' + name + '_'))\
        .first()
    return resource

## get_or_create_line #########################################################
##
def get_or_create_line(session, file_name, line_num):
    """Return the line object for the given file and line number
       Return None if file not in the DB
    """
    line = None
    if file_name:
        # Try to retrieve line from DB
        line = session.query(Line)\
            .filter_by(line=line_num)\
            .join(Line.resource)\
            .filter(Resource.name.like('%' + file_name))\
            .first()

        if not line:
            file = get_file(session, file_name)
            if file:
                line = Line(line_num, file)

    return line

## get_or_create_line #########################################################
##
def get_or_create_line_from_resource_id(session, resource_id, line_num):
    """Return the line object for the given file and line number
       Return None if file not in the DB
    """
    line = None
    if resource_id:
        # Try to retrieve line from DB
        line = session.query(Line)\
            .filter_by(line=line_num)\
            .join(Line.resource)\
            .filter(Resource.id==resource_id)\
            .first()

        # Create line if does not exist yet in DB
        if not line:
            file = get_file_by_id(session, resource_id)
            if file:
                line = Line(line_num, file)

    return line

## get_sub_project ############################################################
##
def get_sub_project(session, name):
    sub_project = session.query(Resource).filter_by(name=name, kind=0).first()

## save_tool ###################################################################
##
def save_tool(session, name):
   tool = Tool(name)
   session.add(tool)
   return tool
