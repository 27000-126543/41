"""
操作日志模块 - 记录所有操作并实时推送到项目群
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_cursor
from core.utils import get_datetime_str
from config.settings import LOGS_DIR


OPERATION_TYPES = {
    'CREATE': '创建',
    'UPDATE': '更新',
    'DELETE': '删除',
    'SUBMIT': '提交',
    'APPROVE': '审批通过',
    'REJECT': '审批驳回',
    'PUBLISH': '发布',
    'OPEN': '开标',
    'SCORE': '评分',
    'AWARD': '定标',
    'ARCHIVE': '归档',
    'WARN': '预警',
    'NOTIFY': '通知',
    'EXPORT': '导出',
    'GENERATE': '生成',
}

MODULES = {
    'PROCUREMENT': '采购申请',
    'BUDGET': '预算管理',
    'TENDER': '招标项目',
    'TEMPLATE': '招标文件',
    'BID': '投标管理',
    'EXPERT': '专家管理',
    'REVIEW': '评审管理',
    'AWARD': '中标管理',
    'CONTRACT': '合同管理',
    'PERFORMANCE': '履约监控',
    'NOTIFICATION': '通知管理',
    'STATISTICS': '统计报告',
    'SYSTEM': '系统',
}


def log_operation(operation_type, module, operator='system', record_id=None, detail=None, ip_address=None, push_to_group=True):
    """
    记录操作日志
    """
    op_type_display = OPERATION_TYPES.get(operation_type, operation_type)
    module_display = MODULES.get(module, module)

    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO operation_logs 
            (operation_type, module, record_id, operator, detail, ip_address, pushed_to_group, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            op_type_display,
            module_display,
            record_id,
            operator,
            detail,
            ip_address,
            1 if push_to_group else 0,
            get_datetime_str()
        ))
        log_id = cursor.lastrowid

    if push_to_group:
        push_to_project_group(log_id, op_type_display, module_display, operator, record_id, detail)

    _write_to_file_log(op_type_display, module_display, operator, record_id, detail)
    return log_id


def push_to_project_group(log_id, op_type, module, operator, record_id, detail):
    """
    模拟推送到项目群（企业微信/钉钉/飞书等）
    """
    message = f"""
📢 【招投标系统操作通知】
━━━━━━━━━━━━━━━━━━
⏰ 时间: {get_datetime_str()}
📋 模块: {module}
🔧 操作: {op_type}
👤 操作人: {operator}
🆔 记录ID: {record_id if record_id else '无'}
📝 详情: {detail if detail else '无'}
━━━━━━━━━━━━━━━━━━
    """.strip()

    print("\n" + "=" * 60)
    print("【推送到项目群】")
    print(message)
    print("=" * 60 + "\n")

    log_file = os.path.join(LOGS_DIR, 'group_messages.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(message + "\n\n")

    return True


def _write_to_file_log(op_type, module, operator, record_id, detail):
    log_file = os.path.join(LOGS_DIR, 'operations.log')
    log_line = f"[{get_datetime_str()}] [{module}] [{op_type}] 操作人:{operator} 记录ID:{record_id} 详情:{detail}\n"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_line)


def query_logs(module=None, operation_type=None, operator=None, start_date=None, end_date=None, limit=100):
    """
    查询操作日志
    """
    sql = "SELECT * FROM operation_logs WHERE 1=1"
    params = []

    if module:
        sql += " AND module = ?"
        params.append(module)
    if operation_type:
        sql += " AND operation_type = ?"
        params.append(operation_type)
    if operator:
        sql += " AND operator LIKE ?"
        params.append(f"%{operator}%")
    if start_date:
        sql += " AND created_at >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND created_at <= ?"
        params.append(end_date + " 23:59:59")

    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with get_cursor() as cursor:
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
