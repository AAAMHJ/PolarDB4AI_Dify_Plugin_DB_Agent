from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from mysql.connector import connect, Error

from re import compile, IGNORECASE, DOTALL, VERBOSE
import time
enable_write = False
enable_update = False
enable_insert = False
enable_ddl = False

class Polardb4aiTaskMonitorTool(Tool):
    def get_sql_operation_type(self, sql):
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
        task_id = tool_parameters.get("task_id", "")
        if not task_id:
            raise Exception("任务ID不能为空。")
        try:
            result = {}
            if task_id == "task_id_skip":
                result = {"taskStatus": "skipped"}
                yield self.create_json_message(result)
            else:
                list1 = [1, 1.2, 1.44, 1.728, 2.0736, 2.48832, 2.9859839999999997, 3.5831807999999996, 4.299816959999999, 5.159780351999999, 6.191736422399999, 7.430083706879999,
                    8.916100448255998, 10.699320537907196, 12.839184645488634, 15.407021574586361, 18.48842588950363, 22.186111067404358, 26.62333328088523,
                    31.947999937062274, 38.33759992447473, 46.005119909369675, 55.206143891243606, 66.24737266949232, 79.49684720339079, 95.39621664406894, 114.47545997288273,
                    137.37055196745928, 164.84466236095113, 197.81359483314137, 237.37631379976963, 284.8515765597235, 341.82189187166824, 410.18627024600187, 492.2235242952022,
                    590.6682291542426, 708.8018749850911, 850]
                list2 = [850, 910, 970, 1030, 1090, 1150, 1210, 1270, 1330, 1390, 1450, 1510, 1570, 1630, 1690, 1750, 1810, 1870, 1930, 1990, 2050, 2110, 2170, 2230, 2290, 2350, 2410,
                    2470, 2530, 2590, 2650, 2710, 2770, 2830, 2890, 2950, 3010, 3070, 3130, 3190, 3250, 3310, 3370, 3430, 3490, 3550, 3610]

                sql1 = f"/*polar4ai*/SHOW TASK `{task_id}`"
                print(sql1)

                flag = 1
                for i in range(1, len(list1)):
                    lines = self.execute_sql(sql1, tool_parameters)
                    if isinstance(lines, str) and lines.startswith("Error"):
                        raise Exception(f"0103 {lines}")
                    if lines.find("finish")!= -1:
                        print("Task completed!")
                        line = lines.split("\n")[1]
                        line = line.split(",")
                        result = {
                            "taskStatus": line[0],
                            "results": line[2],
                            "startTime": line[3][:19],
                            "endTime": line[4][:19]
                        }
                        flag = 0
                        break
                    elif lines.find("fail")!= -1:
                        print("Task fail!")
                        line = lines.split("\n")[1]
                        line = line.split(",")
                        result = {
                            "taskStatus": line[0],
                            "results": line[2],
                            "startTime": line[3][:19],
                            "endTime": line[4][:19]
                        }
                        flag = 0
                        break
                    time.sleep((list1[i]-list1[i-1]) * 60)

                for i in range(1, len(list2)):
                    if flag == 0:
                        break
                    lines = self.execute_sql(sql1, tool_parameters)
                    if isinstance(lines, str) and lines.startswith("Error"):
                        raise Exception(f"0102 {lines}")
                    if lines.find("finish")!=-1:
                        print("Task completed!")
                        line = lines.split("\n")[1]
                        line = line.split(",")
                        result = {
                            "taskStatus": line[0],
                            "results": line[2],
                            "startTime": line[3][:19],
                            "endTime": line[4][:19]
                        }
                        flag = 0
                        break
                    elif lines.find("fail")!= -1:
                        print("Task fail!")
                        line = lines.split("\n")[1]
                        line = line.split(",")
                        result = {
                            "taskStatus": line[0],
                            "results": line[2],
                            "startTime": line[3][:19],
                            "endTime": line[4][:19]
                        }
                        flag = 0
                        break
                    time.sleep((list2[i]-list2[i-1]) * 60)

                if flag :
                    raise Exception("0101")
                print("\nresult\n")
                print(result)
                print("\nresult\n")

                yield self.create_json_message(result)
        except Exception as e:
            raise Exception(f"调用数据库失败: {e}")
