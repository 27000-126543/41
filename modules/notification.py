"""
通知模块 - 邮件、站内信、消息推送
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_cursor
from core.utils import get_datetime_str
from modules.logger import log_operation


NOTIFICATION_TYPES = {
    'AWARD_NOTICE': '中标通知书',
    'THANK_YOU': '未中标感谢信',
    'PERFORMANCE_WARNING': '履约预警',
    'BUDGET_WARNING': '预算预警',
    'EXPERT_INVITE': '专家邀请',
    'NEW_TENDER': '新招标公告',
    'CONTRACT_REMIND': '合同提醒',
}


def create_notification(notification_type, recipient_type, subject, content,
                        recipient_id=None, recipient_email=None, project_id=None):
    """
    创建通知记录
    """
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO notifications 
            (type, recipient_type, recipient_id, recipient_email, project_id, subject, content, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (
            notification_type,
            recipient_type,
            recipient_id,
            recipient_email,
            project_id,
            subject,
            content,
            get_datetime_str()
        ))
        notify_id = cursor.lastrowid

    return notify_id


def send_notification(notification_id):
    """
    发送通知（模拟）
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM notifications WHERE id = ?", (notification_id,))
        notify = cursor.fetchone()
        if not notify:
            return False

        print(f"\n📧 发送通知 [{NOTIFICATION_TYPES.get(notify['type'], notify['type'])}]")
        print(f"   接收方类型: {notify['recipient_type']}")
        if notify['recipient_email']:
            print(f"   邮箱: {notify['recipient_email']}")
        print(f"   主题: {notify['subject']}")
        print(f"   内容摘要: {notify['content'][:100]}..." if len(notify['content']) > 100 else f"   内容: {notify['content']}")

        cursor.execute("""
            UPDATE notifications SET status = 'sent', sent_at = ? WHERE id = ?
        """, (get_datetime_str(), notification_id))

    log_operation(
        operation_type='NOTIFY',
        module='NOTIFICATION',
        operator='system',
        record_id=notification_id,
        detail=f"发送通知: {notify['subject']}"
    )

    return True


def send_award_notice(project_id, supplier, award_amount, contract_code=None):
    """
    发送中标通知书
    """
    subject = f"【中标通知书】恭喜贵司中标"
    content = f"""
尊敬的{supplier['company_name']}：

    恭喜贵司在本次招标项目中成功中标！

    中标金额：¥{award_amount:,.2f}
    合同编号：{contract_code or '待生成'}

    请贵司尽快与我司联系签订合同事宜。

此致
敬礼！

企业招投标管理系统
{get_datetime_str()}
    """.strip()

    notify_id = create_notification(
        notification_type='AWARD_NOTICE',
        recipient_type='supplier',
        recipient_id=supplier['id'],
        recipient_email=supplier.get('contact_email'),
        project_id=project_id,
        subject=subject,
        content=content
    )
    send_notification(notify_id)
    return notify_id


def send_thank_you(project_id, supplier, project_name):
    """
    发送未中标感谢信
    """
    subject = f"【感谢信】感谢参与{project_name}投标"
    content = f"""
尊敬的{supplier['company_name']}：

    感谢贵司参与{project_name}项目的投标。

    经评审委员会综合评审，本次项目由其他单位中标。虽然本次未能合作，但贵司的专业能力和服务态度给我们留下了深刻印象。我们期待在未来的项目中有机会与贵司合作。

    再次感谢贵司的参与和支持！

此致
敬礼！

企业招投标管理系统
{get_datetime_str()}
    """.strip()

    notify_id = create_notification(
        notification_type='THANK_YOU',
        recipient_type='supplier',
        recipient_id=supplier['id'],
        recipient_email=supplier.get('contact_email'),
        project_id=project_id,
        subject=subject,
        content=content
    )
    send_notification(notify_id)
    return notify_id


def send_performance_warning(contract_code, milestone_name, overdue_days, project_manager=None, supplier=None):
    """
    发送履约预警
    """
    subject = f"【履约预警】{contract_code} - {milestone_name}已超期{overdue_days}天"
    content = f"""
【履约预警通知】

合同编号：{contract_code}
里程碑：{milestone_name}
超期天数：{overdue_days}天

请相关负责人立即关注并处理，确保项目按时交付。

此预警同时已发送给：
- 项目经理：{project_manager or '未指定'}
- 供应商：{supplier or '未指定'}

企业招投标管理系统
{get_datetime_str()}
    """.strip()

    notify_id = create_notification(
        notification_type='PERFORMANCE_WARNING',
        recipient_type='manager',
        project_id=None,
        subject=subject,
        content=content
    )
    send_notification(notify_id)
    return notify_id
