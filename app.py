#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业级招投标全流程自动化管理系统 - Flask Web应用入口
"""
import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from flask import Flask, send_from_directory, jsonify

from backend.config import Config
from backend.models import db
from backend.extensions import jwt, cors, socketio, scheduler
from backend.routes.auth import auth_bp, init_demo_users
from backend.routes.api import api_bp
from backend.scheduler import init_scheduler
from backend.websocket import broadcast_log_operation

import backend.websocket  # 注册WebSocket事件


def _patch_logger_to_ws():
    """将现有logger.py的推送也发到WebSocket"""
    try:
        import modules.logger as logger_module
        original_push = logger_module.push_to_project_group

        def patched_push(log_id, op_type, module, operator, record_id, detail):
            result = original_push(log_id, op_type, module, operator, record_id, detail)
            from datetime import datetime
            broadcast_log_operation({
                'id': log_id,
                'operation_type': op_type,
                'module': module,
                'operator': operator,
                'record_id': record_id,
                'detail': detail,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })
            return result

        logger_module.push_to_project_group = patched_push
        print("[WebSocket] 日志推送已桥接到WebSocket")
    except Exception as e:
        print(f"[WebSocket] 日志桥接失败: {e}")


def create_app(config_class=Config):
    app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    socketio.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    _patch_logger_to_ws()

    @app.route('/')
    def index():
        dist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')
        if os.path.exists(os.path.join(dist_path, 'index.html')):
            return send_from_directory(dist_path, 'index.html')
        return jsonify({
            'service': '企业级招投标全流程自动化管理系统',
            'version': '2.0.0-web',
            'api_docs': '/api/health',
            'frontend': '请构建Vue前端: cd frontend && npm install && npm run build',
        })

    @app.route('/api/info')
    def system_info():
        return jsonify({
            'code': 200,
            'data': {
                'name': '企业级招投标全流程自动化管理系统',
                'version': '2.0.0',
                'db_type': app.config.get('DB_TYPE', 'sqlite'),
                'features': [
                    '采购申请自动提取', '预算校验审批', '招标项目自动发布',
                    '投标加密解密', '专家回避分配', '自动评分汇总',
                    '中标通知合同', '履约监控预警', '周统计可视化',
                    '组合查询导出', '实时推送WebSocket', '权限管理'
                ],
                'roles': ['admin管理员', 'procurement采购员', 'manager部门经理', 'expert评审专家', 'supplier供应商'],
            }
        })

    with app.app_context():
        from core.schema import init_database, seed_demo_data
        init_database()
        seed_demo_data()

        db.create_all()
        created = init_demo_users()
        if created > 0:
            print(f"[初始化] 创建了 {created} 个演示用户账号")

    init_scheduler()

    return app


def run_dev():
    app = create_app()
    print("\n" + "=" * 60)
    print("  企业级招投标全流程自动化管理系统 Web版 v2.0")
    print("=" * 60)
    print("  🖥  后端地址: http://localhost:5001")
    print("  📡 WebSocket: ws://localhost:5001")
    print("  📖 健康检查: http://localhost:5001/api/health")
    print("  👤 演示账号:")
    print("     管理员  admin / admin123")
    print("     采购员  buyer01 / buyer123")
    print("     部门经理 manager01 / manager123")
    print("     评审专家 expert01~03 / expert123")
    print("     供应商   supplier01~03 / supplier123")
    print("=" * 60 + "\n")
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    run_dev()
