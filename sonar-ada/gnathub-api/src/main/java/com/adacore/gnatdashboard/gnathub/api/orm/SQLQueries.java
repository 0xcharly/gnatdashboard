/*
 * GNAThub API (GNATdashboard)
 * Copyright (C) 2016, AdaCore
 *
 * This is free software;  you can redistribute it  and/or modify it  under
 * terms of the  GNU General Public License as published  by the Free Soft-
 * ware  Foundation;  either version 3,  or (at your option) any later ver-
 * sion.  This software is distributed in the hope  that it will be useful,
 * but WITHOUT ANY WARRANTY;  without even the implied warranty of MERCHAN-
 * TABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
 * License for  more details.  You should have  received  a copy of the GNU
 * General  Public  License  distributed  with  this  software;   see  file
 * COPYING3.  If not, go to http://www.gnu.org/licenses for a complete copy
 * of the license.
 */

package com.adacore.gnatdashboard.gnathub.api.orm;

/**
 * Generates SQL queries for the Project database.
 */
public class SQLQueries {
  /**
   * Prevents creation of SQLQueries instances.
   */
  private SQLQueries() {
  }

  /**
   * Crafts the SQL query to fetch all resources.
   *
   * @return The SQL query to use to fetch all resources from the database.
   */
  public static String allResources() {
    return BASE_RESOURCE_QUERY;
  }

  /**
   * Crafts the SQL query to fetch all issues.
   *
   * @return The SQL query to use to fetch all issues from the database.
   */
  public static String allIssues() {
    return BASE_ISSUE_QUERY;
  }

  /**
   * Crafts the SQL query to fetch one file by its ID.
   *
   * @param resourceId The file ID.
   * @return The SQL query to fetch that file.
   */
  public static String resourceById(final Integer resourceId) {
    return String.format(RESOURCE_BY_ID, resourceId);
  }

  /**
   * Crafts the SQL query to fetch the list of measures saved by a given tool.
   *
   * @param toolName The name of the tool.
   * @return The SQL query to use to fetch measures from this tool.
   */
  public static String measuresByTool(final String toolName) {
    return String.format(MEASURES_PER_TOOL, toolName) + " ORDER BY (file.id)";
  }

  private final static String BASE_RESOURCE_QUERY = String.format(
      "SELECT "
          + "file.name as path, "
          + "dir.name as directory, "
          + "prj.name as project "
          + "FROM "
          + "resources file, resources dir, resources prj, "
          + "resource_trees tree_file, resource_trees tree_dir "
          + "WHERE "
          + "file.kind = %d AND dir.kind = %d AND prj.kind = %d "
          + "AND file.id = tree_file.child_id AND dir.id = tree_file.parent_id "
          + "AND dir.id = tree_dir.child_id AND prj.id = tree_dir.parent_id",
      ResourceKind.FILE.img, ResourceKind.DIRECTORY.img,
      ResourceKind.PROJECT.img);

  private final static String RESOURCE_BY_ID =
      BASE_RESOURCE_QUERY + " AND file.id = %d";

  private final static String BASE_MEASURE_QUERY = String.format(
      "SELECT "
          + "file.name as path, "
          + "msg.data as value, "
          + "rule.identifier as key "
          + "FROM "
          + "resources file, resources_messages rm, "
          + "rules rule, tools tool, messages msg "
          + "WHERE "
          + "rm.line = 0 AND file.kind = %d AND file.id = rm.resource_id "
          + "AND msg.id = rm.message_id AND rule.tool_id = tool.id "
          + "AND msg.rule_id = rule.id AND rule.kind = %d",
      ResourceKind.FILE.img, RuleKind.MEASURE.img);

  private final static String MEASURES_PER_TOOL =
      BASE_MEASURE_QUERY + " AND LOWER(tool.name) = LOWER('%s')";

  private final static String BASE_ISSUE_QUERY = String.format(
      "SELECT "
          + "file.name as path, "
          + "msg.data as message, "
          + "rule.identifier as key, "
          + "REPLACE(LOWER(tool.name), ' ', '') as tool_name, "
          + "rm.line as line_no, "
          + "c.label as category "
          + "FROM "
          + "resources_messages rm, rules rule, tools tool, "
          + "messages msg, resources file "
          + "LEFT OUTER JOIN "
          + "categories c ON msg.category_id = c.id "
          + "WHERE "
          + "msg.rule_id = rule.id AND rm.message_id = msg.id "
          + "AND rule.tool_id = tool.id AND rm.resource_id = file.id "
          + "AND rule.kind = %d", RuleKind.ISSUE.img);
}