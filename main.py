#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业级招投标全流程自动化管理系统
主入口程序
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.schema import init_database, seed_demo_data


BANNER = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║        企业级招投标全流程自动化管理系统  v1.0                        ║
║                                                                      ║
║   采购申请 → 预算校验 → 招标发布 → 投标解密 → 专家评审 → 定标       ║
║   通知 → 合同生成 → 履约监控 → 统计报告 → 查询导出 → 日志审计       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""


MENU = """
┌─────────────────────────────────────────────────────────────────────┐
│                        主菜单                                        │
├─────────────────────────────────────────────────────────────────────┤
│  1.  采购申请管理（自动提取需求信息）                                 │
│  2.  预算审批校验                                                     │
│  3.  招标项目管理（自动生成+模板匹配+发布）                           │
│  4.  投标管理（自动加密+解密+评分排名）                               │
│  5.  专家管理（自动分配+回避规则）                                    │
│  6.  评审打分（独立打分+去高低分汇总+评审报告）                       │
│  7.  中标管理（定标+通知+感谢信+合同草稿）                            │
│  8.  履约监控（关键节点+超期预警）                                    │
│  9.  统计报告（周报+柱状图+PDF/Excel导出）                            │
│  10. 组合查询+批量导出                                                │
│  11. 操作日志查询                                                     │
│  12. 运行完整全流程演示                                               │
│  0.  退出系统                                                         │
└─────────────────────────────────────────────────────────────────────┘
"""


def init_system():
    print(BANNER)
    print("正在初始化系统...")
    init_database()
    seed_demo_data()
    print("系统初始化完成！")


def handle_procurement():
    from modules.procurement import (create_procurement_request,
                                      auto_extract_from_submission,
                                      list_procurement_requests, get_departments)

    while True:
        print("""
┌───────────────────────┐
│  采购申请管理          │
├───────────────────────┤
│  1. 自动提取创建申请   │
│  2. 手动创建申请       │
│  3. 查看申请列表       │
│  0. 返回               │
└───────────────────────┘""")
        choice = input("请选择: ").strip()

        if choice == '1':
            print("\n请输入/粘贴采购需求的原始文本:")
            raw_text = input("> ").strip()
            depts = get_departments()
            print("\n部门列表:")
            for d in depts:
                print(f"  {d['id']}. {d['name']} (剩余预算: ¥{d['budget_limit'] - d['budget_used']:,.2f})")
            dept_id = int(input("选择部门ID: ").strip())
            submitted_by = input("提交人(默认system): ").strip() or 'system'
            req_id, msg = auto_extract_from_submission(raw_text, dept_id, submitted_by)
            print(f"\n结果: {msg}")
            if req_id:
                print(f"采购申请ID: {req_id}")

        elif choice == '2':
            depts = get_departments()
            print("\n部门列表:")
            for d in depts:
                print(f"  {d['id']}. {d['name']}")
            dept_id = int(input("部门ID: ").strip())
            title = input("标题: ").strip()
            description = input("描述: ").strip()
            print("类别: goods=货物, engineering=工程, service=服务")
            category = input("类别: ").strip() or 'goods'
            amount = float(input("预估金额: ").strip())
            req_date = input("需求日期(YYYY-MM-DD, 可选): ").strip() or None
            contact = input("联系人(可选): ").strip() or None
            phone = input("电话(可选): ").strip() or None
            req_id = create_procurement_request(dept_id, title, description, category,
                                                amount, req_date, contact, phone)
            print(f"\n采购申请创建成功，ID: {req_id}")

        elif choice == '3':
            requests = list_procurement_requests()
            print(f"\n共 {len(requests)} 条采购申请:")
            for r in requests:
                print(f"  [{r['id']}] {r['title']} - {r['department_name']} - ¥{r['estimated_amount']:,.2f} - {r['status']}")

        elif choice == '0':
            break


def handle_budget():
    from modules.budget import approve_budget, reject_budget, get_budget_overview
    from modules.procurement import list_procurement_requests

    while True:
        print("""
┌───────────────────────┐
│  预算管理              │
├───────────────────────┤
│  1. 审批通过申请       │
│  2. 驳回申请           │
│  3. 查看预算总览       │
│  0. 返回               │
└───────────────────────┘""")
        choice = input("请选择: ").strip()

        if choice == '1':
            pending = list_procurement_requests(status='pending')
            print(f"\n待审批申请 ({len(pending)}):")
            for r in pending:
                print(f"  [{r['id']}] {r['title']} - {r['department_name']} - ¥{r['estimated_amount']:,.2f}")
            if pending:
                req_id = int(input("请输入申请ID: ").strip())
                ok, msg = approve_budget(req_id)
                print(f"结果: {msg}")

        elif choice == '2':
            pending = list_procurement_requests(status='pending')
            print(f"\n待审批申请 ({len(pending)}):")
            for r in pending:
                print(f"  [{r['id']}] {r['title']}")
            if pending:
                req_id = int(input("请输入申请ID: ").strip())
                reason = input("驳回原因: ").strip()
                ok, msg = reject_budget(req_id, reason)
                print(f"结果: {msg}")

        elif choice == '3':
            overview = get_budget_overview()
            print("\n部门预算总览:")
            for d in overview:
                print(f"  {d['name']}: 限额¥{d['budget_limit']:,.2f} / 已用¥{d['budget_used']:,.2f} / 剩余¥{d['available_budget']:,.2f} ({d['usage_percent']}%)")

        elif choice == '0':
            break


def handle_tender():
    from modules.tender import (create_tender_from_request, publish_tender,
                                 list_tender_projects, get_templates)
    from modules.procurement import list_procurement_requests

    while True:
        print("""
┌───────────────────────────────┐
│  招标项目管理                  │
├───────────────────────────────┤
│  1. 从采购申请自动生成项目     │
│  2. 发布招标公告               │
│  3. 查看项目列表               │
│  4. 查看招标文件模板           │
│  0. 返回                       │
└───────────────────────────────┘""")
        choice = input("请选择: ").strip()

        if choice == '1':
            approved = list_procurement_requests(status='approved')
            print(f"\n已通过审批可生成招标 ({len(approved)}):")
            for r in approved:
                print(f"  [{r['id']}] {r['title']} - ¥{r['estimated_amount']:,.2f}")
            if approved:
                req_id = int(input("请输入采购申请ID: ").strip())
                proj_id, msg = create_tender_from_request(req_id)
                if proj_id:
                    print(f"生成成功！项目ID: {proj_id}, 编号: {msg}")
                else:
                    print(f"失败: {msg}")

        elif choice == '2':
            projects = list_tender_projects()
            print(f"\n招标项目列表 ({len(projects)}):")
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']} - {p['project_name']} - {p['status']}")
            if projects:
                proj_id = int(input("请输入项目ID: ").strip())
                ok, msg = publish_tender(proj_id)
                print(f"结果: {msg}")

        elif choice == '3':
            projects = list_tender_projects()
            print(f"\n共 {len(projects)} 个招标项目:")
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']} - {p['project_name']} - ¥{p['budget_amount']:,.2f} - 截止:{p['bid_deadline']} - {p['status']}")

        elif choice == '4':
            templates = get_templates()
            print(f"\n招标文件模板 ({len(templates)}):")
            for t in templates:
                print(f"  [{t['id']}] {t['template_name']} - {t['category']} - ¥{t['min_amount']:,.2f}~¥{t['max_amount']:,.2f}")

        elif choice == '0':
            break


def handle_bid():
    from modules.bid import (submit_bid, decrypt_all_bids, calculate_bid_scores,
                              save_bid_rankings, get_project_bids, get_suppliers)
    from modules.tender import list_tender_projects

    while True:
        print("""
┌───────────────────────────────┐
│  投标管理                      │
├───────────────────────────────┤
│  1. 供应商提交投标(自动加密)   │
│  2. 开标解密所有标书           │
│  3. 自动评分排名               │
│  4. 查看项目投标详情           │
│  5. 查看供应商列表             │
│  0. 返回                       │
└───────────────────────────────┘""")
        choice = input("请选择: ").strip()

        if choice == '1':
            projects = list_tender_projects(status='published')
            print(f"\n可投标项目 ({len(projects)}):")
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']} - {p['project_name']} - 截止:{p['bid_deadline']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                suppliers = get_suppliers()
                print(f"\n供应商列表:")
                for s in suppliers:
                    print(f"  [{s['id']}] {s['company_name']} (信用:{s['credit_score']})")
                supp_id = int(input("供应商ID: ").strip())
                amount = float(input("投标金额: ").strip())
                delivery = input("交付日期(YYYY-MM-DD, 可选): ").strip() or None
                content = input("投标内容(可选): ").strip() or None
                bid_id, msg = submit_bid(proj_id, supp_id, amount, delivery, content)
                print(f"结果: {msg}, 投标ID: {bid_id}")

        elif choice == '2':
            projects = list_tender_projects(status='published')
            print(f"\n已发布项目:")
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']} - {p['project_name']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                ok, msg = decrypt_all_bids(proj_id)
                print(f"结果: {msg}")

        elif choice == '3':
            projects = list_tender_projects()
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']} - {p['project_name']} - {p['status']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                results = calculate_bid_scores(proj_id)
                if results:
                    save_bid_rankings(proj_id, results)
                    print(f"\n排名结果（共 {len(results)} 家）:")
                    for r in results:
                        print(f"  第{r['ranking']}名: {r['supplier_name']} - ¥{r['bid_amount']:,.2f} - 综合分:{r['final_score']}")
                else:
                    print("无结果")

        elif choice == '4':
            projects = list_tender_projects()
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                bids = get_project_bids(proj_id)
                print(f"\n投标详情（共 {len(bids)} 条）:")
                for b in bids:
                    rank = f"第{b['ranking']}名" if b['ranking'] else '-'
                    print(f"  {rank}: {b['company_name']} - ¥{b['bid_amount']:,.2f} - {b['status']}")

        elif choice == '5':
            suppliers = get_suppliers()
            for s in suppliers:
                print(f"  [{s['id']}] {s['company_name']} - 信用:{s['credit_score']} - 资质:{s['qualification_level']}")

        elif choice == '0':
            break


def handle_expert():
    from modules.expert import auto_assign_experts, get_project_experts, get_experts
    from modules.tender import list_tender_projects

    while True:
        print("""
┌───────────────────────────────┐
│  专家管理                      │
├───────────────────────────────┤
│  1. 自动分配评审专家(带回避)   │
│  2. 查看项目已分配专家         │
│  3. 查看专家库                 │
│  0. 返回                       │
└───────────────────────────────┘""")
        choice = input("请选择: ").strip()

        if choice == '1':
            projects = list_tender_projects()
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']} - {p['project_name']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                num = int(input("专家人数(默认5): ").strip() or '5')
                experts, msg = auto_assign_experts(proj_id, num_experts=num)
                print(f"结果: {msg}")
                if experts:
                    for e in experts:
                        print(f"  - {e['name']} ({e['expert_code']}) - {e['specialty']}")

        elif choice == '2':
            projects = list_tender_projects()
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                experts = get_project_experts(proj_id)
                print(f"\n已分配专家 ({len(experts)}):")
                for e in experts:
                    print(f"  {e['name']} - {e.get('specialty')}")

        elif choice == '3':
            experts = get_experts()
            print(f"\n专家库共 {len(experts)} 人:")
            for e in experts:
                print(f"  {e['expert_code']} {e['name']} - {e['specialty']} ({e['years_of_experience']}年)")

        elif choice == '0':
            break


def handle_review():
    from modules.review import (expert_submit_score, aggregate_expert_scores,
                                 generate_review_report, get_review_report)
    from modules.tender import list_tender_projects
    from modules.expert import get_project_experts
    from modules.bid import get_project_bids
    import random

    while True:
        print("""
┌───────────────────────────────────┐
│  评审打分管理                      │
├───────────────────────────────────┤
│  1. 模拟专家独立打分               │
│  2. 汇总专家分数（去高低分）       │
│  3. 生成评审报告                   │
│  4. 查看评审报告                   │
│  0. 返回                           │
└───────────────────────────────────┘""")
        choice = input("请选择: ").strip()

        if choice == '1':
            projects = list_tender_projects()
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                experts = get_project_experts(proj_id)
                bids = get_project_bids(proj_id)
                count = 0
                for exp in experts:
                    for bid in bids:
                        tech = round(random.uniform(70, 98), 2)
                        comm = round(random.uniform(65, 95), 2)
                        qual = round(random.uniform(75, 98), 2)
                        expert_submit_score(exp['id'], bid['id'], qual, tech, comm,
                                           comment=f"专家{exp['name']}评审意见", operator=exp['name'])
                        count += 1
                print(f"完成 {count} 次专家打分")

        elif choice == '2':
            projects = list_tender_projects()
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                results, msg = aggregate_expert_scores(proj_id)
                print(f"结果: {msg}")
                if results:
                    for r in results:
                        print(f"  第{r['ranking']}名 {r['supplier_name']}: 综合分={r['final_score']} (技术{r['technical_score']} 商务{r['commercial_score']} 资质{r['qualification_score']})")

        elif choice == '3':
            projects = list_tender_projects()
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                content, msg = generate_review_report(proj_id)
                print(msg)

        elif choice == '4':
            projects = list_tender_projects()
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                report = get_review_report(proj_id)
                if report:
                    print("\n" + report['report_content'])
                else:
                    print("尚未生成评审报告")

        elif choice == '0':
            break


def handle_award():
    from modules.award import determine_winner, notify_all_bidders, generate_contract, archive_losing_bids, get_award
    from modules.tender import list_tender_projects

    while True:
        print("""
┌───────────────────────────────┐
│  中标与合同管理                │
├───────────────────────────────┤
│  1. 自动定标（按综合排名）     │
│  2. 推送中标/未中标通知        │
│  3. 生成合同草稿               │
│  4. 归档未中标数据             │
│  5. 查看中标信息               │
│  0. 返回                       │
└───────────────────────────────┘""")
        choice = input("请选择: ").strip()

        if choice == '1':
            projects = list_tender_projects()
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']} - {p['project_name']} - {p['status']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                award_id, winner = determine_winner(proj_id)
                if award_id:
                    print(f"中标: {winner['company_name']} - ¥{winner['bid_amount']:,.2f}")
                else:
                    print(f"失败: {winner}")

        elif choice == '2':
            projects = list_tender_projects()
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                ok, msg = notify_all_bidders(proj_id)
                print(msg)

        elif choice == '3':
            projects = list_tender_projects()
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                content, msg = generate_contract(proj_id)
                print(msg)
                print("\n" + content[:500] + "\n...")

        elif choice == '4':
            projects = list_tender_projects()
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                cnt = archive_losing_bids(proj_id)
                print(f"已归档 {cnt} 条未中标记录")

        elif choice == '5':
            projects = list_tender_projects()
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']}")
            if projects:
                proj_id = int(input("项目ID: ").strip())
                a = get_award(proj_id)
                if a:
                    print(f"\n中标信息: {a['company_name']} - ¥{a['award_amount']:,.2f} - {a['award_date']}")
                else:
                    print("暂无中标信息")

        elif choice == '0':
            break


def handle_performance():
    from modules.performance import (get_all_contracts, get_contract_milestones,
                                      check_overdue_milestones, update_milestone)

    while True:
        print("""
┌───────────────────────────────┐
│  履约监控                      │
├───────────────────────────────┤
│  1. 查看所有合同               │
│  2. 查看合同履约里程碑         │
│  3. 更新里程碑状态             │
│  4. 检查超期节点并预警         │
│  0. 返回                       │
└───────────────────────────────┘""")
        choice = input("请选择: ").strip()

        if choice == '1':
            contracts = get_all_contracts()
            print(f"\n共 {len(contracts)} 份合同:")
            for c in contracts:
                print(f"  [{c['id']}] {c['contract_code']} - ¥{c['total_amount']:,.2f} - {c['status']}")

        elif choice == '2':
            contracts = get_all_contracts()
            for c in contracts:
                print(f"  [{c['id']}] {c['contract_code']}")
            if contracts:
                cid = int(input("合同ID: ").strip())
                milestones = get_contract_milestones(cid)
                for m in milestones:
                    status_icon = {'pending': '⏳', 'completed': '✅', 'delayed': '⚠️'}.get(m['status'], '❓')
                    print(f"  {status_icon} {m['milestone_name']} - 计划:{m['planned_date']} 实际:{m['actual_date'] or '-'}")

        elif choice == '3':
            contracts = get_all_contracts()
            for c in contracts:
                print(f"  [{c['id']}] {c['contract_code']}")
            if contracts:
                cid = int(input("合同ID: ").strip())
                milestones = get_contract_milestones(cid)
                for m in milestones:
                    print(f"  [{m['id']}] {m['milestone_name']} - {m['status']}")
                mid = int(input("里程碑ID: ").strip())
                print("状态: pending, in_progress, completed, delayed")
                status = input("新状态: ").strip()
                actual = input("实际日期(可选): ").strip() or None
                update_milestone(mid, actual_date=actual, status=status)
                print("更新成功")

        elif choice == '4':
            warnings = check_overdue_milestones()
            print(f"发现 {len(warnings)} 个超期节点:")
            for w in warnings:
                print(f"  - {w['contract_code']} / {w['milestone_name']} / 计划:{w['planned_date']}")

        elif choice == '0':
            break


def handle_statistics():
    from modules.statistics import generate_weekly_statistics, get_all_statistics, export_to_excel, export_to_pdf

    while True:
        print("""
┌───────────────────────────────┐
│  统计报告                      │
├───────────────────────────────┤
│  1. 生成本周统计报告(带柱状图) │
│  2. 查看历史周统计             │
│  3. 导出Excel                  │
│  4. 导出PDF                    │
│  0. 返回                       │
└───────────────────────────────┘""")
        choice = input("请选择: ").strip()

        if choice == '1':
            stats, content, path = generate_weekly_statistics()
            print(f"\n报告已保存: {path}")

        elif choice == '2':
            stats_list = get_all_statistics()
            print(f"\n历史统计 ({len(stats_list)} 周):")
            for s in stats_list:
                print(f"  {s['week_start']}~{s['week_end']}: 项目{s['total_projects']}个 平均{s['avg_duration_days']}天 流标{s['failed_bid_rate']}% 节约¥{s['saved_amount']:,.2f}")

        elif choice == '3':
            stats_list = get_all_statistics()
            data = [dict(s) for s in stats_list]
            path = export_to_excel(data, 'weekly_statistics.xlsx')
            print(f"导出完成: {path}")

        elif choice == '4':
            stats, content, _ = generate_weekly_statistics()
            path = export_to_pdf(content, 'weekly_report.pdf')
            print(f"导出完成: {path}")

        elif choice == '0':
            break


def handle_query():
    from modules.query import search_projects, export_projects, get_bid_details, export_bid_details

    while True:
        print("""
┌───────────────────────────────────────┐
│  组合查询与批量导出                    │
├───────────────────────────────────────┤
│  1. 按条件查询项目                     │
│  2. 导出查询结果为Excel                │
│  3. 批量导出所有投标明细               │
│  4. 批量导出指定项目的投标明细         │
│  0. 返回                               │
└───────────────────────────────────────┘""")
        choice = input("请选择: ").strip()

        if choice in ('1', '2'):
            print("\n请输入查询条件（留空表示不限制）:")
            keyword = input("项目名称/编号关键字: ").strip() or None
            min_amt = input("最低金额: ").strip()
            min_amount = float(min_amt) if min_amt else None
            max_amt = input("最高金额: ").strip()
            max_amount = float(max_amt) if max_amt else None
            status = input("状态(draft/published/decrypted/evaluated/reviewed/awarded/failed): ").strip() or None
            start = input("开始日期(YYYY-MM-DD): ").strip() or None
            end = input("结束日期(YYYY-MM-DD): ").strip() or None
            category = input("类别(goods/engineering/service): ").strip() or None

            if choice == '1':
                results = search_projects(keyword, min_amount, max_amount, status, start, end, category)
                print(f"\n查询到 {len(results)} 条记录:")
                for r in results:
                    print(f"  [{r['id']}] {r['project_code']} {r['project_name']} 预算{r['budget_amount_display']} {r['status']}")
            else:
                path, results = export_projects(keyword, min_amount, max_amount, status, start, end, category)
                print(f"导出 {len(results)} 条记录: {path}")

        elif choice == '3':
            path, details = export_bid_details()
            print(f"导出 {len(details)} 条投标明细: {path}")

        elif choice == '4':
            from modules.tender import list_tender_projects
            projects = list_tender_projects()
            for p in projects:
                print(f"  [{p['id']}] {p['project_code']}")
            ids_input = input("请输入项目ID（多个用逗号分隔）: ").strip()
            ids = [int(x.strip()) for x in ids_input.split(',') if x.strip()]
            path, details = export_bid_details(ids)
            print(f"导出 {len(details)} 条投标明细: {path}")

        elif choice == '0':
            break


def handle_logs():
    from modules.logger import query_logs, OPERATION_TYPES, MODULES

    while True:
        print("""
┌───────────────────────────────┐
│  操作日志查询                  │
├───────────────────────────────┤
│  1. 查询最近日志               │
│  2. 按模块查询                 │
│  3. 按操作类型查询             │
│  0. 返回                       │
└───────────────────────────────┘""")
        choice = input("请选择: ").strip()

        if choice == '1':
            logs = query_logs(limit=30)
            for log in logs:
                print(f"  [{log['created_at']}] {log['module']} / {log['operation_type']} / {log['operator']} - {log['detail'][:50]}")

        elif choice == '2':
            print("模块列表: " + ', '.join(MODULES.values()))
            module = input("输入模块名: ").strip()
            logs = query_logs(module=module, limit=50)
            for log in logs:
                print(f"  [{log['created_at']}] {log['operation_type']} / {log['operator']} - {log['detail'][:60]}")

        elif choice == '3':
            print("操作类型: " + ', '.join(OPERATION_TYPES.values()))
            op = input("输入操作类型: ").strip()
            logs = query_logs(operation_type=op, limit=50)
            for log in logs:
                print(f"  [{log['created_at']}] {log['module']} / {log['operator']} - {log['detail'][:60]}")

        elif choice == '0':
            break


def run_full_demo():
    """运行完整全流程演示"""
    print("\n" + "=" * 70)
    print("  🏭 启动完整招投标全流程自动化演示")
    print("=" * 70)

    import random
    from modules.procurement import auto_extract_from_submission, get_departments, list_procurement_requests
    from modules.budget import approve_budget, get_budget_overview
    from modules.tender import create_tender_from_request, publish_tender, list_tender_projects
    from modules.bid import submit_bid, decrypt_all_bids, calculate_bid_scores, save_bid_rankings, get_suppliers, get_project_bids
    from modules.expert import auto_assign_experts, get_project_experts
    from modules.review import expert_submit_score, aggregate_expert_scores, generate_review_report, get_review_report
    from modules.award import determine_winner, notify_all_bidders, generate_contract, archive_losing_bids, get_award
    from modules.performance import check_overdue_milestones, get_contract_milestones, update_milestone, get_all_contracts
    from modules.statistics import generate_weekly_statistics
    from modules.query import search_projects, export_bid_details

    print("\n【第1步】各部门提交采购申请 (自动提取需求信息)")
    print("-" * 70)
    depts = get_departments()
    demo_requests = [
        (1, "信息技术部申请采购20套服务器设备，预估金额180万元，要求2024年12月31日前交付，联系人张工13800138001"),
        (1, "软件系统开发服务项目，需定制化开发企业管理系统，预算金额85万元"),
        (4, "人力资源部员工培训服务采购，预算35万元，2025年3月启动"),
        (5, "研发中心采购研发工具及云服务，预算580万元"),
        (2, "行政部办公设备采购，预算8.5万元"),
    ]
    created = []
    for dept_id, text in demo_requests:
        req_id, msg = auto_extract_from_submission(text, dept_id, submitted_by='demo_user')
        if req_id:
            created.append(req_id)
            print(f"  ✅ {msg} (ID:{req_id})")

    print(f"\n共创建 {len(created)} 份采购申请")

    print("\n【第2步】预算自动校验审批")
    print("-" * 70)
    approved = []
    for req_id in created:
        ok, msg = approve_budget(req_id, operator='预算经理-王总')
        print(f"  申请ID:{req_id} → {msg}")
        if ok:
            approved.append(req_id)

    print("\n预算总览:")
    for d in get_budget_overview():
        print(f"  {d['name']}: 已用{d['usage_percent']}%，剩余¥{d['available_budget']:,.2f}")

    print("\n【第3步】自动生成招标项目 + 匹配模板 + 发布")
    print("-" * 70)
    project_ids = []
    for req_id in approved:
        proj_id, proj_code = create_tender_from_request(req_id, operator='招标专员')
        if proj_id:
            project_ids.append(proj_id)
            ok, msg = publish_tender(proj_id, operator='招标经理')
            print(f"  📢 {proj_code} → {msg}")

    print("\n【第4步】供应商投标 (内容自动加密存储)")
    print("-" * 70)
    suppliers = get_suppliers()
    for proj_id in project_ids:
        proj = None
        for p in list_tender_projects():
            if p['id'] == proj_id:
                proj = p
                break
        if not proj:
            continue
        num_bidders = random.randint(3, 6)
        selected_suppliers = random.sample(suppliers, min(num_bidders, len(suppliers)))
        budget = proj['budget_amount']
        for s in selected_suppliers:
            bid_amount = round(budget * random.uniform(0.75, 0.98), 2)
            bid_id, msg = submit_bid(proj_id, s['id'], bid_amount, operator=s['company_name'])
            print(f"  📝 {s['company_name']} 投标 {proj['project_code']} → ¥{bid_amount:,.2f}")

    print("\n【第5步】投标截止 → 自动解密所有标书 → 自动评分排名")
    print("-" * 70)
    for proj_id in project_ids:
        ok, msg = decrypt_all_bids(proj_id)
        print(f"  🔓 {msg}")
        results = calculate_bid_scores(proj_id)
        if results:
            save_bid_rankings(proj_id, results)
            print(f"  📊 项目ID:{proj_id} 排名:")
            for r in results[:3]:
                print(f"     第{r['ranking']}名 {r['supplier_name']} 综合分{r['final_score']} 报价¥{r['bid_amount']:,.2f}")

    print("\n【第6步】自动随机分配评审专家 (按专业+回避规则)")
    print("-" * 70)
    for proj_id in project_ids:
        experts, msg = auto_assign_experts(proj_id, num_experts=5)
        if experts:
            names = [e['name'] for e in experts]
            print(f"  🧑‍⚖️ 项目ID:{proj_id} 分配 {len(experts)} 位专家: {', '.join(names)}")

    print("\n【第7步】专家独立打分 → 去掉最高最低分 → 汇总平均分")
    print("-" * 70)
    for proj_id in project_ids:
        experts = get_project_experts(proj_id)
        bids = get_project_bids(proj_id)
        for exp in experts:
            for bid in bids:
                tech = round(random.uniform(72, 97), 2)
                comm = round(random.uniform(68, 96), 2)
                qual = round(random.uniform(74, 99), 2)
                expert_submit_score(exp['id'], bid['id'], qual, tech, comm, operator=exp['name'])

        results, msg = aggregate_expert_scores(proj_id)
        print(f"  📈 项目ID:{proj_id} 专家评分汇总完成:")
        for r in results[:3]:
            print(f"     第{r['ranking']}名 {r['supplier_name']} 综合分{r['final_score']} (专家数:{r['expert_count']})")

    print("\n【第8步】生成评审报告")
    print("-" * 70)
    for proj_id in project_ids:
        content, msg = generate_review_report(proj_id)
        print(f"  📄 项目ID:{proj_id} → {msg}")

    print("\n【第9步】定标 → 推送中标通知书/感谢信 → 归档 → 生成合同草稿")
    print("-" * 70)
    for proj_id in project_ids:
        award_id, winner = determine_winner(proj_id)
        if award_id:
            print(f"  🏆 项目ID:{proj_id} 中标: {winner['company_name']} ¥{winner['bid_amount']:,.2f}")

        ok, msg = notify_all_bidders(proj_id)
        print(f"  📧 {msg}")

        content, msg = generate_contract(proj_id)
        if content:
            c = get_award(proj_id)
            print(f"  📋 项目ID:{proj_id} → {msg}")

        cnt = archive_losing_bids(proj_id)
        print(f"  📦 项目ID:{proj_id} 归档未中标记录 {cnt} 条")

    print("\n【第10步】履约监控 - 关键节点（交付/验收/付款）+ 超期2天自动预警")
    print("-" * 70)
    contracts = get_all_contracts()
    for c in contracts:
        milestones = get_contract_milestones(c['id'])
        print(f"  合同 {c['contract_code']} 里程碑:")
        for m in milestones:
            icon = {'pending': '⏳', 'completed': '✅', 'in_progress': '🔄', 'delayed': '⚠️'}.get(m['status'], '❓')
            print(f"    {icon} {m['milestone_name']} - 计划: {m['planned_date']}")

    warnings = check_overdue_milestones()
    print(f"\n  🔔 超期预警检查完成，发现 {len(warnings)} 个预警节点")

    print("\n【第11步】生成周统计报告（柱状图可视化 + PDF/Excel导出）")
    print("-" * 70)
    stats, content, path = generate_weekly_statistics()
    print(f"  📊 报告已生成并保存: {path}")

    print("\n【第12步】组合查询 + 批量导出投标明细")
    print("-" * 70)
    results = search_projects(status='awarded')
    print(f"  🔍 查询中标项目: {len(results)} 个")
    for r in results[:3]:
        print(f"     {r['project_code']} {r['project_name']} 预算{r['budget_amount_display']} 节约{r['saved_amount_display']}")

    path, details = export_bid_details()
    print(f"  📥 批量导出投标明细 {len(details)} 条 → {path}")

    print("\n" + "=" * 70)
    print("  ✅ 全流程自动化演示完成！所有操作已记录日志并推送项目群")
    print("=" * 70 + "\n")


def main():
    init_system()

    while True:
        print(MENU)
        choice = input("请输入选项 (0-12): ").strip()

        if choice == '1':
            handle_procurement()
        elif choice == '2':
            handle_budget()
        elif choice == '3':
            handle_tender()
        elif choice == '4':
            handle_bid()
        elif choice == '5':
            handle_expert()
        elif choice == '6':
            handle_review()
        elif choice == '7':
            handle_award()
        elif choice == '8':
            handle_performance()
        elif choice == '9':
            handle_statistics()
        elif choice == '10':
            handle_query()
        elif choice == '11':
            handle_logs()
        elif choice == '12':
            run_full_demo()
        elif choice == '0':
            print("\n感谢使用企业级招投标全流程自动化管理系统，再见！\n")
            break
        else:
            print("无效选项，请重新输入")


if __name__ == '__main__':
    main()
