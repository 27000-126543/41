"""
PDF导出模块 - 使用reportlab正确实现中文字体PDF
"""
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from datetime import datetime
from config.settings import REPORTS_DIR

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfgen import canvas
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def _register_cn_font():
    """尝试注册中文字体"""
    cn_fonts = [
        ('/System/Library/Fonts/PingFang.ttc', 'PingFang'),
        ('/System/Library/Fonts/STHeiti Medium.ttc', 'STHeiti'),
        ('/System/Library/Fonts/Supplemental/Songti.ttc', 'Songti'),
        ('C:/Windows/Fonts/simhei.ttf', 'SimHei'),
        ('C:/Windows/Fonts/simsun.ttc', 'SimSun'),
        ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 'WenQuanYi'),
        ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 'NotoSans'),
    ]
    try:
        from reportlab.pdfbase.ttfonts import TTFont
        for path, name in cn_fonts:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(name, path))
                    return name
                except Exception:
                    continue
    except Exception:
        pass
    return 'Helvetica'


CN_FONT = _register_cn_font() if HAS_REPORTLAB else 'Helvetica'


def _cn(text):
    """确保中文可显示"""
    if not isinstance(text, str):
        text = str(text)
    return text


def generate_review_report_pdf(project):
    """生成评审报告PDF"""
    if not HAS_REPORTLAB:
        txt_path = os.path.join(REPORTS_DIR, f"review_{project['project_code']}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"评审报告 - {project['project_name']}")
        return txt_path

    filename = f"review_report_{project['project_code']}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            rightMargin=2 * cm, leftMargin=2 * cm,
                            topMargin=2.5 * cm, bottomMargin=2 * cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CNTitle', parent=styles['Title'],
        fontName=CN_FONT, fontSize=20, leading=28,
        alignment=1, spaceAfter=20, textColor=colors.HexColor('#1e40af'),
    )
    h2_style = ParagraphStyle(
        'CNH2', parent=styles['Heading2'],
        fontName=CN_FONT, fontSize=14, leading=20,
        textColor=colors.HexColor('#1e3a8a'), spaceBefore=15, spaceAfter=10,
    )
    body_style = ParagraphStyle(
        'CNBody', parent=styles['BodyText'],
        fontName=CN_FONT, fontSize=11, leading=18,
    )
    normal_style = ParagraphStyle(
        'CNNormal', parent=styles['Normal'],
        fontName=CN_FONT, fontSize=10, leading=16,
    )

    story = []

    story.append(Paragraph(_cn('招 标 项 目 评 审 报 告'), title_style))
    story.append(Spacer(1, 0.3 * cm))

    info_data = [
        [Paragraph(_cn('项目编号'), normal_style), Paragraph(_cn(project['project_code']), normal_style),
         Paragraph(_cn('项目名称'), normal_style), Paragraph(_cn(project['project_name']), normal_style)],
        [Paragraph(_cn('项目类别'), normal_style), Paragraph(_cn(str(project.get('category', ''))), normal_style),
         Paragraph(_cn('预算金额'), normal_style), Paragraph(_cn(f"¥{project['budget_amount']:,.2f}"), normal_style)],
        [Paragraph(_cn('发布日期'), normal_style), Paragraph(_cn(str(project.get('publish_date', ''))), normal_style),
         Paragraph(_cn('开标日期'), normal_style), Paragraph(_cn(str(project.get('open_bid_date', ''))), normal_style)],
    ]
    info_table = Table(info_data, colWidths=[2.5 * cm, 5 * cm, 2.5 * cm, 5 * cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CN_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eff6ff')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#eff6ff')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)

    story.append(Paragraph(_cn('一、评审委员会组成'), h2_style))

    from core.database import get_cursor
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT e.name, e.title, e.specialty, e.organization
            FROM expert_assignments ea LEFT JOIN experts e ON ea.expert_id = e.id
            WHERE ea.project_id = ?
        """, (project['id'],))
        experts = [dict(r) for r in cursor.fetchall()]

    exp_header = [Paragraph(_cn('序号'), normal_style), Paragraph(_cn('姓名'), normal_style),
                  Paragraph(_cn('职称'), normal_style), Paragraph(_cn('专业'), normal_style),
                  Paragraph(_cn('单位'), normal_style)]
    exp_rows = [exp_header]
    for i, e in enumerate(experts, 1):
        exp_rows.append([
            Paragraph(str(i), normal_style),
            Paragraph(_cn(e.get('name', '')), normal_style),
            Paragraph(_cn(e.get('title', '')), normal_style),
            Paragraph(_cn(e.get('specialty', '')), normal_style),
            Paragraph(_cn(e.get('organization', '')), normal_style),
        ])
    exp_table = Table(exp_rows, colWidths=[1.2 * cm, 2.5 * cm, 3 * cm, 3.5 * cm, 4.8 * cm])
    exp_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CN_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(exp_table)

    story.append(Paragraph(
        _cn(f"二、评分权重（技术{project['weight_technical'] * 100:.0f}% / 商务{project['weight_commercial'] * 100:.0f}% / 资质{project['weight_qualification'] * 100:.0f}%）"),
        h2_style
    ))

    story.append(Paragraph(_cn('三、投标供应商评分汇总表'), h2_style))

    from core.database import get_cursor
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT b.*, s.company_name FROM bids b
            LEFT JOIN suppliers s ON b.supplier_id = s.id
            WHERE b.project_id = ? ORDER BY COALESCE(b.ranking, 9999)
        """, (project['id'],))
        bids = [dict(r) for r in cursor.fetchall()]

    bid_header = [Paragraph(_cn('排名'), normal_style), Paragraph(_cn('供应商'), normal_style),
                  Paragraph(_cn('报价(元)'), normal_style), Paragraph(_cn('技术分'), normal_style),
                  Paragraph(_cn('商务分'), normal_style), Paragraph(_cn('资质分'), normal_style),
                  Paragraph(_cn('综合分'), normal_style)]
    bid_rows = [bid_header]
    for b in bids:
        bid_rows.append([
            Paragraph(str(b.get('ranking', '-')), normal_style),
            Paragraph(_cn(b.get('company_name', '')), normal_style),
            Paragraph(f"{b['bid_amount']:,.2f}", normal_style),
            Paragraph(f"{b.get('technical_score', 0):.2f}", normal_style),
            Paragraph(f"{b.get('commercial_score', 0):.2f}", normal_style),
            Paragraph(f"{b.get('qualification_score', 0):.2f}", normal_style),
            Paragraph(f"{b.get('final_score', 0):.2f}", normal_style),
        ])
    bid_table = Table(bid_rows, colWidths=[1.2 * cm, 3.8 * cm, 2.5 * cm, 2 * cm, 2 * cm, 2 * cm, 2 * cm])
    bid_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CN_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(bid_table)

    story.append(Paragraph(_cn('四、评审结论'), h2_style))
    winner = next((b for b in bids if b.get('ranking') == 1), None)
    if winner:
        story.append(Paragraph(
            _cn(f"推荐中标供应商：<b>{winner['company_name']}</b><br/>"
                f"中标金额：¥{winner['bid_amount']:,.2f}<br/>"
                f"综合得分：{winner.get('final_score', 0):.2f}"),
            body_style
        ))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        _cn(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"),
        ParagraphStyle('Footer', parent=normal_style, textColor=colors.grey, alignment=1)
    ))

    doc.build(story)
    return filepath


def generate_weekly_report_pdf(stats, text_content=None):
    """生成周统计报告PDF"""
    if not HAS_REPORTLAB:
        txt_path = os.path.join(REPORTS_DIR, f"weekly_{stats['week_start']}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text_content or '周报')
        return txt_path

    filename = f"weekly_report_{stats['week_start']}_{stats['week_end']}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            rightMargin=2 * cm, leftMargin=2 * cm,
                            topMargin=2.5 * cm, bottomMargin=2 * cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CNTitle', parent=styles['Title'],
        fontName=CN_FONT, fontSize=20, leading=28,
        alignment=1, spaceAfter=20, textColor=colors.HexColor('#065f46'),
    )
    h2_style = ParagraphStyle(
        'CNH2', parent=styles['Heading2'],
        fontName=CN_FONT, fontSize=14, leading=20,
        textColor=colors.HexColor('#047857'), spaceBefore=12, spaceAfter=8,
    )
    body_style = ParagraphStyle(
        'CNBody', parent=styles['BodyText'],
        fontName=CN_FONT, fontSize=11, leading=20, leftIndent=10,
    )
    normal_style = ParagraphStyle(
        'CNNormal', parent=styles['Normal'],
        fontName=CN_FONT, fontSize=10, leading=16,
    )

    story = []
    story.append(Paragraph(_cn('招 投 标 工 作 周 报'), title_style))
    story.append(Paragraph(
        _cn(f"统计周期：{stats['week_start']} 至 {stats['week_end']}<br/>生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"),
        ParagraphStyle('SubTitle', parent=normal_style, alignment=1, textColor=colors.grey, spaceAfter=20)
    ))

    story.append(Paragraph(_cn('一、核心指标概览'), h2_style))
    metric_data = [
        [Paragraph(_cn('项目总数'), normal_style), Paragraph(_cn(f"{stats['total_projects']} 个"), normal_style),
         Paragraph(_cn('平均用时'), normal_style), Paragraph(_cn(f"{stats['avg_duration_days']} 天"), normal_style)],
        [Paragraph(_cn('流标率'), normal_style), Paragraph(_cn(f"{stats['failed_bid_rate']}%"), normal_style),
         Paragraph(_cn('节约资金'), normal_style), Paragraph(_cn(f"¥{stats['saved_amount']:,.2f}"), normal_style)],
        [Paragraph(_cn('中标项目'), normal_style), Paragraph(_cn(f"{stats.get('awarded_count', 0)} 个"), normal_style),
         Paragraph(_cn('流标项目'), normal_style), Paragraph(_cn(f"{stats.get('failed_count', 0)} 个"), normal_style)],
    ]
    metric_table = Table(metric_data, colWidths=[3 * cm, 4.5 * cm, 3 * cm, 4.5 * cm])
    metric_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CN_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecfdf5')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#ecfdf5')),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f0fdf4')),
        ('BACKGROUND', (3, 0), (3, -1), colors.HexColor('#f0fdf4')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(metric_table)

    story.append(Paragraph(_cn('二、指标说明'), h2_style))
    story.append(Paragraph(_cn(
        "1. 项目总数：本周新创建的招标项目数量<br/>"
        "2. 平均用时：项目从发布到定标的平均天数<br/>"
        "3. 流标率：流标项目 / 已完成项目 × 100%<br/>"
        "4. 节约资金：所有中标项目的预算金额 - 中标金额 之和"),
        body_style
    ))

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        _cn("本报告由招投标自动化管理系统自动生成"),
        ParagraphStyle('Footer', parent=normal_style, textColor=colors.grey, alignment=1)
    ))

    doc.build(story)
    return filepath
