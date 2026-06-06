"""
查询导出模块 - 组合查询、批量导出
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_cursor
from core.utils import format_amount, get_datetime_str
from config.settings import EXPORTS_DIR
from modules.logger import log_operation
from modules.statistics import export_to_excel


def search_projects(keyword=None, min_amount=None, max_amount=None,
                    status=None, start_date=None, end_date=None, category=None, limit=500):
    """
    按项目名称、金额区间、状态、时间段组合查询
    """
    sql = """
        SELECT DISTINCT
            tp.id,
            tp.project_code,
            tp.project_name,
            tp.category,
            tp.budget_amount,
            tp.status,
            tp.publish_date,
            tp.bid_deadline,
            tp.created_at,
            d.name as department_name,
            a.award_amount as final_amount,
            s.company_name as winner_name
        FROM tender_projects tp
        LEFT JOIN procurement_requests pr ON tp.request_id = pr.id
        LEFT JOIN departments d ON pr.department_id = d.id
        LEFT JOIN awards a ON tp.id = a.project_id
        LEFT JOIN suppliers s ON a.supplier_id = s.id
        WHERE 1=1
    """
    params = []

    if keyword:
        sql += " AND (tp.project_name LIKE ? OR tp.project_code LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if min_amount is not None:
        sql += " AND tp.budget_amount >= ?"
        params.append(min_amount)
    if max_amount is not None:
        sql += " AND tp.budget_amount <= ?"
        params.append(max_amount)
    if status:
        sql += " AND tp.status = ?"
        params.append(status)
    if category:
        sql += " AND tp.category = ?"
        params.append(category)
    if start_date:
        sql += " AND tp.created_at >= ?"
        params.append(start_date + " 00:00:00")
    if end_date:
        sql += " AND tp.created_at <= ?"
        params.append(end_date + " 23:59:59")

    sql += " ORDER BY tp.created_at DESC LIMIT ?"
    params.append(limit)

    with get_cursor() as cursor:
        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]

    for r in results:
        r['budget_amount_display'] = format_amount(r['budget_amount'])
        r['final_amount_display'] = format_amount(r['final_amount']) if r['final_amount'] else '-'
        r['saved_amount'] = (r['budget_amount'] - r['final_amount']) if r['final_amount'] else 0
        r['saved_amount_display'] = format_amount(r['saved_amount']) if r['saved_amount'] > 0 else '-'

    return results


def get_bid_details(project_ids=None):
    """
    获取投标明细（支持批量导出）
    """
    if not project_ids:
        sql = """
            SELECT 
                tp.project_code,
                tp.project_name,
                tp.category,
                tp.budget_amount,
                s.company_name as bidder_name,
                s.qualification_level,
                s.credit_score,
                b.bid_amount,
                b.delivery_date,
                b.technical_score,
                b.commercial_score,
                b.qualification_score,
                b.final_score,
                b.ranking,
                b.status as bid_status,
                b.submitted_at
            FROM bids b
            LEFT JOIN tender_projects tp ON b.project_id = tp.id
            LEFT JOIN suppliers s ON b.supplier_id = s.id
            ORDER BY tp.project_code, b.ranking
        """
        params = []
    else:
        placeholders = ','.join('?' * len(project_ids))
        sql = f"""
            SELECT 
                tp.project_code,
                tp.project_name,
                tp.category,
                tp.budget_amount,
                s.company_name as bidder_name,
                s.qualification_level,
                s.credit_score,
                b.bid_amount,
                b.delivery_date,
                b.technical_score,
                b.commercial_score,
                b.qualification_score,
                b.final_score,
                b.ranking,
                b.status as bid_status,
                b.submitted_at
            FROM bids b
            LEFT JOIN tender_projects tp ON b.project_id = tp.id
            LEFT JOIN suppliers s ON b.supplier_id = s.id
            WHERE b.project_id IN ({placeholders})
            ORDER BY tp.project_code, b.ranking
        """
        params = project_ids

    with get_cursor() as cursor:
        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]

    for r in results:
        r['bid_amount_display'] = format_amount(r['bid_amount'])
        r['budget_amount_display'] = format_amount(r['budget_amount'])

    return results


def export_bid_details(project_ids=None, filename=None):
    """
    批量导出投标明细
    """
    details = get_bid_details(project_ids)

    if not filename:
        filename = f"bid_details_{get_datetime_str().replace(' ', '_').replace(':', '-')}.xlsx"

    filepath = export_to_excel(details, filename, sheet_name='投标明细')

    log_operation(
        operation_type='EXPORT',
        module='SYSTEM',
        operator='system',
        record_id=None,
        detail=f"批量导出投标明细: 共 {len(details)} 条记录 -> {filepath}"
    )

    return filepath, details


def export_projects(keyword=None, min_amount=None, max_amount=None,
                    status=None, start_date=None, end_date=None, category=None, filename=None):
    """
    按查询条件导出项目列表
    """
    projects = search_projects(keyword, min_amount, max_amount, status, start_date, end_date, category)

    if not filename:
        filename = f"projects_{get_datetime_str().replace(' ', '_').replace(':', '-')}.xlsx"

    filepath = export_to_excel(projects, filename, sheet_name='项目列表')

    log_operation(
        operation_type='EXPORT',
        module='SYSTEM',
        operator='system',
        record_id=None,
        detail=f"导出项目列表: 共 {len(projects)} 条记录 -> {filepath}"
    )

    return filepath, projects
