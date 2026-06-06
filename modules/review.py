"""
评审打分模块 - 专家独立打分，自动汇总去掉最高最低分
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_cursor
from core.utils import get_datetime_str, format_amount
from config.settings import EXPERT_REVIEW_RULES, WEIGHT_CONFIG
from modules.logger import log_operation


def expert_submit_score(assignment_id, bid_id, qualification_score,
                        technical_score, commercial_score, comment=None,
                        operator='expert'):
    """
    专家独立打分
    """
    for score, name in [(qualification_score, '资质分'), (technical_score, '技术分'), (commercial_score, '商务分')]:
        if score < 0 or score > 100:
            return False, f"{name}必须在0-100之间"

    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM expert_assignments WHERE id = ?", (assignment_id,))
        assignment = cursor.fetchone()
        if not assignment:
            return False, "专家分配记录不存在"

        cursor.execute("SELECT * FROM bids WHERE id = ?", (bid_id,))
        bid = cursor.fetchone()
        if not bid:
            return False, "投标记录不存在"

        if bid['project_id'] != assignment['project_id']:
            return False, "投标与项目不匹配"

        try:
            cursor.execute("""
                INSERT INTO expert_scores 
                (assignment_id, bid_id, qualification_score, technical_score, commercial_score, comment, scored_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (assignment_id, bid_id, qualification_score, technical_score,
                  commercial_score, comment, get_datetime_str()))
        except Exception:
            cursor.execute("""
                UPDATE expert_scores 
                SET qualification_score = ?, technical_score = ?, commercial_score = ?, comment = ?, scored_at = ?
                WHERE assignment_id = ? AND bid_id = ?
            """, (qualification_score, technical_score, commercial_score, comment,
                  get_datetime_str(), assignment_id, bid_id))

    log_operation(
        operation_type='SCORE',
        module='REVIEW',
        operator=operator,
        record_id=bid_id,
        detail=f"专家打分: 技术={technical_score}, 商务={commercial_score}, 资质={qualification_score}"
    )

    return True, "打分成功"


def _trim_scores(scores):
    """
    去掉最高分和最低分
    """
    if len(scores) <= 2:
        return scores
    sorted_scores = sorted(scores)
    if EXPERT_REVIEW_RULES['remove_highest']:
        sorted_scores = sorted_scores[:-1]
    if EXPERT_REVIEW_RULES['remove_lowest']:
        sorted_scores = sorted_scores[1:]
    return sorted_scores


def aggregate_expert_scores(project_id, operator='review_manager'):
    """
    汇总所有专家打分，去掉最高最低分后取平均
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM tender_projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()
        if not project:
            return None, "招标项目不存在"
        project = dict(project)

        cursor.execute("""
            SELECT es.*, ea.expert_id, e.name as expert_name
            FROM expert_scores es
            LEFT JOIN expert_assignments ea ON es.assignment_id = ea.id
            LEFT JOIN experts e ON ea.expert_id = e.id
            WHERE ea.project_id = ?
        """, (project_id,))
        all_scores = cursor.fetchall()

        if not all_scores:
            return None, "暂无专家打分记录"

        cursor.execute("SELECT * FROM bids WHERE project_id = ?", (project_id,))
        bids = cursor.fetchall()

        cursor.execute("""
            SELECT s.* FROM suppliers s
            WHERE s.id IN (SELECT supplier_id FROM bids WHERE project_id = ?)
        """, (project_id,))
        suppliers = {s['id']: dict(s) for s in cursor.fetchall()}

        w_t = project['weight_technical']
        w_c = project['weight_commercial']
        w_q = project['weight_qualification']

        results = []
        for bid in bids:
            bid_scores = [s for s in all_scores if s['bid_id'] == bid['id']]
            if not bid_scores:
                continue

            tech_scores = [s['technical_score'] for s in bid_scores if s['technical_score'] is not None]
            comm_scores = [s['commercial_score'] for s in bid_scores if s['commercial_score'] is not None]
            qual_scores = [s['qualification_score'] for s in bid_scores if s['qualification_score'] is not None]

            tech_trimmed = _trim_scores(tech_scores)
            comm_trimmed = _trim_scores(comm_scores)
            qual_trimmed = _trim_scores(qual_scores)

            tech_avg = sum(tech_trimmed) / len(tech_trimmed) if tech_trimmed else 0
            comm_avg = sum(comm_trimmed) / len(comm_trimmed) if comm_trimmed else 0
            qual_avg = sum(qual_trimmed) / len(qual_trimmed) if qual_trimmed else 0

            final_score = tech_avg * w_t + comm_avg * w_c + qual_avg * w_q

            supplier = suppliers.get(bid['supplier_id'], {})
            results.append({
                'bid_id': bid['id'],
                'supplier_id': bid['supplier_id'],
                'supplier_name': supplier.get('company_name', ''),
                'bid_amount': bid['bid_amount'],
                'technical_score': round(tech_avg, 2),
                'commercial_score': round(comm_avg, 2),
                'qualification_score': round(qual_avg, 2),
                'final_score': round(final_score, 2),
                'expert_count': len(bid_scores),
                'raw_tech_scores': tech_scores,
                'raw_comm_scores': comm_scores,
                'raw_qual_scores': qual_scores,
            })

        results.sort(key=lambda x: x['final_score'], reverse=True)
        for i, r in enumerate(results):
            r['ranking'] = i + 1
            cursor.execute("""
                UPDATE bids 
                SET technical_score = ?, commercial_score = ?, qualification_score = ?,
                    final_score = ?, ranking = ?, status = 'reviewed'
                WHERE id = ?
            """, (
                r['technical_score'], r['commercial_score'], r['qualification_score'],
                r['final_score'], r['ranking'], r['bid_id']
            ))

        cursor.execute("""
            UPDATE tender_projects SET status = 'reviewed', updated_at = ? WHERE id = ?
        """, (get_datetime_str(), project_id))

    log_operation(
        operation_type='SCORE',
        module='REVIEW',
        operator=operator,
        record_id=project_id,
        detail=f"专家评分汇总完成: 共 {len(results)} 家供应商，去掉最高最低分后取平均"
    )

    return results, "评分汇总完成"


def generate_review_report(project_id, operator='review_manager'):
    """
    生成评审报告
    """
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT tp.*, pr.description as request_description, d.name as department_name
            FROM tender_projects tp
            LEFT JOIN procurement_requests pr ON tp.request_id = pr.id
            LEFT JOIN departments d ON pr.department_id = d.id
            WHERE tp.id = ?
        """, (project_id,))
        project = cursor.fetchone()
        if not project:
            return None, "招标项目不存在"
        project = dict(project)

        cursor.execute("""
            SELECT b.*, s.company_name, s.contact_person, s.contact_phone
            FROM bids b
            LEFT JOIN suppliers s ON b.supplier_id = s.id
            WHERE b.project_id = ?
            ORDER BY COALESCE(b.ranking, 9999)
        """, (project_id,))
        bids = [dict(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT ea.*, e.name, e.specialty, e.title
            FROM expert_assignments ea
            LEFT JOIN experts e ON ea.expert_id = e.id
            WHERE ea.project_id = ?
        """, (project_id,))
        experts = [dict(row) for row in cursor.fetchall()]

    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("                    招 标 项 目 评 审 报 告")
    report_lines.append("=" * 70)
    report_lines.append("")
    report_lines.append(f"项目编号：{project['project_code']}")
    report_lines.append(f"项目名称：{project['project_name']}")
    report_lines.append(f"项目类别：{project['category']}")
    report_lines.append(f"采购部门：{project.get('department_name', '')}")
    report_lines.append(f"预算金额：{format_amount(project['budget_amount'])}")
    report_lines.append(f"发布日期：{project['publish_date']}")
    report_lines.append(f"投标截止：{project['bid_deadline']}")
    report_lines.append(f"开标日期：{project['open_bid_date']}")
    report_lines.append("")
    report_lines.append("-" * 70)
    report_lines.append("一、评审委员会组成")
    report_lines.append("-" * 70)
    for i, exp in enumerate(experts, 1):
        report_lines.append(f"  {i}. {exp['name']} - {exp.get('title', '')} ({exp.get('specialty', '')})")
    report_lines.append("")
    report_lines.append("-" * 70)
    report_lines.append(f"二、评分权重设置（技术{project['weight_technical']*100:.0f}% / 商务{project['weight_commercial']*100:.0f}% / 资质{project['weight_qualification']*100:.0f}%）")
    report_lines.append("-" * 70)
    report_lines.append("")
    report_lines.append("-" * 70)
    report_lines.append("三、投标供应商评分汇总表（已去高低分取平均）")
    report_lines.append("-" * 70)
    report_lines.append(f"{'排名':<6}{'供应商名称':<25}{'报价(元)':<15}{'技术分':<10}{'商务分':<10}{'资质分':<10}{'综合分':<10}")
    report_lines.append("-" * 86)
    for bid in bids:
        if bid['ranking']:
            report_lines.append(
                f"{bid['ranking']:<6}"
                f"{bid['company_name'][:23]:<25}"
                f"{bid['bid_amount']:<15,.2f}"
                f"{bid.get('technical_score', 0):<10.2f}"
                f"{bid.get('commercial_score', 0):<10.2f}"
                f"{bid.get('qualification_score', 0):<10.2f}"
                f"{bid.get('final_score', 0):<10.2f}"
            )
    report_lines.append("")
    report_lines.append("-" * 70)
    report_lines.append("四、评审结论")
    report_lines.append("-" * 70)
    if bids and bids[0]['ranking'] == 1:
        winner = bids[0]
        report_lines.append(f"  推荐中标供应商：{winner['company_name']}")
        report_lines.append(f"  中标金额：{format_amount(winner['bid_amount'])}")
        report_lines.append(f"  综合得分：{winner.get('final_score', 0):.2f}")
    report_lines.append("")
    report_lines.append("=" * 70)
    report_lines.append(f"报告生成时间：{get_datetime_str()}")
    report_lines.append("=" * 70)

    report_content = "\n".join(report_lines)

    with get_cursor() as cursor:
        cursor.execute("DELETE FROM review_reports WHERE project_id = ?", (project_id,))
        cursor.execute("""
            INSERT INTO review_reports (project_id, report_content, generated_at, created_by)
            VALUES (?, ?, ?, ?)
        """, (project_id, report_content, get_datetime_str(), operator))

    log_operation(
        operation_type='GENERATE',
        module='REVIEW',
        operator=operator,
        record_id=project_id,
        detail=f"生成评审报告: {project['project_code']}"
    )

    return report_content, "评审报告生成成功"


def get_review_report(project_id):
    """
    获取评审报告
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM review_reports WHERE project_id = ?", (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
