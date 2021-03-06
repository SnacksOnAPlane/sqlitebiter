# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, unicode_literals

import simplesqlite
from sqliteschema import SQLiteSchemaExtractor


class TableCreator(object):
    def __init__(self, logger, dst_con, result_logger, verbosity_level):
        self.__logger = logger
        self.__dst_con = dst_con
        self.__result_logger = result_logger
        self.__verbosity_level = verbosity_level

        self.__schema_extractor = SQLiteSchemaExtractor(dst_con)

    def create(self, table_data, index_list, source_info):
        con_mem = simplesqlite.connect_memdb()
        con_mem.create_table_from_tabledata(table_data)
        need_rename = self.__require_rename_table(con_mem, table_data.table_name)
        src_table_name = con_mem.fetch_table_name_list()[0]
        dst_table_name = src_table_name

        if need_rename:
            dst_table_name = self.__make_unique_table_name(src_table_name)

            self.__logger.debug(
                "rename table from '{}' to '{}'".format(src_table_name, dst_table_name)
            )

            is_create_table = True
            simplesqlite.copy_table(
                src_con=con_mem,
                dst_con=self.__dst_con,
                src_table_name=src_table_name,
                dst_table_name=dst_table_name,
            )
        else:
            is_create_table = not self.__dst_con.has_table(dst_table_name)
            simplesqlite.append_table(
                src_con=con_mem, dst_con=self.__dst_con, table_name=dst_table_name
            )

        self.__dst_con.create_index_list(dst_table_name, index_list)

        self.__result_logger.logging_success(
            source_info.get_name(self.__verbosity_level), dst_table_name, is_create_table
        )

    def __require_rename_table(self, src_con, src_table_name):
        if not self.__dst_con.has_table(src_table_name):
            return False

        lhs = self.__schema_extractor.fetch_table_schema(src_table_name).as_dict()
        rhs = SQLiteSchemaExtractor(src_con).fetch_table_schema(src_table_name).as_dict()

        return lhs != rhs

    def __make_unique_table_name(self, table_name_base):
        exist_table_name_list = self.__dst_con.fetch_table_name_list()

        if table_name_base not in exist_table_name_list:
            return table_name_base

        suffix_id = 1
        while True:
            table_name_candidate = "{:s}_{:d}".format(table_name_base, suffix_id)

            if table_name_candidate not in exist_table_name_list:
                return table_name_candidate

            suffix_id += 1
