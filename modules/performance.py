"""
履约监控模块 - 监控关键节点，超期预警
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_cursor
from core.utils import get_date_str, parse_date, days_between, get_datetime_str
from config.settings import PERFORMANCE_WARNING_DAYS
from modules.logger import log_operation
from modules.notification import send_performance_warning


def get_contract_milestones(contract_id):
    """获取合同履约里程碑
    """
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT pm.*, c.contract_code, c.total_amount
            FROM performance_milestones pm
            LEFT JOIN contracts c ON pm.contract_id = c.id
            WHERE pm.contract_id = ?
            ORDER BY pm.planned_date
        """, (contract_id,))
        return [dict(row) for row in cursor.fetchall()]


def update_milestone(milestone_id, actual_date=None, status=None, comment=None, operator='project_manager'):
    """更新里程碑状态
    """
    with get_cursor() as cursor:
        updates = []
        params = []
        if actual_date:
            updates.append("actual_date = ?")
            params.append(actual_date)
        if status:
            updates.append("status = ?")
            params.append(status)
        if comment:
            updates.append("comment = ?")
            params.append(comment)
        params.append(milestone_id)

        if updates:
            sql = f"UPDATE performance_milestones SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, params)

            cursor.execute("SELECT * FROM performance_milestones WHERE id = ?", (milestone_id,))
            milestone = cursor.fetchone()

    log_operation(
        operation_type='UPDATE',
        module='PERFORMANCE',
        operator=operator,
        record_id=milestone_id,
        detail=f"更新里程碑: {milestone['milestone_name']} -> {status or milestone['status']}"
    )

    return True


def check_overdue_milestones():
    """检查所有超期里程碑，超期2天自动预警
    """
    today = get_date_str()
    warnings = []

    with get_cursor() as cursor:
        cursor.execute("""
            SELECT pm.*, c.contract_code, c.project_id
            FROM performance_milestones pm
            LEFT JOIN contracts c ON pm.contract_id = c.id
            WHERE pm.status = 'pending' AND pm.warning_sent = 0
        """)
        milestones = cursor.fetchall()

        for ms in milestones:
            ms_dict = dict(ms)
            overdue = days_between(ms_dict['planned_date'], today)
            if overdue >= PERFORMANCE_WARNING_DAYS:
                warnings.append(ms_dict)

                cursor.execute("""
                    UPDATE performance_milestones SET warning_sent = 1 WHERE id = ?
                """, (ms_dict['id'],))

                with get_cursor() as c2:
                    c2.execute("""
                        SELECT s.company_name, s.contact_person FROM awards a
                        LEFT JOIN suppliers s ON a.supplier_id = s.id
                        WHERE a.project_id = ?
                    """, (ms_dict['project_id'],))
                    supplier = c2.fetchone()
                    supplier_name = supplier['company_name'] if supplier else None

                send_performance_warning(
                    ms_dict['contract_code'],
                    ms_dict['milestone_name'],
                    overdue,
                    project_manager='项目经理',
                    supplier=supplier_name
                )

                log_operation(
                    operation_type='WARN',
                    module='PERFORMANCE',
                    operator='system',
                    record_id=ms_dict['id'],
                    detail=f"履约预警: {ms_dict['contract_code']} - {ms_dict['milestone_name']} 超期{overdue}天"
                )

    return warnings


def get_all_contracts(status=None):
    """获取合同列表
    """
    sql = "SELECT * FROM contracts WHERE 1=1"
    params = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY created_at DESC"

    with get_cursor() as cursor:
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def get_contract(contract_id):
    """获取合同详情
    """
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT c.*, tp.project_name, tp.project_code, s.company_name
            FROM contracts c
            LEFT JOIN tender_projects tp ON c.project_id = tp.id
            LEFT JOIN awards a ON c.award_id = a.id
            LEFT JOIN suppliers s ON a.supplier_id = s.id
            WHERE c.id = ?
        """, (contract_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
