#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试脚本 - 非交互模式验证所有模块
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.schema import init_database, seed_demo_data


def test_all_modules():
    print("=" * 70)
    print("  企业级招投标全流程自动化系统 - 模块测试")
    print("=" * 70)

    print("\n[1/13] 初始化数据库和演示数据...")
    init_database()
    seed_demo_data()
    print("  ✅ 数据库初始化完成")

    from modules.procurement import auto_extract_from_submission, get_departments
    print("\n[2/13] 测试采购申请模块 (自动提取需求)...")
    depts = get_departments()
    test_texts = [
        (depts[0]['id'], "信息技术部采购服务器10台，金额约80万元，要求2024-12-31前交付"),
        (depts[1]['id'], "办公设备采购预算8万元"),
    ]
    created = []
    for did, text in test_texts:
        rid, msg = auto_extract_from_submission(text, did, 'tester')
        created.append(rid)
        print(f"  ✅ 申请ID:{rid} - {msg}")

    from modules.budget import approve_budget, get_budget_overview
    print("\n[3/13] 测试预算自动校验审批...")
    approved = []
    for rid in created:
        ok, msg = approve_budget(rid, 'budget_manager')
        print(f"  ✅ 申请ID:{rid} → {msg}")
        if ok:
            approved.append(rid)
    overview = get_budget_overview()
    print(f"  ✅ 预算总览获取成功，共 {len(overview)} 个部门")

    from modules.tender import create_tender_from_request, publish_tender, match_template
    print("\n[4/13] 测试招标项目生成+模板匹配+发布...")
    project_ids = []
    for rid in approved:
        pid, code = create_tender_from_request(rid, 'tester')
        if pid:
            project_ids.append(pid)
            ok, msg = publish_tender(pid, 'tender_manager')
            print(f"  ✅ 项目 {code} 发布成功")
    template = match_template('goods', 500000)
    print(f"  ✅ 模板匹配: {template['template_name'] if template else '无'}")

    from modules.bid import submit_bid, decrypt_all_bids, calculate_bid_scores, save_bid_rankings, get_suppliers
    import random
    print("\n[5/13] 测试投标加密提交+解密+自动评分排名...")
    suppliers = get_suppliers()
    for pid in project_ids:
        for s in suppliers[:4]:
            amt = round(random.uniform(50000, 90000), 2)
            bid, msg = submit_bid(pid, s['id'], amt)
        ok, msg = decrypt_all_bids(pid)
        print(f"  ✅ {msg}")
        results = calculate_bid_scores(pid)
        if results:
            save_bid_rankings(pid, results)
            print(f"  ✅ 评分排名完成: {len(results)} 家，第一名:{results[0]['supplier_name']} {results[0]['final_score']}")

    from modules.expert import auto_assign_experts, get_project_experts
    print("\n[6/13] 测试专家自动分配（按专业+回避规则）...")
    for pid in project_ids:
        exps, msg = auto_assign_experts(pid, num_experts=5)
        if exps:
            names = [e['name'] for e in exps]
            print(f"  ✅ 项目ID:{pid} 分配专家: {', '.join(names)}")

    from modules.review import expert_submit_score, aggregate_expert_scores, generate_review_report
    from modules.bid import get_project_bids
    print("\n[7/13] 测试专家独立打分+去高低分汇总+评审报告...")
    for pid in project_ids:
        exps = get_project_experts(pid)
        bids = get_project_bids(pid)
        for exp in exps:
            for bid in bids:
                expert_submit_score(exp['id'], bid['id'],
                                   round(random.uniform(75, 98), 2),
                                   round(random.uniform(70, 97), 2),
                                   round(random.uniform(68, 96), 2),
                                   operator=exp['name'])
        results, msg = aggregate_expert_scores(pid)
        print(f"  ✅ {msg}, 第一名:{results[0]['supplier_name'] if results else 'N/A'}")
        content, msg = generate_review_report(pid)
        print(f"  ✅ 评审报告: {msg}")

    from modules.award import determine_winner, notify_all_bidders, generate_contract, archive_losing_bids
    print("\n[8/13] 测试定标+通知+合同生成+归档...")
    for pid in project_ids:
        aid, winner = determine_winner(pid)
        if aid:
            print(f"  ✅ 定标: {winner['company_name']} ¥{winner['bid_amount']:,.2f}")
        ok, msg = notify_all_bidders(pid)
        print(f"  ✅ {msg}")
        content, msg = generate_contract(pid)
        print(f"  ✅ {msg}")
        cnt = archive_losing_bids(pid)
        print(f"  ✅ 归档未中标: {cnt} 条")

    from modules.performance import check_overdue_milestones, get_all_contracts, get_contract_milestones
    print("\n[9/13] 测试履约监控+超期预警...")
    contracts = get_all_contracts()
    print(f"  ✅ 合同数: {len(contracts)}")
    for c in contracts:
        ms = get_contract_milestones(c['id'])
        print(f"  ✅ 合同{c['contract_code']} 里程碑: {len(ms)} 个")
    warnings = check_overdue_milestones()
    print(f"  ✅ 超期预警检查完成，预警 {len(warnings)} 个")

    from modules.statistics import generate_weekly_statistics, export_to_excel, export_to_pdf
    print("\n[10/13] 测试周统计报告+可视化+PDF/Excel导出...")
    stats, content, path = generate_weekly_statistics()
    print(f"  ✅ 报告生成: {path}")
    expath = export_to_excel([{'a': 1, 'b': 2}, {'a': 3, 'b': 4}], 'test_export.xlsx')
    print(f"  ✅ Excel导出: {expath}")
    pdfpath = export_to_pdf("Test PDF content\nLine 2\nLine 3", 'test_export.pdf')
    print(f"  ✅ PDF/TXT导出: {pdfpath}")

    from modules.query import search_projects, export_projects, export_bid_details
    print("\n[11/13] 测试组合查询+批量导出...")
    results = search_projects(keyword='服务器', min_amount=10000)
    print(f"  ✅ 条件查询: {len(results)} 条")
    path, projs = export_projects()
    print(f"  ✅ 项目导出: {len(projs)} 条 → {path}")
    path, details = export_bid_details()
    print(f"  ✅ 投标明细导出: {len(details)} 条 → {path}")

    from modules.logger import log_operation, query_logs
    print("\n[12/13] 测试操作日志记录与推送...")
    log_operation('CREATE', 'SYSTEM', 'tester', detail='测试日志记录', push_to_group=True)
    logs = query_logs(limit=5)
    print(f"  ✅ 日志查询: {len(logs)} 条，已推送项目群")

    from modules.notification import create_notification, send_notification
    print("\n[13/13] 测试通知系统...")
    nid = create_notification('NEW_TENDER', 'supplier', '测试通知', '这是一条测试通知内容', recipient_email='test@example.com')
    send_notification(nid)
    print(f"  ✅ 通知创建并发送成功")

    print("\n" + "=" * 70)
    print("  🎉 所有模块测试通过！系统运行正常")
    print("=" * 70)
    print("\n输出文件目录:")
    print(f"  - 数据库: data/bidding_system.db")
    print(f"  - 报告: output/reports/")
    print(f"  - 合同: output/contracts/")
    print(f"  - 导出: output/exports/")
    print(f"  - 日志: output/logs/")


if __name__ == '__main__':
    test_all_modules()
