"""
预算校验模块 - 校验采购申请的预算额度
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_cursor
from core.utils import get_datetime_str
from modules.logger import log_operation
from modules.notification import create_notification, send_notification


def check_department_budget(department_id, amount):
    """
    检查部门预算是否足够
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM departments WHERE id = ?", (department_id,))
        dept = cursor.fetchone()
        if not dept:
            return False, "部门不存在", 0, 0

        available = dept['budget_limit'] - dept['budget_used']
        enough = available >= amount

        return enough, available, dept['budget_limit'], dept['budget_used']


def approve_budget(request_id, operator='budget_manager'):
    """
    审批预算 - 自动校验并更新
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM procurement_requests WHERE id = ?", (request_id,))
        request = cursor.fetchone()
        if not request:
            return False, "采购申请不存在"

        if request['status'] != 'pending':
            return False, f"当前状态为 {request['status']}，无法审批"

        amount = request['estimated_amount']
        dept_id = request['department_id']

        enough, available, budget_limit, budget_used = check_department_budget(dept_id, amount)

        if not enough:
            rejection_reason = f"预算不足！部门剩余预算: ¥{available:,.2f}，申请金额: ¥{amount:,.2f}"
            cursor.execute("""
                UPDATE procurement_requests 
                SET status = 'rejected', budget_approved = 0, rejection_reason = ?, updated_at = ?
                WHERE id = ?
            """, (rejection_reason, get_datetime_str(), request_id))

            log_operation(
                operation_type='REJECT',
                module='BUDGET',
                operator=operator,
                record_id=request_id,
                detail=rejection_reason
            )

            _send_budget_warning(request_id, request['title'], amount, available)

            return False, rejection_reason

        cursor.execute("""
            UPDATE departments SET budget_used = budget_used + ? WHERE id = ?
        """, (amount, dept_id))

        cursor.execute("""
            UPDATE procurement_requests 
            SET status = 'approved', budget_approved = 1, updated_at = ?
            WHERE id = ?
        """, (get_datetime_str(), request_id))

    log_operation(
        operation_type='APPROVE',
        module='BUDGET',
        operator=operator,
        record_id=request_id,
        detail=f"预算审批通过: {request['title']}, 金额: ¥{amount:,.2f}, 部门剩余预算: ¥{available - amount:,.2f}"
    )

    return True, "预算审批通过"


def reject_budget(request_id, reason, operator='budget_manager'):
    """
    驳回预算申请
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM procurement_requests WHERE id = ?", (request_id,))
        request = cursor.fetchone()
        if not request:
            return False, "采购申请不存在"

        cursor.execute("""
            UPDATE procurement_requests 
            SET status = 'rejected', budget_approved = 0, rejection_reason = ?, updated_at = ?
            WHERE id = ?
        """, (reason, get_datetime_str(), request_id))

    log_operation(
        operation_type='REJECT',
        module='BUDGET',
        operator=operator,
        record_id=request_id,
        detail=f"预算驳回: {request['title']}, 原因: {reason}"
    )

    return True, "已驳回"


def _send_budget_warning(request_id, title, amount, available):
    subject = f"【预算预警】采购申请预算不足"
    content = f"""
采购申请：{title}
申请金额：¥{amount:,.2f}
部门剩余预算：¥{available:,.2f}
差额：¥{amount - available:,.2f}

请相关部门协调处理。
    """.strip()
    notify_id = create_notification(
        notification_type='BUDGET_WARNING',
        recipient_type='department_manager',
        project_id=request_id,
        subject=subject,
        content=content
    )
    send_notification(notify_id)


def get_budget_overview():
    """
    获取预算总览
    """
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT d.*, 
                   (d.budget_limit - d.budget_used) as available_budget,
                   ROUND(CASE WHEN d.budget_limit > 0 THEN d.budget_used * 100.0 / d.budget_limit ELSE 0 END, 2) as usage_percent
            FROM departments d
            ORDER BY usage_percent DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
