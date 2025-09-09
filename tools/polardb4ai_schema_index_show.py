from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from mysql.connector import connect, Error

from re import compile, IGNORECASE, DOTALL, VERBOSE

enable_write = False
enable_update = False
enable_insert = False
enable_ddl = True

class Polardb4aiSchemaIndexTool(Tool):
    def get_sql_operation_type(self, sql):
        """
        使用正则表达式判断 SQL 操作类型
        :param sql: 输入 SQL 语句
        :return: 返回操作类型 ('INSERT', 'DELETE', 'UPDATE', 'DDL', 'OTHER')
        """
        pattern = compile(
            r"""
            ^(?:\s*--.*?$\s*)*              
            (?:/\*.*?\*/\s*)*               
            (?:\s*\B/\*.*?\*/\s*)*          
            \b(INSERT|DELETE|UPDATE|CREATE|ALTER|DROP|TRUNCATE|SELECT)\b
            """,
            IGNORECASE | DOTALL | VERBOSE
        )
        match = pattern.search(sql)
        if not match:
            return "OTHER"
        keyword = match.group(1).upper()
        if keyword in ("INSERT", "DELETE", "UPDATE", "SELECT"):
            return keyword
        elif keyword in ("CREATE", "ALTER", "DROP", "TRUNCATE"):
            return "DDL"
        else:
            return "OTHER"

    def get_db_config(self, tool_parameters):
        """Get database configuration from environment variables."""
        config = {
            "host": tool_parameters.get("polardb_host", ""),
            "port": tool_parameters.get("polardb_port", ""),
            "user": tool_parameters.get("polardb_user", ""),
            "password": tool_parameters.get("polardb_password", ""),
            "database": tool_parameters.get("polardb_database", "")
        }
        
        if not all([config["host"], config["port"], config["user"], config["password"], config["database"]]):
            # logger.error("Missing required database configuration. Please check environment variables:")
            # logger.error("POLARDB_MYSQL_USER, POLARDB_MYSQL_PASSWORD, and POLARDB_MYSQL_DATABASE are required")
            raise ValueError("Missing required database configuration")
        return config

    def execute_sql(self, arguments: str, tool_parameters) -> str:
        print("execute_sql...")
        config = self.get_db_config(tool_parameters)
        query = arguments
        if not query:
            raise ValueError("Query is required")
        operation_type = self.get_sql_operation_type(query)
        print(f"SQL operation type: {operation_type}")
        global enable_write,enable_update,enable_insert,enable_ddl
        if operation_type == 'INSERT' and not enable_insert:
            print(f"INSERT operation is not enabled, please check POLARDB_MYSQL_ENABLE_INSERT")
            return "INSERT operation is not enabled in current tool"
        elif operation_type == 'UPDATE' and not enable_update:
            print(f"UPDATE operation is not enabled, please check POLARDB_MYSQL_ENABLE_UPDATE")
            return "UPDATE operation is not enabled in current tool"
        elif operation_type == 'DELETE' and not enable_write:
            print(f"DELETE operation is not enabled, please check POLARDB_MYSQL_ENABLE_WRITE")
            return "DELETE operation is not enabled in current tool"
        elif operation_type == 'DDL' and not enable_ddl:
            print(f"DDL operation is not enabled, please check POLARDB_MYSQL_ENABLE_DDL")
            return "DDL operation is not enabled in current tool" 
        else:   
            print(f"will Executing SQL: {query}")
            try:
                with connect(**config) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(query)
                        if cursor.description is not None:
                            rows = cursor.fetchall()
                            return rows
                        else:
                            conn.commit()
                            return f"Query executed successfully. Rows affected: {cursor.rowcount}"
            except Error as e:
                return f"Error executing query: {str(e)}"

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        print(tool_parameters)
        schema_index_name = tool_parameters.get("schema_index_name", "")
        if not schema_index_name:
            raise Exception("schema_index表名不能为空。")

        try:
            sql0 = f"/*polar4ai*/CREATE TABLE {schema_index_name}(id integer, table_name varchar, table_comment text_ik_max_word, table_ddl text_ik_max_word, column_names text_ik_max_word, column_comments text_ik_max_word, sample_values text_ik_max_word, vecs vector_768,ext text_ik_max_word, PRIMARY key (id))"
            lines = self.execute_sql(sql0, tool_parameters)
            if isinstance(lines, str) and lines.startswith("Error"):
                print(lines)
                if lines.find("table exist")== -1:
                    raise Exception(lines)
        except Exception as e:
            raise Exception(f"调用数据库失败 0202: {e}")

        sql1 = f"/*polar4ai*/SELECT id, table_name, table_comment FROM {schema_index_name}"
        try:
            lines = self.execute_sql(sql1, tool_parameters)
            if isinstance(lines, str) and lines.startswith("Error"):
                print(lines)
                raise Exception(lines)
            result = {}
            for line in lines:
                result[str(line[0])] = {
                        "table_name": line[1],
                        "table_comment":line[2]
                }
            yield self.create_json_message(result)
        except Exception as e:
            raise Exception(f"调用数据库失败 0201: {e}")
