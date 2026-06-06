"""
中标管理模块 - 定标、通知、合同
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_cursor
from core.utils import get_datetime_str, get_date_str, add_days, generate_contract_code, format_amount
from config.settings import CONTRACTS_DIR
from modules.logger import log_operation
from modules.notification import send_award_notice, send_thank_you
from modules.notification import create_notification, send_notification


def determine_winner(project_id, operator='review_committee'):
    """
    确定中标供应商（按综合排名第一）
    """
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT b.*, s.company_name, s.contact_person, s.contact_phone, s.contact_email
            FROM bids b
            LEFT JOIN suppliers s ON b.supplier_id = s.id
            WHERE b.project_id = ? AND b.status IN ('evaluated', 'reviewed')
            ORDER BY b.ranking ASC LIMIT 1
        """, (project_id,))
        winner = cursor.fetchone()
        if not winner:
            return None, "未找到合格的中标候选"

        cursor.execute("SELECT * FROM tender_projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()
        if not project:
            return None, "招标项目不存在"

        cursor.execute("SELECT id FROM awards WHERE project_id = ?", (project_id,))
        if cursor.fetchone():
            return None, "该项目已完成定标"

        cursor.execute("""
            INSERT INTO awards 
            (project_id, winning_bid_id, supplier_id, award_amount, award_date, status)
            VALUES (?, ?, ?, ?, ?, 'awarded')
        """, (project_id, winner['id'], winner['supplier_id'], winner['bid_amount'], get_date_str()))
        award_id = cursor.lastrowid

        cursor.execute("""
            UPDATE tender_projects SET status = 'awarded', updated_at = ? WHERE id = ?
        """, (get_datetime_str(), project_id))

    winner_dict = dict(winner)
    log_operation(
        operation_type='AWARD',
        module='AWARD',
        operator=operator,
        record_id=project_id,
        detail=f"定标完成: {winner_dict['company_name']}, 中标金额: {format_amount(winner_dict['bid_amount'])}"
    )

    return award_id, winner_dict


def notify_all_bidders(project_id, operator='system'):
    """
    向所有投标方发送通知（中标通知书+感谢信）
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM tender_projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()

        cursor.execute("""
            SELECT b.*, s.*
            FROM bids b
            LEFT JOIN suppliers s ON b.supplier_id = s.id
            WHERE b.project_id = ?
        """, (project_id,))
        all_bids = cursor.fetchall()

        cursor.execute("SELECT * FROM awards WHERE project_id = ?", (project_id,))
        award = cursor.fetchone()

    if not project or not all_bids:
        return False, "无投标数据"

    notified = 0
    winner_id = award['supplier_id'] if award else None

    for bid in all_bids:
        supplier = {
            'id': bid['supplier_id'],
            'company_name': bid['company_name'],
            'contact_email': bid['contact_email']
        }
        if winner_id and bid['supplier_id'] == winner_id:
            contract_code = generate_contract_code()
            send_award_notice(project_id, supplier, award['award_amount'], contract_code)
        else:
            send_thank_you(project_id, supplier, project['project_name'])
        notified += 1

        with get_cursor() as cursor:
            cursor.execute("UPDATE awards SET notification_sent = 1 WHERE project_id = ?", (project_id,))
            cursor.execute("UPDATE bids SET status = 'notified' WHERE project_id = ? AND supplier_id = ?", (project_id, bid['supplier_id']))

    log_operation(
        operation_type='NOTIFY',
        module='AWARD',
        operator=operator,
        record_id=project_id,
        detail=f"已向 {notified} 家投标方发送通知（中标通知书/感谢信"
    )

    return True, f"已向 {notified} 家投标方发送通知"


def generate_contract(project_id, operator='contract_manager'):
    """
    生成电子合同草稿
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM awards WHERE project_id = ?", (project_id,))
        award = cursor.fetchone()
        if not award:
            return None, "未找到中标记录"

        cursor.execute("SELECT * FROM tender_projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()

        cursor.execute("SELECT * FROM suppliers WHERE id = ?", (award['supplier_id'],))
        supplier = cursor.fetchone()

    contract_code = generate_contract_code()
    start_date = get_date_str()
    end_date = add_days(start_date, 180)

    contract_content = f"""
═══════════════════════════════════════════════════════════════════
                        合 同 协 议 书
═══════════════════════════════════════════════════════════════════

合同编号：{contract_code}
签订日期：{start_date}

甲方（采购方）：
    企业名称：XX集团有限公司
    地址：XX市XX区XX路XX号
    法定代表人：XXX
    联系人：XXX
    联系电话：XXX-XXXXXXX

乙方（供应方）：
    企业名称：{supplier['company_name']}
    统一社会信用代码：{supplier['unified_social_code']}
    地址：{supplier['address']}
    法定代表人：{supplier['legal_representative']}
    联系人：{supplier['contact_person']}
    联系电话：{supplier['contact_phone']}

═══════════════════════════════════════════════════════════════════

第一条 项目概况
    1.1 项目编号：{project['project_code']}
    1.2 项目名称：{project['project_name']}
    1.3 项目类别：{project['category']}

第二条 合同金额
    2.1 合同总金额：人民币（大写）{_num_to_chinese(award['award_amount'])}元整
    2.2 小写金额：¥{award['award_amount']:,.2f}元

第三条 合同期限
    3.1 合同生效日期：{start_date}
    3.2 合同完成日期：{end_date}

第四条 付款方式
    4.1 预付款：合同签订后支付30%
    4.2 进度款：交付验收合格后支付60%
    4.3 质保金：验收满一年后支付10%

第五条 交付与验收
    5.1 交付时间：合同签订后30日内
    5.2 验收标准：按国家相关标准执行

第六条 违约责任
    6.1 任何一方违约应承担相应违约责任

第七条 争议解决
    7.1 协商不成，协商不成向甲方所在地人民法院诉讼

第八条 其他约定
    8.1 本合同一式四份，甲乙双方各执两份

═══════════════════════════════════════════════════════════════════

甲方（盖章）：                乙方（盖章）：
法定代表人：                    法定代表人：
日期：                            日期：

═══════════════════════════════════════════════════════════════════
    """.strip()

    with get_cursor() as cursor:
        try:
            cursor.execute("""
                INSERT INTO contracts 
                (award_id, project_id, contract_code, contract_content, start_date, end_date, total_amount, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'draft')
            """, (award['id'], project_id, contract_code, contract_content, start_date, end_date, award['award_amount']))
            contract_id = cursor.lastrowid

            cursor.execute("UPDATE awards SET contract_generated = 1 WHERE id = ?", (award['id'],))
        except Exception as e:
            return None, f"合同生成失败: {str(e)}"

    contract_file = os.path.join(CONTRACTS_DIR, f"{contract_code}.txt")
    with open(contract_file, 'w', encoding='utf-8') as f:
        f.write(contract_content)

    _create_performance_milestones(contract_id, start_date, end_date)

    log_operation(
        operation_type='GENERATE',
        module='CONTRACT',
        operator=operator,
        record_id=contract_id,
        detail=f"生成合同草稿: {contract_code}, 金额: {format_amount(award['award_amount'])}"
    )

    return contract_content, f"合同 {contract_code} 已生成"


def _create_performance_milestones(contract_id, start_date, end_date):
    """
    创建履约里程碑
    """
    milestones = [
        ('货物/服务交付', add_days(start_date, 30), 'delivery'),
        ('项目验收', add_days(start_date, 60), 'acceptance'),
        ('最终付款', add_days(start_date, 90), 'payment'),
    ]
    with get_cursor() as cursor:
        for name, date, mtype in milestones:
            cursor.execute("""
                INSERT INTO performance_milestones 
                (contract_id, milestone_name, planned_date, milestone_type, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (contract_id, name, date, mtype))


def archive_losing_bids(project_id, operator='system'):
    """
    归档未中标方历史数据
    """
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE bids SET status = 'archived' 
            WHERE project_id = ? AND status != 'winning'
        """, (project_id,))
        updated = cursor.rowcount

    log_operation(
        operation_type='ARCHIVE',
        module='AWARD',
        operator=operator,
        record_id=project_id,
        detail=f"归档未中标投标: 共 {updated} 条记录"
    )
    return updated


def get_award(project_id):
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT a.*, s.company_name, s.contact_person, tp.project_name, tp.project_code
            FROM awards a
            LEFT JOIN suppliers s ON a.supplier_id = s.id
            LEFT JOIN tender_projects tp ON a.project_id = tp.id
            WHERE a.project_id = ?
        """, (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def _num_to_chinese(num):
    """数字转中文大写金额"""
    digits = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
    units = ['', '拾', '佰', '仟', '万', '亿']
    num = int(num)
    if num == 0:
        return '零'
    result = ''
    unit_idx = 0
    while num > 0:
        digit = num % 10
        if digit > 0:
            result = digits[digit] + units[unit_idx if unit_idx < len(units) else len(units) - 1] + result
        elif result and not result.startswith('零'):
            result = '零' + result
        num //= 10
        unit_idx += 1
    if result.endswith('零'):
        result = result[:-1]
    return result
