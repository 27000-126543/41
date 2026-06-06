"""
专家管理模块 - 专家库、自动分配、回避规则
"""
import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_cursor
from core.utils import get_datetime_str
from config.settings import EXPERT_REVIEW_RULES
from modules.logger import log_operation
from modules.notification import create_notification, send_notification


def get_experts(specialty=None, is_active=True):
    """
    获取专家列表
    """
    sql = "SELECT * FROM experts WHERE 1=1"
    params = []

    if specialty:
        sql += " AND (specialty LIKE ? OR sub_specialty LIKE ?)"
        params.extend([f"%{specialty}%", f"%{specialty}%"])
    if is_active:
        sql += " AND is_active = 1"

    sql += " ORDER BY years_of_experience DESC"

    with get_cursor() as cursor:
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def _check_avoid_rule(expert, supplier_names):
    """
    检查专家回避规则
    """
    avoid_suppliers = (expert.get('avoid_suppliers') or '').split(';')
    avoid_companies = (expert.get('avoid_companies') or '').split(';')

    avoid_list = [s.strip() for s in avoid_suppliers + avoid_companies if s.strip()]

    for supplier_name in supplier_names:
        for avoid in avoid_list:
            if avoid and avoid in supplier_name:
                return False
    return True


def auto_assign_experts(project_id, category=None, num_experts=None, operator='system'):
    """
    按专业和回避规则自动随机分配评审专家
    """
    if num_experts is None:
        num_experts = EXPERT_REVIEW_RULES['min_experts']

    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM tender_projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()
        if not project:
            return None, "招标项目不存在"

        cursor.execute("""
            SELECT s.company_name FROM bids b
            LEFT JOIN suppliers s ON b.supplier_id = s.id
            WHERE b.project_id = ? AND b.status != 'withdrawn'
        """, (project_id,))
        suppliers = [row['company_name'] for row in cursor.fetchall()]

        if not suppliers:
            return None, "没有投标供应商，无法分配专家"

        category_map = {
            'goods': '软件开发;智能硬件;系统集成;网络安全;大数据',
            'engineering': '工程建设',
            'service': '咨询服务;商务评标'
        }
        specialties = category_map.get(category or project['category'], '软件开发').split(';')

        all_experts = []
        for spec in specialties:
            experts = get_experts(specialty=spec)
            all_experts.extend(experts)

        unique_experts = {}
        for exp in all_experts:
            unique_experts[exp['id']] = exp
        all_experts = list(unique_experts.values())

        eligible_experts = [
            exp for exp in all_experts
            if _check_avoid_rule(exp, suppliers)
        ]

        cursor.execute("SELECT expert_id FROM expert_assignments WHERE project_id = ?", (project_id,))
        assigned_ids = {row['expert_id'] for row in cursor.fetchall()}
        eligible_experts = [exp for exp in eligible_experts if exp['id'] not in assigned_ids]

        if len(eligible_experts) < num_experts:
            all_active = [e for e in get_experts() if e['id'] not in assigned_ids]
            eligible_experts = [e for e in all_active if _check_avoid_rule(e, suppliers)]

        if len(eligible_experts) < num_experts:
            return None, f"符合条件的专家不足，需要{num_experts}人，仅有{len(eligible_experts)}人"

        selected = random.sample(eligible_experts, num_experts)

        assigned = []
        for exp in selected:
            try:
                cursor.execute("""
                    INSERT INTO expert_assignments 
                    (project_id, expert_id, assignment_date, status, created_at)
                    VALUES (?, ?, ?, 'assigned', ?)
                """, (project_id, exp['id'], get_datetime_str().split()[0], get_datetime_str()))
                assigned.append(exp)

                subject = f"【专家邀请】请参与{project['project_name']}项目评审"
                content = f"""
尊敬的{exp['name']}专家：

    邀请您参与{project['project_name']}（项目编号：{project['project_code']}）的评审工作。

    开标日期：{project['open_bid_date']}
    项目预算：¥{project['budget_amount']:,.2f}

    请您登录系统进行独立打分。

此致
敬礼！

企业招投标管理系统
                """
                notify_id = create_notification(
                    notification_type='EXPERT_INVITE',
                    recipient_type='expert',
                    recipient_id=exp['id'],
                    recipient_email=exp.get('email'),
                    project_id=project_id,
                    subject=subject,
                    content=content
                )
                send_notification(notify_id)
            except Exception:
                pass

    log_operation(
        operation_type='CREATE',
        module='EXPERT',
        operator=operator,
        record_id=project_id,
        detail=f"自动分配评审专家 {len(assigned)} 人: {', '.join([e['name'] for e in assigned])}"
    )

    return [dict(e) for e in assigned], f"成功分配 {len(assigned)} 位评审专家"


def get_project_experts(project_id):
    """
    获取项目已分配专家
    """
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT ea.*, e.name, e.expert_code, e.specialty, e.sub_specialty,
                   e.title, e.organization, e.phone, e.email
            FROM expert_assignments ea
            LEFT JOIN experts e ON ea.expert_id = e.id
            WHERE ea.project_id = ?
            ORDER BY ea.created_at
        """, (project_id,))
        return [dict(row) for row in cursor.fetchall()]
