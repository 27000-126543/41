"""
企业级招投标全流程自动化管理系统 - 配置文件
"""
import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
REPORTS_DIR = os.path.join(OUTPUT_DIR, 'reports')
CONTRACTS_DIR = os.path.join(OUTPUT_DIR, 'contracts')
EXPORTS_DIR = os.path.join(OUTPUT_DIR, 'exports')
LOGS_DIR = os.path.join(OUTPUT_DIR, 'logs')

for d in [DATA_DIR, OUTPUT_DIR, REPORTS_DIR, CONTRACTS_DIR, EXPORTS_DIR, LOGS_DIR]:
    os.makedirs(d, exist_ok=True)

DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')
if DB_TYPE == 'postgresql':
    DATABASE_URL = os.environ.get(
        'DATABASE_URL',
        'postgresql://bidding:bidding123@localhost:5432/bidding_system'
    )
else:
    DATABASE_PATH = os.path.join(DATA_DIR, 'bidding_system.db')
    DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

WEIGHT_CONFIG = {
    'default': {
        'technical': 0.40,
        'commercial': 0.35,
        'qualification': 0.25
    },
    'engineering': {
        'technical': 0.50,
        'commercial': 0.30,
        'qualification': 0.20
    },
    'service': {
        'technical': 0.35,
        'commercial': 0.35,
        'qualification': 0.30
    },
    'goods': {
        'technical': 0.30,
        'commercial': 0.45,
        'qualification': 0.25
    }
}

PERFORMANCE_WARNING_DAYS = 2

NOTIFICATION_CONFIG = {
    'webhook_url': 'https://example.com/project-group-webhook',
    'email_smtp': 'smtp.company.com',
    'email_port': 587,
    'email_user': 'bidding@company.com'
}

EXPERT_REVIEW_RULES = {
    'min_experts': 5,
    'remove_highest': True,
    'remove_lowest': True,
    'avoid_relations': True
}

STATISTICS_SCHEDULE = {
    'day': 'monday',
    'time': '09:00'
}

BIDDING_PERIOD_DAYS = {
    'small': 7,
    'medium': 15,
    'large': 20
}

AMOUNT_THRESHOLDS = {
    'small': 500000,
    'medium': 5000000
}
