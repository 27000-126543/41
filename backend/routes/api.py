"""
通用业务API路由 - 复用现有modules/业务逻辑
"""
import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from backend.auth import success, error, get_current_user, role_required, permission_required

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.get('/health')
def health():
    return success({'status': 'ok', 'service': 'bidding-system-web'})


@api_bp.get('/departments')
@jwt_required()
def list_departments():
    from modules.procurement import get_departments
    return success(get_departments())


@api_bp.get('/budget/overview')
@jwt_required()
@permission_required('budget:view')
def budget_overview():
    from modules.budget import get_budget_overview
    return success(get_budget_overview())


# ---------------- 采购申请 ----------------
@api_bp.get('/procurements')
@jwt_required()
@permission_required('procurement:view')
def list_procurements():
    from modules.procurement import list_procurement_requests
    status = request.args.get('status')
    return success(list_procurement_requests(status=status))


@api_bp.get('/procurements/<int:rid>')
@jwt_required()
@permission_required('procurement:view')
def get_procurement(rid):
    from modules.procurement import get_procurement_request
    req = get_procurement_request(rid)
    if not req:
        return error('申请不存在', 404)
    return success(req)


@api_bp.post('/procurements')
@jwt_required()
@permission_required('procurement:create')
def create_procurement():
    user = get_current_user()
    data = request.get_json() or {}
    auto_extract = data.get('auto_extract', False)

    if auto_extract and data.get('raw_text'):
        from modules.procurement import auto_extract_from_submission
        dept_id = data.get('department_id') or user.department_id or 1
        rid, msg = auto_extract_from_submission(data['raw_text'], dept_id, user.username)
        if rid:
            return success({'id': rid, 'msg': msg})
        return error(msg)

    from modules.procurement import create_procurement_request
    rid = create_procurement_request(
        department_id=data.get('department_id') or user.department_id or 1,
        title=data['title'],
        description=data.get('description', ''),
        category=data.get('category', 'goods'),
        estimated_amount=float(data['estimated_amount']),
        required_date=data.get('required_date'),
        contact_person=data.get('contact_person'),
        contact_phone=data.get('contact_phone'),
        submitted_by=user.username,
    )
    return success({'id': rid}, '采购申请已创建')


@api_bp.post('/procurements/<int:rid>/approve')
@jwt_required()
@permission_required('budget:approve')
def approve_procurement(rid):
    from modules.budget import approve_budget
    user = get_current_user()
    ok, msg = approve_budget(rid, operator=user.username)
    if ok:
        return success(msg=msg)
    return error(msg)


@api_bp.post('/procurements/<int:rid>/reject')
@jwt_required()
@permission_required('budget:approve')
def reject_procurement(rid):
    from modules.budget import reject_budget
    user = get_current_user()
    data = request.get_json() or {}
    ok, msg = reject_budget(rid, data.get('reason', '不符合要求'), operator=user.username)
    if ok:
        return success(msg=msg)
    return error(msg)


# ---------------- 招标项目 ----------------
@api_bp.get('/tenders')
@jwt_required()
@permission_required('tender:view')
def list_tenders():
    from modules.tender import list_tender_projects
    status = request.args.get('status')
    category = request.args.get('category')
    return success(list_tender_projects(status=status, category=category))


@api_bp.get('/tenders/<int:tid>')
@jwt_required()
@permission_required('tender:view')
def get_tender(tid):
    from modules.tender import get_tender_project
    t = get_tender_project(tid)
    if not t:
        return error('项目不存在', 404)
    return success(t)


@api_bp.post('/tenders/from-request/<int:rid>')
@jwt_required()
@permission_required('tender:create')
def create_tender_from_request(rid):
    from modules.tender import create_tender_from_request
    user = get_current_user()
    pid, msg = create_tender_from_request(rid, operator=user.username)
    if pid:
        return success({'id': pid, 'project_code': msg})
    return error(msg)


@api_bp.post('/tenders/<int:tid>/publish')
@jwt_required()
@permission_required('tender:publish')
def publish_tender(tid):
    from modules.tender import publish_tender
    user = get_current_user()
    ok, msg = publish_tender(tid, operator=user.username)
    if ok:
        return success(msg=msg)
    return error(msg)


@api_bp.get('/templates')
@jwt_required()
def list_templates():
    from modules.tender import get_templates
    return success(get_templates())


# ---------------- 投标 ----------------
@api_bp.get('/tenders/<int:tid>/bids')
@jwt_required()
@permission_required('bid:view')
def list_bids(tid):
    from modules.bid import get_project_bids
    return success(get_project_bids(tid))


@api_bp.get('/suppliers')
@jwt_required()
def list_suppliers():
    from modules.bid import get_suppliers
    return success(get_suppliers())


@api_bp.post('/tenders/<int:tid>/bids')
@jwt_required()
def create_bid(tid):
    user = get_current_user()
    if user.role == 'supplier' and not user.supplier_id:
        return error('供应商账号未关联供应商档案')

    from modules.bid import submit_bid
    data = request.get_json() or {}
    supplier_id = data.get('supplier_id') or user.supplier_id
    if not supplier_id:
        return error('请指定供应商')

    bid_id, msg = submit_bid(
        project_id=tid,
        supplier_id=int(supplier_id),
        bid_amount=float(data['bid_amount']),
        delivery_date=data.get('delivery_date'),
        bid_content=data.get('bid_content'),
        operator=user.username,
    )
    if bid_id:
        return success({'id': bid_id}, msg)
    return error(msg)


@api_bp.post('/tenders/<int:tid>/decrypt')
@jwt_required()
@permission_required('bid:view')
def decrypt_bids(tid):
    from modules.bid import decrypt_all_bids
    user = get_current_user()
    ok, msg = decrypt_all_bids(tid, operator=user.username)
    if ok:
        return success(msg=msg)
    return error(msg)


@api_bp.post('/tenders/<int:tid>/auto-score')
@jwt_required()
def auto_score(tid):
    from modules.bid import calculate_bid_scores, save_bid_rankings
    user = get_current_user()
    results = calculate_bid_scores(tid)
    if not results:
        return error('无可评分的投标')
    save_bid_rankings(tid, results, operator=user.username)
    return success(results)


# ---------------- 专家 ----------------
@api_bp.get('/experts')
@jwt_required()
def list_experts():
    from modules.expert import get_experts
    specialty = request.args.get('specialty')
    return success(get_experts(specialty=specialty))


@api_bp.get('/tenders/<int:tid>/experts')
@jwt_required()
def get_tender_experts(tid):
    from modules.expert import get_project_experts
    return success(get_project_experts(tid))


@api_bp.post('/tenders/<int:tid>/assign-experts')
@jwt_required()
@permission_required('expert:assign')
def assign_experts(tid):
    from modules.expert import auto_assign_experts
    data = request.get_json() or {}
    num = int(data.get('num_experts', 5))
    user = get_current_user()
    exps, msg = auto_assign_experts(tid, num_experts=num, operator=user.username)
    if exps:
        return success(exps, msg)
    return error(msg)


# ---------------- 评审打分 ----------------
@api_bp.post('/tenders/<int:tid>/expert-score')
@jwt_required()
@permission_required('review:score')
def expert_score(tid):
    user = get_current_user()
    if user.role == 'expert' and not user.expert_id:
        return error('专家账号未关联专家档案')

    from modules.review import expert_submit_score
    from modules.expert import get_project_experts

    data = request.get_json() or {}
    assignment_id = data.get('assignment_id')
    if not assignment_id and user.role == 'expert':
        experts = get_project_experts(tid)
        for e in experts:
            if e['expert_id'] == user.expert_id:
                assignment_id = e['id']
                break

    if not assignment_id:
        return error('未找到专家分配记录')

    ok, msg = expert_submit_score(
        assignment_id=assignment_id,
        bid_id=int(data['bid_id']),
        qualification_score=float(data['qualification_score']),
        technical_score=float(data['technical_score']),
        commercial_score=float(data['commercial_score']),
        comment=data.get('comment'),
        operator=user.username,
    )
    if ok:
        return success(msg=msg)
    return error(msg)


@api_bp.post('/tenders/<int:tid>/aggregate-scores')
@jwt_required()
def aggregate_scores(tid):
    from modules.review import aggregate_expert_scores
    user = get_current_user()
    results, msg = aggregate_expert_scores(tid, operator=user.username)
    if results:
        return success(results, msg)
    return error(msg)


@api_bp.get('/tenders/<int:tid>/review-report')
@jwt_required()
@permission_required('review:view')
def get_review_report(tid):
    from modules.review import get_review_report, generate_review_report
    user = get_current_user()
    report = get_review_report(tid)
    if not report:
        _, msg = generate_review_report(tid, operator=user.username)
        report = get_review_report(tid)
    return success(report)


@api_bp.post('/tenders/<int:tid>/review-report')
@jwt_required()
def generate_report(tid):
    from modules.review import generate_review_report
    user = get_current_user()
    content, msg = generate_review_report(tid, operator=user.username)
    return success({'content': content}, msg)


# ---------------- 中标 ----------------
@api_bp.post('/tenders/<int:tid>/determine-winner')
@jwt_required()
@permission_required('award:decide')
def determine_winner(tid):
    from modules.award import determine_winner
    user = get_current_user()
    aid, winner = determine_winner(tid, operator=user.username)
    if aid:
        return success({'award_id': aid, 'winner': dict(winner) if winner else None})
    return error(winner if isinstance(winner, str) else '定标失败')


@api_bp.get('/tenders/<int:tid>/award')
@jwt_required()
@permission_required('award:view')
def get_award(tid):
    from modules.award import get_award
    return success(get_award(tid))


@api_bp.post('/tenders/<int:tid>/notify-bidders')
@jwt_required()
def notify_bidders(tid):
    from modules.award import notify_all_bidders
    ok, msg = notify_all_bidders(tid)
    if ok:
        return success(msg=msg)
    return error(msg)


@api_bp.post('/tenders/<int:tid>/generate-contract')
@jwt_required()
@permission_required('contract:create')
def generate_contract(tid):
    from modules.award import generate_contract
    user = get_current_user()
    content, msg = generate_contract(tid, operator=user.username)
    if content:
        return success({'content': content}, msg)
    return error(msg)


@api_bp.post('/tenders/<int:tid>/archive')
@jwt_required()
def archive_bids(tid):
    from modules.award import archive_losing_bids
    cnt = archive_losing_bids(tid)
    return success({'archived_count': cnt}, f'归档{cnt}条记录')


# ---------------- 履约 ----------------
@api_bp.get('/contracts')
@jwt_required()
@permission_required('performance:view')
def list_contracts():
    from modules.performance import get_all_contracts
    return success(get_all_contracts())


@api_bp.get('/contracts/<int:cid>')
@jwt_required()
def get_contract(cid):
    from modules.performance import get_contract
    c = get_contract(cid)
    if not c:
        return error('合同不存在', 404)
    return success(c)


@api_bp.get('/contracts/<int:cid>/milestones')
@jwt_required()
def get_milestones(cid):
    from modules.performance import get_contract_milestones
    return success(get_contract_milestones(cid))


@api_bp.post('/milestones/<int:mid>')
@jwt_required()
def update_milestone(mid):
    from modules.performance import update_milestone
    user = get_current_user()
    data = request.get_json() or {}
    update_milestone(
        milestone_id=mid,
        actual_date=data.get('actual_date'),
        status=data.get('status'),
        comment=data.get('comment'),
        operator=user.username,
    )
    return success(msg='更新成功')


@api_bp.post('/performance/check-overdue')
@jwt_required()
def check_overdue():
    from modules.performance import check_overdue_milestones
    warnings = check_overdue_milestones()
    return success({'count': len(warnings), 'items': warnings})


# ---------------- 统计报表 ----------------
@api_bp.get('/statistics/weekly')
@jwt_required()
@permission_required('statistics:view')
def weekly_statistics():
    from modules.statistics import generate_weekly_statistics, get_all_statistics
    if request.args.get('generate') == '1':
        stats, content, path = generate_weekly_statistics()
        return success({'stats': stats, 'report_content': content, 'report_path': path})
    return success(get_all_statistics())


# ---------------- 查询导出 ----------------
@api_bp.get('/search/projects')
@jwt_required()
@permission_required('query:all')
def search_projects():
    from modules.query import search_projects
    results = search_projects(
        keyword=request.args.get('keyword'),
        min_amount=float(request.args.get('min_amount')) if request.args.get('min_amount') else None,
        max_amount=float(request.args.get('max_amount')) if request.args.get('max_amount') else None,
        status=request.args.get('status'),
        start_date=request.args.get('start_date'),
        end_date=request.args.get('end_date'),
        category=request.args.get('category'),
    )
    return success(results)


@api_bp.post('/export/projects')
@jwt_required()
def export_projects():
    from modules.query import export_projects
    data = request.get_json() or {}
    path, results = export_projects(
        keyword=data.get('keyword'),
        min_amount=data.get('min_amount'),
        max_amount=data.get('max_amount'),
        status=data.get('status'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        category=data.get('category'),
    )
    return success({'path': path, 'count': len(results)})


@api_bp.post('/export/bid-details')
@jwt_required()
def export_bids():
    from modules.query import export_bid_details
    data = request.get_json() or {}
    project_ids = data.get('project_ids')
    path, details = export_bid_details(project_ids=project_ids)
    return success({'path': path, 'count': len(details)})


# ---------------- 日志 ----------------
@api_bp.get('/logs')
@jwt_required()
def list_logs():
    from modules.logger import query_logs
    logs = query_logs(
        module=request.args.get('module'),
        operation_type=request.args.get('operation_type'),
        operator=request.args.get('operator'),
        start_date=request.args.get('start_date'),
        end_date=request.args.get('end_date'),
        limit=int(request.args.get('limit', 100)),
    )
    return success(logs)


# ---------------- PDF导出 ----------------
@api_bp.get('/export/review-report-pdf/<int:tid>')
@jwt_required()
def export_review_pdf(tid):
    try:
        from backend.pdf_export import generate_review_report_pdf
        from modules.tender import get_tender_project
        t = get_tender_project(tid)
        if not t:
            return error('项目不存在', 404)
        pdf_path = generate_review_report_pdf(t)
        return success({'pdf_path': pdf_path})
    except Exception as e:
        return error(f'PDF生成失败: {str(e)}')


@api_bp.get('/export/weekly-report-pdf')
@jwt_required()
def export_weekly_pdf():
    try:
        from modules.statistics import generate_weekly_statistics
        from backend.pdf_export import generate_weekly_report_pdf
        stats, content, _ = generate_weekly_statistics()
        pdf_path = generate_weekly_report_pdf(stats, content)
        return success({'pdf_path': pdf_path})
    except Exception as e:
        return error(f'PDF生成失败: {str(e)}')


# ---------------- WebSocket测试 ----------------
@api_bp.post('/test-ws-push')
@jwt_required()
def test_ws_push():
    from backend.extensions import socketio
    data = request.get_json() or {}
    socketio.emit('project_notification', {
        'type': 'test',
        'content': data.get('content', '测试消息'),
        'time': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })
    return success(msg='推送测试完成')
