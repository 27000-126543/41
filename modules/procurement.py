"""
采购申请模块 - 从各部门提交的采购申请中自动提取需求信息
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_cursor
from core.utils import extract_info_from_text, get_datetime_str, get_date_str
from modules.logger import log_operation


def create_procurement_request(department_id, title, description, category,
                               estimated_amount, required_date=None,
                               contact_person=None, contact_phone=None,
                               attachments=None, submitted_by='system'):
    """
    创建采购申请
    """
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO procurement_requests 
            (department_id, title, description, category, estimated_amount, 
             required_date, contact_person, contact_phone, attachments, submitted_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            department_id, title, description, category, estimated_amount,
            required_date, contact_person, contact_phone, attachments,
            submitted_by, get_datetime_str()
        ))
        request_id = cursor.lastrowid

    log_operation(
        operation_type='CREATE',
        module='PROCUREMENT',
        operator=submitted_by,
        record_id=request_id,
        detail=f"创建采购申请: {title}, 预估金额: ¥{estimated_amount:,.2f}"
    )

    return request_id


def auto_extract_from_submission(raw_text, department_id, submitted_by='system'):
    """
    从提交的原始文本中自动提取需求信息并创建采购申请
    """
    extracted = extract_info_from_text(raw_text)

    title = f"采购申请-{get_date_str()}"
    lines = raw_text.strip().split('\n')
    if lines:
        first_line = lines[0].strip()
        if len(first_line) <= 50:
            title = first_line
        else:
            title = first_line[:50]

    description = raw_text
    category = extracted.get('category', 'goods')
    estimated_amount = extracted.get('amount', 0)
    required_date = extracted.get('date')

    if estimated_amount == 0:
        return None, "无法提取预估金额，请明确标注金额信息"

    request_id = create_procurement_request(
        department_id=department_id,
        title=title,
        description=description,
        category=category,
        estimated_amount=estimated_amount,
        required_date=required_date,
        submitted_by=submitted_by
    )

    return request_id, "采购申请创建成功，已自动提取需求信息"


def get_procurement_request(request_id):
    """
    获取采购申请详情
    """
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT pr.*, d.name as department_name 
            FROM procurement_requests pr
            LEFT JOIN departments d ON pr.department_id = d.id
            WHERE pr.id = ?
        """, (request_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_procurement_requests(status=None, department_id=None, limit=50):
    """
    列出采购申请
    """
    sql = """
        SELECT pr.*, d.name as department_name 
        FROM procurement_requests pr
        LEFT JOIN departments d ON pr.department_id = d.id
        WHERE 1=1
    """
    params = []

    if status:
        sql += " AND pr.status = ?"
        params.append(status)
    if department_id:
        sql += " AND pr.department_id = ?"
        params.append(department_id)

    sql += " ORDER BY pr.created_at DESC LIMIT ?"
    params.append(limit)

    with get_cursor() as cursor:
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def get_departments():
    """
    获取部门列表
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM departments ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]
