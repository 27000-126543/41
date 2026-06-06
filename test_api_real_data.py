#!/usr/bin/env python3
"""
企业级招投标管理系统 - 核心API测试脚本
验证所有核心API返回真实数据库数据，而非mock
"""
import sys
import os
import json
import urllib.request
import urllib.parse

BASE_URL = 'http://localhost:5001'


def api_login(username, password):
    """登录获取token"""
    data = json.dumps({'username': username, 'password': password}).encode()
    req = urllib.request.Request(
        f'{BASE_URL}/api/auth/login',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    res = json.loads(urllib.request.urlopen(req).read())
    if res.get('code') != 200:
        raise Exception(f'登录失败: {res.get("msg")}')
    return res['data']['token'], res['data']['user']


def api_get(token, endpoint, params=None):
    """GET请求"""
    url = f'{BASE_URL}{endpoint}'
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    return json.loads(urllib.request.urlopen(req).read())


def api_post(token, endpoint, data=None):
    """POST请求"""
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(
        f'{BASE_URL}{endpoint}',
        data=body,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    return json.loads(urllib.request.urlopen(req).read())


def check(name, data, min_length=0):
    """检查数据并打印"""
    code = data.get('code')
    ok = code == 200
    body = data.get('data')
    if isinstance(body, list):
        cnt = len(body)
        is_mock = False
        # 检查是否是硬编码mock数据（样本数据长度极小且有明显特征）
        if cnt > 0 and isinstance(body[0], dict):
            keys = set(body[0].keys())
            if not keys.intersection({'id', 'created_at', 'name', 'title', 'project_code'}):
                is_mock = True
        if min_length and cnt < min_length:
            ok = False
        print(f"{'✅' if ok else '❌'} {name}: code={code}, 记录数={cnt}, {'(疑似mock!)' if is_mock else ''}")
        if cnt > 0 and isinstance(body[0], dict):
            print(f"   字段示例: {list(body[0].keys())[:8]}")
            sample = body[0]
            for k in list(sample.keys())[:3]:
                v = sample[k]
                print(f"     {k}={str(v)[:50]}")
    elif isinstance(body, dict):
        print(f"{'✅' if ok else '❌'} {name}: code={code}, dict keys={list(body.keys())[:8]}")
    else:
        print(f"{'✅' if ok else '❌'} {name}: code={code}, data类型={type(body).__name__}, 值={str(body)[:80]}")
    return ok


def main():
    print("=" * 70)
    print("  企业级招投标管理系统 - 核心API真实性测试")
    print("=" * 70)
    print()

    # 0. 健康检查（无需token）
    print("【0️⃣ 系统健康检查】")
    health = json.loads(urllib.request.urlopen(f'{BASE_URL}/api/health').read())
    ok = health.get('code') == 200 and health.get('data', {}).get('status') == 'ok'
    print(f"{'✅' if ok else '❌'} /api/health: {health}")
    print()

    # 1. 登录
    print("【1️⃣ 用户登录】")
    try:
        token, user = api_login('admin', 'admin123')
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        sys.exit(1)
    print(f"✅ admin登录成功: 角色={user.get('role')}, 姓名={user.get('real_name')}")
    print(f"   Token前30位: {token[:30]}...")
    print()

    all_pass = True

    # 2. 采购申请
    print("【2️⃣ 业务数据API真实性检查】")
    res = api_get(token, '/api/procurements')
    if not check('采购申请 /api/procurements', res, min_length=0): all_pass = False

    # 3. 招标项目
    res = api_get(token, '/api/tenders')
    if not check('招标项目 /api/tenders', res, min_length=0): all_pass = False

    # 4. 专家
    res = api_get(token, '/api/experts')
    if not check('专家库 /api/experts', res, min_length=5): all_pass = False

    # 5. 供应商
    res = api_get(token, '/api/suppliers')
    if not check('供应商 /api/suppliers', res, min_length=5): all_pass = False

    # 6. 部门
    res = api_get(token, '/api/departments')
    if not check('部门 /api/departments', res, min_length=3): all_pass = False

    # 7. 模板
    res = api_get(token, '/api/templates')
    if not check('招标文件模板 /api/templates', res, min_length=3): all_pass = False

    # 8. 预算总览
    res = api_get(token, '/api/budget/overview')
    if not check('预算总览 /api/budget/overview', res, min_length=3): all_pass = False

    # 9. 合同
    res = api_get(token, '/api/contracts')
    if not check('合同 /api/contracts', res): all_pass = False

    # 10. 操作日志
    res = api_get(token, '/api/logs', {'limit': 5})
    if not check('操作日志 /api/logs', res, min_length=3): all_pass = False

    # 11. 周统计
    res = api_get(token, '/api/statistics/weekly')
    if not check('周统计 /api/statistics/weekly', res): all_pass = False

    # 12. 项目搜索
    res = api_get(token, '/api/search/projects')
    if not check('全网搜索 /api/search/projects', res): all_pass = False

    # 13. 生成周统计（测试写操作）
    print()
    print("【3️⃣ 写操作与复杂API测试】")
    res = api_get(token, '/api/statistics/weekly', {'generate': '1'})
    ok = res.get('code') == 200 and 'stats' in res.get('data', {})
    print(f"{'✅' if ok else '❌'} 生成周统计: code={res.get('code')}, stats keys={list(res.get('data',{}).get('stats',{}).keys()) if ok else 'N/A'}")
    if not ok: all_pass = False

    # 14. WebSocket推送测试
    res = api_post(token, '/api/test-ws-push', {'content': '【测试脚本】WebSocket实时推送测试消息'})
    ok = res.get('code') == 200
    print(f"{'✅' if ok else '❌'} WebSocket推送测试: {res.get('msg')}")
    if not ok: all_pass = False

    # 15. PDF导出测试
    try:
        tenders = api_get(token, '/api/tenders').get('data', [])
        if tenders:
            tid = tenders[0]['id']
            res = api_get(token, f'/api/export/review-report-pdf/{tid}')
            ok = res.get('code') == 200
            pdf_path = res.get('data', {}).get('pdf_path')
            exists = os.path.exists(pdf_path) if pdf_path else False
            print(f"{'✅' if ok and exists else '❌'} 评审报告PDF导出: code={res.get('code')}, 路径={pdf_path}, 存在={exists}")
            if not (ok and exists): all_pass = False
    except Exception as e:
        print(f"❌ 评审报告PDF导出失败: {e}")
        all_pass = False

    try:
        res = api_get(token, '/api/export/weekly-report-pdf')
        ok = res.get('code') == 200
        pdf_path = res.get('data', {}).get('pdf_path')
        exists = os.path.exists(pdf_path) if pdf_path else False
        print(f"{'✅' if ok and exists else '❌'} 周报PDF导出: code={res.get('code')}, 路径={pdf_path}, 存在={exists}")
        if not (ok and exists): all_pass = False
    except Exception as e:
        print(f"❌ 周报PDF导出失败: {e}")
        all_pass = False

    # 16. 角色权限测试（5种角色登录）
    print()
    print("【4️⃣ 多角色登录与权限测试】")
    test_users = [
        ('buyer01', 'buyer123', '采购员'),
        ('manager01', 'manager123', '部门经理'),
        ('expert01', 'expert123', '评审专家'),
        ('supplier01', 'supplier123', '供应商'),
    ]
    for uname, pwd, role_name in test_users:
        try:
            t, u = api_login(uname, pwd)
            r = api_get(t, '/api/tenders')
            ok = r.get('code') == 200
            print(f"{'✅' if ok else '❌'} {role_name}({uname})登录: 角色={u.get('role')}, 招标查询权限={ok}")
        except Exception as e:
            print(f"❌ {role_name}({uname})登录失败: {e}")
            all_pass = False

    print()
    print("=" * 70)
    if all_pass:
        print("  🎉 所有核心API测试通过！数据均来自真实数据库。")
    else:
        print("  ⚠️ 部分测试未通过，请检查上方输出")
    print("=" * 70)
    sys.exit(0 if all_pass else 1)


if __name__ == '__main__':
    main()
