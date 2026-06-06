"""
Web后端配置
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'bidding-system-secret-key-2024-enterprise')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-bidding-enterprise-2024-secret')
    JWT_ACCESS_TOKEN_EXPIRES = 86400

    DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')

    if DB_TYPE == 'postgresql':
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            'DATABASE_URL',
            'postgresql://bidding:bidding123@localhost:5432/bidding_system'
        )
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'data', 'bidding_system.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')

    SCHEDULER_API_ENABLED = True


ROLES = {
    'admin': '系统管理员',
    'procurement': '采购员',
    'expert': '评审专家',
    'supplier': '供应商',
    'manager': '部门经理',
}

PERMISSIONS = {
    'admin': ['all'],
    'procurement': [
        'procurement:create', 'procurement:view',
        'tender:create', 'tender:view', 'tender:publish',
        'bid:view', 'expert:assign',
        'review:view', 'award:view', 'award:decide',
        'contract:view', 'contract:create',
        'performance:view', 'statistics:view',
        'query:all',
    ],
    'expert': [
        'review:score', 'review:view',
        'tender:view', 'bid:view',
    ],
    'supplier': [
        'tender:view',
        'bid:create', 'bid:view', 'bid:mine',
        'award:view',
    ],
    'manager': [
        'budget:approve', 'budget:view',
        'procurement:view', 'tender:view',
        'statistics:view', 'query:all',
        'performance:view',
    ],
}
