"""
投标管理模块 - 接收投标、自动解密、自动排名
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_cursor
from core.utils import encrypt_content, decrypt_content, get_datetime_str, format_amount
from modules.logger import log_operation


def submit_bid(project_id, supplier_id, bid_amount, delivery_date=None,
               bid_content=None, operator='supplier'):
    """
    供应商提交投标（投标内容自动加密存储）
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM tender_projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()
        if not project:
            return None, "招标项目不存在"

        if project['status'] != 'published':
            return None, f"项目状态 {project['status']}，不可投标"

        cursor.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
        supplier = cursor.fetchone()
        if not supplier:
            return None, "供应商不存在"

        if supplier['status'] != 'active':
            return None, "供应商状态异常"

        cursor.execute("SELECT id FROM bids WHERE project_id = ? AND supplier_id = ?", (project_id, supplier_id))
        if cursor.fetchone():
            return None, "该供应商已提交投标"

        encrypted = encrypt_content(bid_content or f"投标内容-{supplier['company_name']}")

        cursor.execute("""
            INSERT INTO bids 
            (project_id, supplier_id, bid_amount, delivery_date, encrypted_content, status, submitted_at)
            VALUES (?, ?, ?, ?, ?, 'submitted', ?)
        """, (project_id, supplier_id, bid_amount, delivery_date, encrypted, get_datetime_str()))
        bid_id = cursor.lastrowid

    log_operation(
        operation_type='SUBMIT',
        module='BID',
        operator=supplier['company_name'],
        record_id=bid_id,
        detail=f"提交投标: 项目ID={project_id}, 供应商={supplier['company_name']}, 金额={format_amount(bid_amount)}"
    )

    return bid_id, "投标成功"


def decrypt_all_bids(project_id, operator='tender_manager'):
    """
    投标截止后自动解密所有标书
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM tender_projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()
        if not project:
            return False, "招标项目不存在"

        cursor.execute("SELECT * FROM bids WHERE project_id = ?", (project_id,))
        bids = cursor.fetchall()

        if not bids:
            return False, "没有投标记录"

        decrypted_count = 0
        for bid in bids:
            if bid['status'] != 'decrypted':
                decrypted = decrypt_content(bid['encrypted_content'])
                cursor.execute("""
                    UPDATE bids 
                    SET decrypted_content = ?, decrypted_at = ?, status = 'decrypted'
                    WHERE id = ?
                """, (decrypted, get_datetime_str(), bid['id']))
                decrypted_count += 1

        cursor.execute("""
            UPDATE tender_projects SET status = 'decrypted', updated_at = ? WHERE id = ?
        """, (get_datetime_str(), project_id))

    log_operation(
        operation_type='OPEN',
        module='BID',
        operator=operator,
        record_id=project_id,
        detail=f"开标解密: 项目 {project['project_code']} 共解密 {decrypted_count} 份投标文件"
    )

    return True, f"成功解密 {decrypted_count} 份投标文件"


def calculate_bid_scores(project_id):
    """
    按预设权重自动计算投标基础分数（不包含专家评分）
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM tender_projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()
        if not project:
            return None

        w_t = project['weight_technical']
        w_c = project['weight_commercial']
        w_q = project['weight_qualification']

        cursor.execute("SELECT * FROM bids WHERE project_id = ? AND status != 'withdrawn'", (project_id,))
        bids = cursor.fetchall()
        if not bids:
            return None

        bid_list = [dict(b) for b in bids]
        amounts = [b['bid_amount'] for b in bid_list]
        min_amount = min(amounts)
        max_amount = max(amounts)

        cursor.execute("SELECT * FROM suppliers WHERE id IN ({})".format(
            ','.join('?' * len(bid_list))
        ), [b['supplier_id'] for b in bid_list])
        suppliers = {s['id']: dict(s) for s in cursor.fetchall()}

        results = []
        for bid in bid_list:
            supplier = suppliers.get(bid['supplier_id'], {})
            if max_amount > min_amount:
                commercial_score = 60 + 40 * (max_amount - bid['bid_amount']) / (max_amount - min_amount)
            else:
                commercial_score = 100

            qualification_score = min(100, max(0, supplier.get('credit_score', 60) * 1.05))
            technical_score = 75 + (supplier.get('years_of_experience', 0) if 'years_of_experience' in supplier else 5)
            technical_score = min(100, technical_score)

            final_score = (technical_score * w_t +
                          commercial_score * w_c +
                          qualification_score * w_q)

            results.append({
                'bid_id': bid['id'],
                'supplier_id': bid['supplier_id'],
                'supplier_name': supplier.get('company_name', ''),
                'bid_amount': bid['bid_amount'],
                'technical_score': round(technical_score, 2),
                'commercial_score': round(commercial_score, 2),
                'qualification_score': round(qualification_score, 2),
                'final_score': round(final_score, 2)
            })

        results.sort(key=lambda x: x['final_score'], reverse=True)
        for i, r in enumerate(results):
            r['ranking'] = i + 1

        return results


def save_bid_rankings(project_id, results, operator='tender_manager'):
    """
    保存投标排名结果
    """
    with get_cursor() as cursor:
        for r in results:
            cursor.execute("""
                UPDATE bids 
                SET technical_score = ?, commercial_score = ?, qualification_score = ?,
                    final_score = ?, ranking = ?, status = 'evaluated'
                WHERE id = ?
            """, (
                r['technical_score'], r['commercial_score'], r['qualification_score'],
                r['final_score'], r['ranking'], r['bid_id']
            ))

        cursor.execute("""
            UPDATE tender_projects SET status = 'evaluated', updated_at = ? WHERE id = ?
        """, (get_datetime_str(), project_id))

    log_operation(
        operation_type='SCORE',
        module='BID',
        operator=operator,
        record_id=project_id,
        detail=f"完成自动评分排名: 共 {len(results)} 家投标供应商"
    )


def get_project_bids(project_id):
    """
    获取项目所有投标
    """
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT b.*, s.company_name, s.contact_person, s.contact_phone, s.credit_score, s.qualification_level
            FROM bids b
            LEFT JOIN suppliers s ON b.supplier_id = s.id
            WHERE b.project_id = ?
            ORDER BY COALESCE(b.ranking, 9999), b.bid_amount ASC
        """, (project_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_suppliers():
    """
    获取供应商列表
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM suppliers WHERE status = 'active' ORDER BY credit_score DESC")
        return [dict(row) for row in cursor.fetchall()]
