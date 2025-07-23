from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from mysql.connector import connect, Error

from re import compile, IGNORECASE, DOTALL, VERBOSE

enable_write = True
enable_update = True
enable_insert = True
enable_ddl = True

class Polardb4aiLlmConfigEditorTool(Tool):
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
                            columns = [desc[0] for desc in cursor.description]
                            rows = cursor.fetchall()
                            result = [",".join(map(str, row)) for row in rows]
                            return "\n".join([",".join(columns)] + result)
                        else:
                            conn.commit()
                            return f"Query executed successfully. Rows affected: {cursor.rowcount}"
            except Error as e:
                return f"Error executing query: {str(e)}"

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        print(tool_parameters)
        config_id1 = tool_parameters.get("config_id1", "")
        text_condition1 = tool_parameters.get("text_condition1", "")
        formula_function1 = tool_parameters.get("formula_function1", "")
        is_functional1 = tool_parameters.get("is_functional1", "")
        if is_functional1 == 'None':
            is_functional1 = ""
        if config_id1:
            1
        elif text_condition1 or formula_function1 or is_functional1:
            raise Exception("请填写ID1")

        config_id2 = tool_parameters.get("config_id2", "")
        text_condition2 = tool_parameters.get("text_condition2", "")
        formula_function2 = tool_parameters.get("formula_function2", "")
        is_functional2 = tool_parameters.get("is_functional2", "")
        if is_functional2 == 'None':
            is_functional2 = ""
        if config_id2:
            1
        elif text_condition2 or formula_function2 or is_functional2:
            raise Exception("请填写ID2")

        try:
            if config_id1:
                if not (text_condition1 or formula_function1 or is_functional1):
                    sql1_1 = f"DELETE FROM polar4ai_nl2sql_llm_config WHERE id = {config_id1}"
                    lines1_1 = self.execute_sql(sql1_1, tool_parameters)
                    # 检查 result 是否为字符串且以 "Error" 开头
                    if isinstance(lines1_1, str) and lines1_1.startswith("Error"):
                        raise Exception(lines1_1)
                else:
                    sql1_1 = f"SELECT id FROM polar4ai_nl2sql_llm_config where id = {config_id1}"
                    lines1_1 = self.execute_sql(sql1_1, tool_parameters)
                    print(lines1_1)
                    # 检查 result 是否为字符串且以 "Error" 开头
                    if isinstance(lines1_1, str) and lines1_1.startswith("Error"):
                        raise Exception(lines1_1)
                    prefix = "id"
                    if lines1_1.startswith(prefix):
                        lines1_1 = lines1_1[len(prefix):]
                    print("lines1_1:")
                    print(lines1_1)
                    if lines1_1:
                        update_info = ""
                        if text_condition1:
                            update_info = update_info + f", text_condition = '{text_condition1}'"
                        if formula_function1:
                            update_info = update_info + f", formula_function = '{formula_function1}'"
                        if is_functional1:
                            update_info = update_info + f", is_functional = {is_functional1}"
                        print(update_info)
                        if update_info:
                            update_info = update_info[1:]
                            print(update_info)
                        else:
                            raise Exception("Error: 无字段需要更新")
                        sql1_2 = f"UPDATE polar4ai_nl2sql_llm_config SET {update_info} WHERE id = {config_id1}"
                        lines1_2 = self.execute_sql(sql1_2, tool_parameters)
                        # 检查 result 是否为字符串且以 "Error" 开头
                        if isinstance(lines1_2, str) and lines1_2.startswith("Error"):
                            raise Exception(lines1_2)
                    elif text_condition1 and formula_function1:
                        if is_functional1 == "":
                            is_functional1 = 1
                        sql1_2 = f"INSERT INTO polar4ai_nl2sql_llm_config (`id`,`is_functional`,`text_condition`,`formula_function`) VALUES ({config_id1},{is_functional1},'{text_condition1}','{formula_function1}')"
                        lines1_2 = self.execute_sql(sql1_2, tool_parameters)
                        # 检查 result 是否为字符串且以 "Error" 开头
                        if isinstance(lines1_2, str) and lines1_2.startswith("Error"):
                            raise Exception(lines1_2)
                    else:
                        raise Exception("新建config，匹配字段1与业务信息1必填，该config默认有效")
                        
            if config_id2:
                if not (text_condition2 or formula_function2 or is_functional2):
                    sql2_1 = f"DELETE FROM polar4ai_nl2sql_llm_config WHERE id = {config_id2}"
                    lines2_1 = self.execute_sql(sql2_1, tool_parameters)
                    # 检查 result 是否为字符串且以 "Error" 开头
                    if isinstance(lines2_1, str) and lines2_1.startswith("Error"):
                        raise Exception(lines2_1)
                else:
                    sql2_1 = f"SELECT id FROM polar4ai_nl2sql_llm_config where id = {config_id2}"
                    lines2_1 = self.execute_sql(sql2_1, tool_parameters)
                    print(lines2_1)
                    # 检查 result 是否为字符串且以 "Error" 开头
                    if isinstance(lines2_1, str) and lines2_1.startswith("Error"):
                        raise Exception(lines2_1)
                    prefix = "id"
                    if lines2_1.startswith(prefix):
                        lines2_1 = lines2_1[len(prefix):]
                    print("lines2_1:")
                    print(lines2_1)
                    if lines2_1:
                        update_info = ""
                        if text_condition2:
                            update_info = update_info + f", text_condition = '{text_condition2}'"
                        if formula_function2:
                            update_info = update_info + f", formula_function = '{formula_function2}'"
                        if is_functional2:
                            update_info = update_info + f", is_functional = {is_functional2}"
                        print(update_info)
                        if update_info:
                            update_info = update_info[1:]
                            print(update_info)
                        else:
                            raise Exception("Error: 无字段需要更新")
                        sql2_2 = f"UPDATE polar4ai_nl2sql_llm_config SET {update_info} WHERE id = {config_id2}"
                        lines2_2 = self.execute_sql(sql2_2, tool_parameters)
                        # 检查 result 是否为字符串且以 "Error" 开头
                        if isinstance(lines2_2, str) and lines2_2.startswith("Error"):
                            raise Exception(lines2_2)
                    elif text_condition2 and formula_function2:
                        if is_functional2 == "":
                            is_functional2 = 1
                        sql2_2 = f"INSERT INTO polar4ai_nl2sql_llm_config (`id`,`is_functional`,`text_condition`,`formula_function`) VALUES ({config_id2},{is_functional2},'{text_condition2}','{formula_function2}')"
                        lines2_2 = self.execute_sql(sql2_2, tool_parameters)
                        # 检查 result 是否为字符串且以 "Error" 开头
                        if isinstance(lines2_2, str) and lines2_2.startswith("Error"):
                            raise Exception(lines2_2)
                    else:
                        raise Exception("新建config，匹配字段2与业务信息2必填，该config默认有效")
            
            yield self.create_text_message("done")
        except Exception as e:
            raise Exception(f"调用数据库失败: {e}")
