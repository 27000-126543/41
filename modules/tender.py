"""
招标项目模块 - 自动生成招标项目，匹配模板，发布
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_cursor
from core.utils import generate_project_code, get_date_str, add_days, get_datetime_str, format_amount
from config.settings import WEIGHT_CONFIG, BIDDING_PERIOD_DAYS, AMOUNT_THRESHOLDS
from modules.logger import log_operation


def get_bidding_period(amount):
    if amount <= AMOUNT_THRESHOLDS['small']:
        return BIDDING_PERIOD_DAYS['small']
    elif amount <= AMOUNT_THRESHOLDS['medium']:
        return BIDDING_PERIOD_DAYS['medium']
    else:
        return BIDDING_PERIOD_DAYS['large']


def match_template(category, amount):
    """
    根据项目类型和金额匹配合适的招标文件模板
    """
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM bid_templates 
            WHERE category = ? AND is_active = 1 
              AND min_amount <= ? AND max_amount > ?
            ORDER BY min_amount DESC LIMIT 1
        """, (category, amount, amount))
        template = cursor.fetchone()

        if not template:
            cursor.execute("""
                SELECT * FROM bid_templates 
                WHERE category = ? AND is_active = 1
                ORDER BY min_amount ASC LIMIT 1
            """, (category,))
            template = cursor.fetchone()

        return dict(template) if template else None


def create_tender_from_request(request_id, operator='system'):
    """
    从已通过的采购申请自动创建招标项目
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM procurement_requests WHERE id = ?", (request_id,))
        request = cursor.fetchone()
        if not request:
            return None, "采购申请不存在"

        if request['status'] != 'approved':
            return None, f"采购申请状态为 {request['status']}，需先通过预算审批"

        cursor.execute("SELECT id FROM tender_projects WHERE request_id = ?", (request_id,))
        if cursor.fetchone():
            return None, "该采购申请已生成招标项目"

        category = request['category']
        amount = request['estimated_amount']
        project_code = generate_project_code(category)
        publish_date = get_date_str()
        bidding_days = get_bidding_period(amount)
        bid_deadline = add_days(publish_date, bidding_days)
        open_bid_date = add_days(bid_deadline, 1)

        weights = WEIGHT_CONFIG.get(category, WEIGHT_CONFIG['default'])

        template = match_template(category, amount)
        template_id = template['id'] if template else None

        cursor.execute("""
            INSERT INTO tender_projects 
            (request_id, project_code, project_name, category, budget_amount,
             publish_date, bid_deadline, open_bid_date, status, template_id,
             weight_technical, weight_commercial, weight_qualification,
             created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?)
        """, (
            request_id, project_code, request['title'], category, amount,
            publish_date, bid_deadline, open_bid_date, template_id,
            weights['technical'], weights['commercial'], weights['qualification'],
            operator, get_datetime_str()
        ))
        project_id = cursor.lastrowid

    log_operation(
        operation_type='CREATE',
        module='TENDER',
        operator=operator,
        record_id=project_id,
        detail=f"生成招标项目: {project_code} - {request['title']}, 预算: {format_amount(amount)}, 投标截止: {bid_deadline}"
    )

    return project_id, project_code


def get_tender_project(project_id):
    """
    获取招标项目详情
    """
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT tp.*, pr.description as request_description, 
                   d.name as department_name, bt.template_name, bt.content as template_content
            FROM tender_projects tp
            LEFT JOIN procurement_requests pr ON tp.request_id = pr.id
            LEFT JOIN departments d ON pr.department_id = d.id
            LEFT JOIN bid_templates bt ON tp.template_id = bt.id
            WHERE tp.id = ?
        """, (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_tender_projects(status=None, category=None, limit=50):
    """
    列出招标项目
    """
    sql = """
        SELECT tp.*, pr.description as request_description, 
               d.name as department_name
        FROM tender_projects tp
        LEFT JOIN procurement_requests pr ON tp.request_id = pr.id
        LEFT JOIN departments d ON pr.department_id = d.id
        WHERE 1=1
    """
    params = []

    if status:
        sql += " AND tp.status = ?"
        params.append(status)
    if category:
        sql += " AND tp.category = ?"
        params.append(category)

    sql += " ORDER BY tp.created_at DESC LIMIT ?"
    params.append(limit)

    with get_cursor() as cursor:
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def publish_tender(project_id, operator='tender_manager'):
    """
    发布招标公告到企业官网和供应商门户
    """
    project = get_tender_project(project_id)
    if not project:
        return False, "招标项目不存在"

    if project['status'] not in ['draft', 'ready']:
        return False, f"当前状态 {project['status']} 无法发布"

    template = project.get('template_content', '')
    if not template:
        template = "标准招标文件模板内容"

    publish_content = f"""
【招标公告】
项目编号: {project['project_code']}
项目名称: {project['project_name']}
项目类别: {project['category']}
预算金额: {format_amount(project['budget_amount'])}
发布日期: {project['publish_date']}
投标截止: {project['bid_deadline']}
开标日期: {project['open_bid_date']}

项目简介:
{project.get('request_description', '无')}

招标文件:
{template}
    """.strip()

    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE tender_projects 
            SET status = 'published', published_to_website = 1, published_to_portal = 1, updated_at = ?
            WHERE id = ?
        """, (get_datetime_str(), project_id))

    log_operation(
        operation_type='PUBLISH',
        module='TENDER',
        operator=operator,
        record_id=project_id,
        detail=f"发布招标公告: {project['project_code']} - {project['project_name']} 到企业官网和供应商门户"
    )

    print("\n" + "=" * 60)
    print("【发布到企业官网】")
    print(publish_content)
    print("=" * 60)
    print("【发布到供应商门户】")
    print(publish_content)
    print("=" * 60 + "\n")

    return True, f"招标项目 {project['project_code']} 已成功发布"


def get_templates():
    """
    获取所有招标文件模板
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM bid_templates WHERE is_active = 1 ORDER BY category, min_amount")
        return [dict(row) for row in cursor.fetchall()]
