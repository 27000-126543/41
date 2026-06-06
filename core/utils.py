"""
工具函数模块
"""
import hashlib
import random
import string
from datetime import datetime, timedelta
import base64
import json
import re


def generate_project_code(category="PRJ"):
    prefix = category.upper()[:3]
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{date_str}-{random_str}"


def generate_contract_code():
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"HT-{date_str}-{random_str}"


def encrypt_content(content, key="bidding_system_key_2024"):
    if not content:
        return ""
    content_bytes = content.encode('utf-8')
    key_bytes = key.encode('utf-8')
    encrypted = bytearray()
    for i, b in enumerate(content_bytes):
        encrypted.append(b ^ key_bytes[i % len(key_bytes)])
    return base64.b64encode(bytes(encrypted)).decode('utf-8')


def decrypt_content(encrypted_content, key="bidding_system_key_2024"):
    if not encrypted_content:
        return ""
    encrypted_bytes = base64.b64decode(encrypted_content.encode('utf-8'))
    key_bytes = key.encode('utf-8')
    decrypted = bytearray()
    for i, b in enumerate(encrypted_bytes):
        decrypted.append(b ^ key_bytes[i % len(key_bytes)])
    return bytes(decrypted).decode('utf-8')


def format_amount(amount):
    return f"¥{amount:,.2f}"


def get_date_str(date_obj=None):
    if date_obj is None:
        date_obj = datetime.now()
    return date_obj.strftime("%Y-%m-%d")


def get_datetime_str(dt_obj=None):
    if dt_obj is None:
        dt_obj = datetime.now()
    return dt_obj.strftime("%Y-%m-%d %H:%M:%S")


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


def days_between(date1_str, date2_str):
    d1 = parse_date(date1_str)
    d2 = parse_date(date2_str)
    if d1 and d2:
        return (d2 - d1).days
    return 0


def add_days(date_str, days):
    d = parse_date(date_str)
    if d:
        return (d + timedelta(days=days)).strftime("%Y-%m-%d")
    return ""


def extract_info_from_text(text):
    info = {}
    if not text:
        return info
    amount_match = re.search(r'(\d+[\d,]*\.?\d*)\s*(?:元|万|万元|RMB|¥)', text)
    if amount_match:
        raw = amount_match.group(1).replace(',', '')
        info['amount'] = float(raw)
        if '万' in amount_match.group(0):
            info['amount'] *= 10000
    date_match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)', text)
    if date_match:
        info['date'] = date_match.group(1).replace('年', '-').replace('月', '-').replace('/', '-').replace('日', '')
    category_keywords = {
        '软件开发': 'goods', '系统': 'goods', '硬件': 'goods', '设备': 'goods',
        '工程': 'engineering', '施工': 'engineering', '建设': 'engineering',
        '服务': 'service', '咨询': 'service', '运维': 'service', '培训': 'service'
    }
    for kw, cat in category_keywords.items():
        if kw in text:
            info['category'] = cat
            break
    return info


def md5_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()
