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

class Polardb4aiPatternIndexEditorTool(Tool):
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
        pattern_index_name = tool_parameters.get("pattern_index_name", "")
        if not pattern_index_name:
            raise Exception("pattern_index表名不能为空。")
        pattern_id1 = tool_parameters.get("pattern_id1", "")
        pattern_question1 = tool_parameters.get("pattern_question1", "")
        pattern_sql1 = tool_parameters.get("pattern_sql1", "")
        if pattern_id1:
            if not (pattern_question1 and pattern_sql1) and not (pattern_question1 == '' and pattern_sql1 == ''):
                raise Exception("请补全问题1或答案SQL1")
        elif pattern_question1 or pattern_sql1:
            raise Exception("请填写ID1")

        pattern_id2 = tool_parameters.get("pattern_id2", "")
        pattern_question2 = tool_parameters.get("pattern_question2", "")
        pattern_sql2 = tool_parameters.get("pattern_sql2", "")
        if pattern_id2:
            if not (pattern_question2 and pattern_sql2) and not (pattern_question2 == '' and pattern_sql2 == ''):
                raise Exception("请补全问题2或答案SQL2")
        elif pattern_question2 or pattern_sql2:
            raise Exception("请填写ID2")
        
        rebuild = tool_parameters.get("rebuild", '1')
        
        try:
            sql0 = f"CREATE TABLE if not EXISTS `polar4ai_nl2sql_pattern_{pattern_index_name}` (`id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',`pattern_question` text COMMENT '模板问题',`pattern_description` text COMMENT '模板描述',`pattern_sql` text COMMENT '模板SQL',`pattern_params` text COMMENT '模板参数',PRIMARY KEY (`id`)) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
            lines0 = self.execute_sql(sql0, tool_parameters)
            print(lines0)
            if isinstance(lines0, str) and lines0.startswith("Error"):
                raise Exception(f"0512 {lines0}")
            
            if pattern_id1:
                if (pattern_question1 and pattern_sql1):
                    sql1_1 = f"SELECT id FROM polar4ai_nl2sql_pattern_{pattern_index_name} where id = {pattern_id1}"
                    lines1_1 = self.execute_sql(sql1_1, tool_parameters)
                    print(lines1_1)
                    # 检查 result 是否为字符串且以 "Error" 开头
                    if isinstance(lines1_1, str) and lines1_1.startswith("Error"):
                        raise Exception(f"0511 {lines1_1}")
                    prefix = "id"
                    if lines1_1.startswith(prefix):
                        lines1_1 = lines1_1[len(prefix):]
                    print("lines1_1:")
                    print(lines1_1)
                    if lines1_1:
                        sql1_2 = f"UPDATE polar4ai_nl2sql_pattern_{pattern_index_name} SET pattern_question = '{pattern_question1}', pattern_description = '{pattern_question1}', pattern_sql = '{pattern_sql1}',pattern_params = '' WHERE id = {pattern_id1}"
                        lines1_2 = self.execute_sql(sql1_2, tool_parameters)
                        # 检查 result 是否为字符串且以 "Error" 开头
                        if isinstance(lines1_2, str) and lines1_2.startswith("Error"):
                            raise Exception(f"0510 {lines1_2}")
                    else:
                        sql1_2 = f"INSERT INTO polar4ai_nl2sql_pattern_{pattern_index_name} (`id`,`pattern_question`,`pattern_description`,`pattern_sql`,`pattern_params`) VALUES ({pattern_id1},'{pattern_question1}','{pattern_question1}','{pattern_sql1}','')"
                        lines1_2 = self.execute_sql(sql1_2, tool_parameters)
                        # 检查 result 是否为字符串且以 "Error" 开头
                        if isinstance(lines1_2, str) and lines1_2.startswith("Error"):
                            raise Exception(f"0509 {lines1_2}")
                elif (pattern_question1=='' and pattern_sql1==''):
                    sql1_1 = f"DELETE FROM polar4ai_nl2sql_pattern_{pattern_index_name} WHERE id = {pattern_id1}"
                    lines1_1 = self.execute_sql(sql1_1, tool_parameters)
                    # 检查 result 是否为字符串且以 "Error" 开头
                    if isinstance(lines1_1, str) and lines1_1.startswith("Error"):
                        raise Exception(f"0508 {lines1_1}")
            
            if pattern_id2:
                if (pattern_question2 and pattern_sql2):
                    sql2_1 = f"SELECT id FROM polar4ai_nl2sql_pattern_{pattern_index_name} where id = {pattern_id2}"
                    lines2_1 = self.execute_sql(sql2_1, tool_parameters)
                    print(lines2_1)
                    # 检查 result 是否为字符串且以 "Error" 开头
                    if isinstance(lines2_1, str) and lines2_1.startswith("Error"):
                        raise Exception(f"0507 {lines2_1}")  
                    prefix = "id"
                    if lines2_1.startswith(prefix):
                        lines2_1 = lines2_1[len(prefix):]
                    print("lines2_1:")
                    print(lines2_1)
                    if lines2_1:
                        sql2_2 = f"UPDATE polar4ai_nl2sql_pattern_{pattern_index_name} SET pattern_question = '{pattern_question2}', pattern_description = '{pattern_question2}', pattern_sql = '{pattern_sql2}',pattern_params = '' WHERE id = {pattern_id2}"
                        lines2_2 = self.execute_sql(sql2_2, tool_parameters)
                        # 检查 result 是否为字符串且以 "Error" 开头
                        if isinstance(lines2_2, str) and lines2_2.startswith("Error"):
                            raise Exception(f"0506 {lines2_2}")
                    else:
                        sql2_2 = f"INSERT INTO polar4ai_nl2sql_pattern_{pattern_index_name} (`id`,`pattern_question`,`pattern_description`,`pattern_sql`,`pattern_params`) VALUES ({pattern_id2},'{pattern_question2}','{pattern_question2}','{pattern_sql2}','')"
                        lines2_2 = self.execute_sql(sql2_2, tool_parameters)
                        # 检查 result 是否为字符串且以 "Error" 开头
                        if isinstance(lines2_2, str) and lines2_2.startswith("Error"):
                            raise Exception(f"0505 {lines2_2}")
                elif (pattern_question2=='' and pattern_sql2==''):
                    sql2_1 = f"DELETE FROM polar4ai_nl2sql_pattern_{pattern_index_name} WHERE id = {pattern_id2}"
                    lines2_1 = self.execute_sql(sql2_1, tool_parameters)
                    # 检查 result 是否为字符串且以 "Error" 开头
                    if isinstance(lines2_1, str) and lines2_1.startswith("Error"):
                        raise Exception(f"0504 {lines2_1}")
            
            if rebuild == '1':
                sql3_1 = f"/*polar4ai*/DROP TABLE {pattern_index_name}"
                lines3_1 = self.execute_sql(sql3_1, tool_parameters)
                # 检查 result 是否为字符串且以 "Error" 开头
                if isinstance(lines3_1, str) and lines3_1.startswith("Error"):
                    print(lines3_1)
                    if lines3_1.find("Unknown table")== -1:
                        raise Exception(f"0503 {lines3_1}")
                sql3_1 = f"/*polar4ai*/CREATE TABLE {pattern_index_name}(id integer, pattern_question text_ik_max_word, pattern_description text_ik_max_word, pattern_sql text_ik_max_word, pattern_params text_ik_max_word, pattern_tables text_ik_max_word, vecs vector_768, PRIMARY key (id))"
                lines3_1 = self.execute_sql(sql3_1, tool_parameters)
                # 检查 result 是否为字符串且以 "Error" 开头
                if isinstance(lines3_1, str) and lines3_1.startswith("Error"):
                    raise Exception(f"0502 {lines3_1}")
                sql3_1 = f"/*polar4ai*/SELECT * FROM PREDICT (MODEL _polar4ai_text2vec, SELECT '') WITH (mode='async', resource='pattern', pattern_table_name='polar4ai_nl2sql_pattern_{pattern_index_name}') INTO {pattern_index_name};"
                lines3_1 = self.execute_sql(sql3_1, tool_parameters)
                # 检查 result 是否为字符串且以 "Error" 开头
                if isinstance(lines3_1, str) and lines3_1.startswith("Error"):
                    raise Exception(f"0501 {lines3_1}")
                prefix = "task_id\n"
                if lines3_1.startswith(prefix):
                    lines3_1 = lines3_1[len(prefix):]
                yield self.create_text_message(lines3_1)
            else:
                yield self.create_text_message("task_id_skip")
        except Exception as e:
            raise Exception(f"调用数据库失败: {e}")
