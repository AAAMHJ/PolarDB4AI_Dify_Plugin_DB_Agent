from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from mysql.connector import connect, Error

from re import compile, IGNORECASE, DOTALL, VERBOSE

enable_write = False
enable_update = False
enable_insert = False
enable_ddl = False

class Polardb4aiPatternIndexShowTool(Tool):
    def get_sql_operation_type(self, sql):
        """
        使用正则表达式判断 SQL 操作类型
        :param sql: 输入 SQL 语句
        :return: 返回操作类型 ('INSERT', 'DELETE', 'UPDATE', 'DDL', 'OTHER')
        """
        # 正则表达式匹配 SQL 操作类型（忽略大小写）
        pattern = compile(
            r"""
            ^(?:\s*--.*?$\s*)*              # 跳过单行注释（-- 或 # 开头）
            (?:/\*.*?\*/\s*)*               # 跳过块注释（/* ... */）
            (?:\s*\B/\*.*?\*/\s*)*          # 跳过块注释（更严格的匹配）
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
                            columns = [desc[0] for desc in cursor.description]
                            rows = cursor.fetchall()
                            return rows
                        else:
                            conn.commit()
                            return f"Query executed successfully. Rows affected: {cursor.rowcount}"
            except Error as e:
                return f"Error executing query: {str(e)}"

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        print(tool_parameters)
        pattern_index_name = tool_parameters.get("pattern_index_name", "")
        if not pattern_index_name:
            raise Exception("pattern_index表名不能为空。")
        
        try:
            sql0 = f"/*polar4ai*/CREATE TABLE {pattern_index_name}(id integer, pattern_question text_ik_max_word, pattern_description text_ik_max_word, pattern_sql text_ik_max_word, pattern_params text_ik_max_word, pattern_tables text_ik_max_word, vecs vector_768, PRIMARY key (id))"
            lines = self.execute_sql(sql0, tool_parameters)
            if isinstance(lines, str) and lines.startswith("Error"):
                print(lines)
                if lines.find("table exist")== -1:
                    raise Exception(lines)
        except Exception as e:
            raise Exception(f"调用数据库失败 0402: {e}")

        try:
            sql1 = f"/*polar4ai*/SELECT id, pattern_question, pattern_sql FROM {pattern_index_name} order by id"
            print(sql1)
            lines = self.execute_sql(sql1, tool_parameters)
            # 检查 result 是否为字符串且以 "Error" 开头
            if isinstance(lines, str) and lines.startswith("Error"):
                raise Exception(lines)
            result = {}
            for line in lines:
                result[str(line[0])] = {
                        "pattern_question": line[1],
                        "pattern_sql":line[2]
                }
            print("\nresult\n")
            print(result)
            print("\nresult\n")
            yield self.create_json_message(result)
        except Exception as e:
            raise Exception(f"调用数据库失败 0401: {e}")
