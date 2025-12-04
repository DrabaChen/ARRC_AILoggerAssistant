# -*- coding: utf-8 -*-
"""
Roll-call AI Logger Assistant

@author: BG5CVB

"""
import json
import csv
import os
import datetime
from openai import OpenAI
from typing import List

# 导入彩色输出库
try:
    from colorama import init, Fore, Back, Style
    init()  # 初始化colorama以支持Windows
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # 如果没有安装colorama，定义空的彩色类
    class Fore:
        RED = ''
        GREEN = ''
        YELLOW = ''
        BLUE = ''
        MAGENTA = ''
        CYAN = ''
        WHITE = ''
        RESET = ''
    class Back:
        RED = ''
        GREEN = ''
        YELLOW = ''
        BLUE = ''
        MAGENTA = ''
        CYAN = ''
        WHITE = ''
        RESET = ''
    class Style:
        BRIGHT = ''
        DIM = ''
        NORMAL = ''
        RESET_ALL = ''

CITY = "杭州"
OPERATOR = ""
RECORD = []    # NR, DATE, UTC, CALL, RST, QTH, RIG, ANT, PWR, ALT, RMKS, OP
NR_COUNTER = 1

def cprint(text: str, color: str = "WHITE", bright: bool = False, end_str: str = "\n") -> None:
    """
    彩色打印函数，自动处理 colorama 是否可用。
    
    Parameters
    ----------
    text : str
        要打印的文本。
    color : str
        颜色名称，如 'RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE'。
    bright : bool
        是否使用高亮（bright）样式。
    """
    if COLORS_AVAILABLE:
        color_code = getattr(Fore, color.upper(), Fore.WHITE)
        style_code = Style.BRIGHT if bright else Style.NORMAL
        reset_code = Style.RESET_ALL
        print(f"{style_code}{color_code}{text}{reset_code}", end = end_str)
    else:
        # 无 colorama 时直接打印原文
        print(text, end = end_str)


def get_client():
    return OpenAI(
        api_key = os.getenv("DEEPSEEK_API_KEY"),
        base_url = "https://api.deepseek.com/v1",
    )


def get_respond(raw_text):
    """
    Parameters
    ----------
    raw_text : str
        Row text recorded while listening to the callee.

    Returns
    -------
    record : srt(json)
        Formatted text, including CALL, RST, QTH, RIG, ANT, PWR, ALT, RMKS.
        
    The function is called to call the API
        (using environment veriable API_key)
            to obtain a formatted json result.

    """
    client = get_client()
    
    sys_prompt = (
        "你是一名资深业余无线电爱好者，现在需要帮助新手将杂乱的信息整理成一条有序的QSO记录。"
        "你需要从中提取相关信息，推测地点、设备、高度、天线等。除了设备（如UV-K6等）需要用字母，其他信息请使用数字和中文表述。"
        "需要提取的字段，分别是CALL（呼号）, RST（信号报告）, QTH（地址）, RIG（设备）, ANT（天线）, PWR（功率）, ALT（高度，通常为几米或几楼）, RMKS（备注）。"
        f"你所在的城市是{CITY}，推测地点时需要优先考虑本地以及附近地区的地名。"
        "一些可能的缩写，供你参考：“3ele yagi”表示“3单元八木”，“orgn”表示“原装（天线）”，“gnd”表示“地面高度（ground）”，等。"
        "请返回JSON格式的内容，不要输出其他任何多余的内容！"
    )
    
    usr_prompt = (
        f"请根据下文推测相关信息，如果遇到无法辨别的字段，请使用字符串NULL表示。信号报告默认为59。"
        f"\n\n输入文本：{raw_text}"
        f"\n\n请严格按照以下JSON格式返回："
        f'{{"CALL": "呼号", "RST": "信号报告", "QTH": "地点", "RIG": "设备", "ANT": "天线", "PWR": "功率", "ALT": "高度", "RMKS": "备注"}}'
    )
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": usr_prompt},
            ],
            stream = False,
            temperature = 0.8,
            response_format = {"type": "json_object"}  # 确保返回JSON格式
        )
        
        # 提取AI返回的内容
        content = response.choices[0].message.content
        
        # 尝试解析JSON
        try:
            result = json.loads(content)
            # 确保所有必需字段都存在
            required_fields = ["CALL", "RST", "QTH", "RIG", "ANT", "PWR", "ALT", "RMKS"]
            
            for field in required_fields:
                if field not in result:
                    result[field] = "NULL"
            return json.dumps(result, ensure_ascii = False)
        
        except json.JSONDecodeError:
            # 如果解析失败，返回一个默认的JSON结构
            cprint(f"Warning: Could not parse JSON response: {content}", "YELLOW")
            return json.dumps({
                "CALL": "NULL",
                "RST": "NULL",
                "QTH": "NULL",
                "RIG": "NULL",
                "ANT": "NULL",
                "PWR": "NULL",
                "ALT": "NULL",
                "RMKS": content  # 将原始响应作为备注
            }, ensure_ascii = False)
            
    except Exception as e:
        cprint(f"API调用错误: {e}", "RED")
        # 返回一个默认的JSON结构作为错误处理
        return json.dumps({
            "CALL": "NULL",
            "RST": "NULL",
            "QTH": "NULL",
            "RIG": "NULL",
            "ANT": "NULL",
            "PWR": "NULL",
            "ALT": "NULL",
            "RMKS": f"API调用错误: {str(e)}"
        }, ensure_ascii = False)


def get_respond_for_edit(original_record: str, correction: str):
    """
    专门用于编辑记录的API调用函数，基于原始记录和更正内容生成新的记录
    """
    client = get_client()
    
    sys_prompt = (
        "你是一名资深业余无线电爱好者，现在需要帮助新手将杂乱的信息整理成一条有序的QSO记录。"
        "你需要从中提取相关信息，推测地点、设备、高度、天线等。除了设备（如UV-K6等）需要用字母，其他信息请使用数字和中文表述。"
        "需要提取的字段，分别是CALL（呼号）, RST（信号报告）, QTH（地址）, RIG（设备）, ANT（天线）, PWR（功率）, ALT（高度，通常为几米或几楼）, RMKS（备注）。"
        f"你所在的城市是{CITY}，推测地点时需要优先考虑本地以及附近地区的地名。"
        "一些可能的缩写，供你参考：“3ele yagi”表示“3单元八木”，“orgn”表示“原装（天线）”，“gnd”表示“地面高度（ground）”，等。"
        "请返回JSON格式的内容，不要输出其他任何多余的内容！"
    )
    
    usr_prompt = (
        f"原始记录：{original_record}\n\n"
        f"更正内容：{correction}\n\n"
        f"请根据更正内容对原始记录进行修正，如果更正内容中没有提到的字段，保持原记录的值不变。"
        f"请严格按照以下JSON格式返回："
        f'{{"CALL": "呼号", "RST": "信号报告", "QTH": "地点", "RIG": "设备", "ANT": "天线", "PWR": "功率", "ALT": "高度", "RMKS": "备注"}}'
    )
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": usr_prompt},
            ],
            stream = False,
            temperature = 0.8,
            response_format = {"type": "json_object"}  # 确保返回JSON格式
        )
        
        # 提取AI返回的内容
        content = response.choices[0].message.content
        
        # 尝试解析JSON
        try:
            result = json.loads(content)
            # 确保所有必需字段都存在
            required_fields = ["CALL", "RST", "QTH", "RIG", "ANT", "PWR", "ALT", "RMKS"]
            
            for field in required_fields:
                if field not in result:
                    result[field] = "NULL"
            return json.dumps(result, ensure_ascii = False)
        
        except json.JSONDecodeError:
            # 如果解析失败，返回一个默认的JSON结构
            cprint(f"Warning: Could not parse JSON response: {content}", "YELLOW")
            return json.dumps({
                "CALL": "NULL",
                "RST": "NULL",
                "QTH": "NULL",
                "RIG": "NULL",
                "ANT": "NULL",
                "PWR": "NULL",
                "ALT": "NULL",
                "RMKS": content  # 将原始响应作为备注
            }, ensure_ascii = False)
            
    except Exception as e:
        cprint(f"API调用错误: {e}", "RED")
        # 返回一个默认的JSON结构作为错误处理
        return json.dumps({
            "CALL": "NULL",
            "RST": "NULL",
            "QTH": "NULL",
            "RIG": "NULL",
            "ANT": "NULL",
            "PWR": "NULL",
            "ALT": "NULL",
            "RMKS": f"API调用错误: {str(e)}"
        }, ensure_ascii = False)

    
def save_final(filename):
    """
    Parameters
    ----------
    filename : str
        The name of the final record file, without filetype postfix.

    Returns
    -------
    None.
    
    The function is called to save the record as a .csv file.

    """
    
    global RECORD
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    # 修复CSV编码问题，使用utf-8-sig以避免BOM问题，同时确保中文正确显示
    with open(filename, 'w', newline = '', encoding = 'utf-8-sig') as csvfile:
        fieldnames = ['NR', 'DATE', 'UTC', 'CALL', 'RST', 'QTH', 'RIG', 'ANT', 'PWR', 'ALT', 'RMKS', 'OP']
        writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
        
        writer.writeheader()
        for record in RECORD:
            row = {
                'NR': record[0],
                'DATE': record[1],
                'UTC': record[2],
                'CALL': record[3],
                'RST': record[4],
                'QTH': record[5],
                'RIG': record[6],
                'ANT': record[7],
                'PWR': record[8],
                'ALT': record[9],
                'RMKS': record[10],
                'OP': record[11]
            }
            writer.writerow(row)
    
    cprint(f"Final record saved as {filename}", "GREEN")


def backup():
    """
    
    The function is called halfway, to leave a latest backup file.
    
    """
    
    global RECORD
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"backup_{timestamp}.json"
    
    with open(filename, 'w', encoding = 'utf-8') as f:
        json.dump({
            "OPERATOR": OPERATOR,
            "RECORD": RECORD,
            "NR_COUNTER": NR_COUNTER
        }, f, ensure_ascii = False, indent = 2)
    
    cprint(f"Backup saved as {filename}", "CYAN")
    
    # 清理旧备份文件（保留最近5个）
    clean_old_backups()
 
    
def clean_old_backups() -> None:
    """
    
    The function cleans all old backups but left 5 latest.
    
    """
    
    backup_files = [f for f in os.listdir('.') if f.startswith('backup_') and f.endswith('.json')]
    backup_files.sort(key = lambda x: os.path.getmtime(x), reverse = True)
    
    for old_backup in backup_files[5:]:
        os.remove(old_backup)
        cprint(f"Removed old backup: {old_backup}", "YELLOW")
    
    
def clean_bkup():
    """
    
    The function is called to clean all backup files.
    
    """
    
    backup_files = [f for f in os.listdir('.') if f.startswith('backup_') and f.endswith('.json')]
    
    for backup_file in backup_files:
        os.remove(backup_file)
        cprint(f"Removed backup: {backup_file}", "YELLOW")
    
    cprint("All backup files cleaned.", "RED")
    
    
def load_bkup() -> None:
    """
    
    The function is called to load from a backup file into RECORD.

    """
    
    global OPERATOR, RECORD, NR_COUNTER
    
    backup_files = [f for f in os.listdir('.') if f.startswith('backup_') and f.endswith('.json')]
    if not backup_files:
        cprint("No backup files found.", "YELLOW")
        return
    
    # 按修改时间排序，获取最新的备份文件
    backup_files.sort(key = lambda x: os.path.getmtime(x), reverse = True)
    latest_backup = backup_files[0]
    
    try:
        with open(latest_backup, 'r', encoding = 'utf-8') as f:
            data = json.load(f)
            OPERATOR = data.get("OPERATOR", "")
            RECORD = data.get("RECORD", [])
            NR_COUNTER = data.get("NR_COUNTER", len(RECORD) + 1)
        
        cprint(f"Loaded backup from {latest_backup}", "GREEN")
        cprint(f"Current operator: {OPERATOR}", "CYAN")
        cprint(f"Records loaded: {len(RECORD)}", "CYAN")
    except Exception as e:
        cprint(f"Error loading backup: {e}", "RED")
        
    
def append_record(info: List[str]) -> None:
    """
    Parameters
    ----------
    info : list
        A list containing basic info, including:
            CALL, RST, QTH, RIG, ANT, PWR, ALT, RMKS
            in order.

    Returns
    -------
    None.
    
    The function is called to append a record into RECORD.
    Time info DATE and UTC (gets from system), serial number NR and OP will be added.

    """
    
    global NR_COUNTER
    
    # 获取当前日期和UTC时间
    now = datetime.datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    utc_str = now.strftime("%H:%M")
    
    # 构建完整记录 [NR, DATE, UTC, CALL, RST, QTH, RIG, ANT, PWR, ALT, RMKS, OP]
    record = [
        str(NR_COUNTER),  # NR
        date_str,         # DATE
        utc_str,          # UTC
        info[0] if len(info) > 0 else "",  # CALL
        info[1] if len(info) > 1 else "",  # RST
        info[2] if len(info) > 2 else "",  # QTH
        info[3] if len(info) > 3 else "",  # RIG
        info[4] if len(info) > 4 else "",  # ANT
        info[5] if len(info) > 5 else "",  # PWR
        info[6] if len(info) > 6 else "",  # ALT
        info[7] if len(info) > 7 else "",  # RMKS
        OPERATOR          # OP
    ]
    
    RECORD.append(record)
    NR_COUNTER += 1
    cprint(f"Record #{record[0]} added: {record[3]} - {record[1]} {record[2]}", "GREEN")
    

def edit_record(call: str) -> None:
    """
    编辑指定呼号的记录
    """
    global RECORD
    
    # 查找指定呼号的记录
    found_records = []
    for i, record in enumerate(RECORD):
        if record[3].upper() == call.upper():  # 比较CALL字段
            found_records.append((i, record))
    
    if not found_records:
        cprint(f"未找到呼号为 {call} 的记录", "RED")
        return
    
    if len(found_records) > 1:
        cprint(f"找到多个呼号为 {call} 的记录:", "YELLOW")
        for i, record in found_records:
            cprint(f"  #{record[0]} - {record[3]} - {record[1]} {record[2]} - {record[5]}", "WHITE")
        record_index = input("请输入要编辑的记录编号: ").strip()
        try:
            record_index = int(record_index)
            record_to_edit = None
            for i, record in found_records:
                if int(record[0]) == record_index:
                    record_to_edit = (i, record)
                    break
            if record_to_edit is None:
                cprint("未找到指定编号的记录", "RED")
                return
        except ValueError:
            cprint("无效的编号", "RED")
            return
    else:
        record_to_edit = found_records[0]
    
    original_record = record_to_edit[1]
    cprint(f"原始记录: #{original_record[0]} - {original_record[3]} - {original_record[5]}", "CYAN")
    
    correction = input("请输入更正内容: ").strip()
    if not correction:
        cprint("更正内容不能为空", "RED")
        return
    
    # 调用AI API获取格式化信息
    try:
        # 构建原始记录字符串用于AI处理
        original_str = f"CALL: {original_record[3]}, RST: {original_record[4]}, QTH: {original_record[5]}, RIG: {original_record[6]}, ANT: {original_record[7]}, PWR: {original_record[8]}, ALT: {original_record[9]}, RMKS: {original_record[10]}"
        formatted_json = get_respond_for_edit(original_str, correction)
        info_dict = json.loads(formatted_json)
        
        # 提取信息并更新记录
        updated_record = [
            original_record[0],  # NR保持不变
            original_record[1],  # DATE保持不变
            original_record[2],  # UTC保持不变
            info_dict.get("CALL", original_record[3]),  # 使用AI返回的值或保持原值
            info_dict.get("RST", original_record[4]),
            info_dict.get("QTH", original_record[5]),
            info_dict.get("RIG", original_record[6]),
            info_dict.get("ANT", original_record[7]),
            info_dict.get("PWR", original_record[8]),
            info_dict.get("ALT", original_record[9]),
            info_dict.get("RMKS", original_record[10]),
            original_record[11]  # OP保持不变
        ]
        
        # 更新记录
        RECORD[record_to_edit[0]] = updated_record
        cprint(f"记录 #{updated_record[0]} 已更新: {updated_record[3]} - {updated_record[1]} {updated_record[2]}", "GREEN")
    except Exception as e:
        cprint(f"Error processing edit: {e}", "RED")
        cprint("Please try again or use 'H' for help.", "YELLOW")


def modify_op(call: str) -> None:
    """
    
    The function is called to change current OP.
    
    """
    
    global OPERATOR
    OPERATOR = call
    cprint(f"Operator changed to: {OPERATOR}", "GREEN")
    
    
def get_input():
    """
    
    Returns
    -------
    res : str
        The command or text got from user (entire line).
    
    The function is called to print a input prompt.
    [Nr. x] >
        Ready to get a new record.
    
    """
    
    global NR_COUNTER
    
    if OPERATOR == "":
        cprint("[OP NOT SET!]", "RED", end_str = "")
    else:
        cprint(f"[{OPERATOR}]", "GREEN", end_str = "")

    cprint(f"[Nr. {NR_COUNTER}] > ", "WHITE", bright = True, end_str = "")    
    return input().strip().upper()


def do_action(cmd):
    """
    Parameters
    ----------
    cmd : str
        Raw command.

    Returns
    -------
    None.
    
    The function is called to do corresponding actions based on the cmd.
    Case insensitive!
    
    `HELP` or `H`: print help info.
    `SAVE` or `S`: save backup.
    `LOAD` or `L`: load from backup.
    `FINAL` or `SF`: save the final record.
    `OP`: set current OPERATOR.
    `EDIT` or `E`: edit a record.
    Default: the QSO info text, which needed to be processed.

    """
    
    global OPERATOR, NR_COUNTER
    
    cmd_upper = cmd.strip().upper()
    
    if cmd_upper in ["HELP", "H"]:
        print_help()
    elif cmd_upper in ["SAVE", "S"]:
        backup()
    elif cmd_upper in ["LOAD", "L"]:
        load_bkup()
    elif cmd_upper in ["FINAL", "SF"]:
        filename = input("Enter filename for final record (without extension): ")
        save_final(filename)
    elif cmd_upper.startswith("OP "):
        op_call = cmd[3:].strip()
        modify_op(op_call)
    elif cmd_upper.startswith("EDIT ") or cmd_upper.startswith("E "):
        call = cmd.split(" ", 1)[1].strip()
        edit_record(call)
    elif cmd_upper == "QUIT":
        cprint("Quitting...", "RED")
    elif cmd_upper == "SHOW":
        show_records()
    elif cmd_upper == "CLEAR":
        RECORD.clear()
        NR_COUNTER = 1
        cprint("Records cleared.", "YELLOW")
    elif cmd_upper == "STATUS":
        show_status()
    else:
        # 默认处理为QSO信息
        if not OPERATOR:
            cprint("Error: Please set operator first using 'OP [call]' command", "RED")
            return
            
        # 调用AI API获取格式化信息
        try:
            formatted_json = get_respond(cmd)
            info_dict = json.loads(formatted_json)
            
            # 提取信息并添加到记录
            info = [
                info_dict.get("CALL", ""),
                info_dict.get("RST", ""),
                info_dict.get("QTH", ""),
                info_dict.get("RIG", ""),
                info_dict.get("ANT", ""),
                info_dict.get("PWR", ""),
                info_dict.get("ALT", ""),
                info_dict.get("RMKS", "")
            ]
            
            append_record(info)
        except Exception as e:
            cprint(f"Error processing QSO: {e}", "RED")
            cprint("Please try again or use 'H' for help.", "YELLOW")
            

def print_help() -> None:
    """
    
    The function is called to print help messages.
    
    """
    
    help_text = f"""
{Style.BRIGHT}{Fore.CYAN}Radio Roll-call AI Logger Assistant Help:{Style.RESET_ALL}
{Fore.CYAN}-----------------------------------------{Style.RESET_ALL}
{Style.BRIGHT}Commands (case insensitive):{Style.RESET_ALL}
  {Fore.GREEN}HELP{Style.RESET_ALL} or {Fore.GREEN}H{Style.RESET_ALL}     - {Fore.YELLOW}Show this help{Style.RESET_ALL}
  {Fore.GREEN}SAVE{Style.RESET_ALL} or {Fore.GREEN}S{Style.RESET_ALL}     - {Fore.YELLOW}Save backup{Style.RESET_ALL}
  {Fore.GREEN}LOAD{Style.RESET_ALL} or {Fore.GREEN}L{Style.RESET_ALL}     - {Fore.YELLOW}Load from backup{Style.RESET_ALL}
  {Fore.GREEN}FINAL{Style.RESET_ALL} or {Fore.GREEN}SF{Style.RESET_ALL}   - {Fore.YELLOW}Save final record to CSV{Style.RESET_ALL}
  {Fore.GREEN}OP [call]{Style.RESET_ALL}     - {Fore.YELLOW}Set current operator call sign{Style.RESET_ALL}
  {Fore.GREEN}EDIT [call]{Style.RESET_ALL}   - {Fore.YELLOW}Edit a record by call sign{Style.RESET_ALL}
  {Fore.GREEN}SHOW{Style.RESET_ALL}          - {Fore.YELLOW}Show current records{Style.RESET_ALL}
  {Fore.GREEN}CLEAR{Style.RESET_ALL}         - {Fore.YELLOW}Clear all records{Style.RESET_ALL}
  {Fore.GREEN}STATUS{Style.RESET_ALL}        - {Fore.YELLOW}Show current status{Style.RESET_ALL}
  {Fore.GREEN}QUIT{Style.RESET_ALL}          - {Fore.YELLOW}Exit program{Style.RESET_ALL}

{Style.BRIGHT}Default:{Style.RESET_ALL}
  {Fore.CYAN}Any other text will be treated as QSO information to be processed by AI.{Style.RESET_ALL}

{Style.BRIGHT}Examples:{Style.RESET_ALL}
  {Fore.MAGENTA}CQ de AB1CD 599 NY RIG:IC-7300 ANT:Dipole 100W{Style.RESET_ALL}
  {Fore.MAGENTA}TX1EF de AB1CD FM RST 579 QTH:Boston RIG:FT-991{Style.RESET_ALL}
    """
    
    print(help_text)


def show_records() -> None:
    """
    The function is called to show all records.
    """
    if not RECORD:
        cprint("No records yet.", "YELLOW")
        return
    
    print(f"\n{Style.BRIGHT}{Fore.CYAN}Current Records:{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Fore.WHITE}{'NR':<3} {'DATE':<10} {'UTC':<8} {'CALL':<8} {'RST':<5} {'QTH':<15} {'RIG':<15} {'ANT':<15} {'PWR':<8} {'ALT':<8} {'RMKS':<20}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'-' * 120}{Style.RESET_ALL}")
    for record in RECORD:
        print(f"{Fore.WHITE}{record[0]:<3} {record[1]:<10} {record[2]:<8} {record[3]:<8} {record[4]:<5} {record[5]:<15} {record[6]:<15} {record[7]:<15} {record[8]:<8} {record[9]:<8} {record[10]:<20}{Style.RESET_ALL}")


def show_status() -> None:
    """
    
    The function is called to show current status.
    
    """
    cprint(f"Current Operator: {OPERATOR}", "CYAN", bright=True)
    cprint(f"Records Count: {len(RECORD)}", "CYAN", bright=True)
    cprint(f"Next NR: {NR_COUNTER}", "CYAN", bright=True)
    

if __name__ == "__main__":
    
    cprint("Radio Roll-call AI Logger Assistant", "GREEN", bright=True)
    cprint("Type 'H' or 'HELP' for help", "YELLOW", bright=True)
    
    cmd = get_input()
    
    while cmd.upper() != "QUIT":
        do_action(cmd)
        
        cmd = get_input()
    
    cprint("Program ended.", "RED", bright=True)