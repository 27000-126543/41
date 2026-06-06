"""
认证路由 - 登录、注册、用户信息
"""
from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from backend.models import db, User, Department, Supplier, Expert
from backend.auth import success, error, get_current_user

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.post('/login')
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return error('请输入用户名和密码')

    user = User.query.filter_by(username=username).first()
    if not user:
        return error('用户不存在')
    if user.status != 'active':
        return error('账号已被禁用')
    if not user.check_password(password):
        return error('密码错误')

    user.last_login = datetime.now()
    db.session.commit()

    token = create_access_token(identity=username)
    return success({
        'token': token,
        'user': user.to_dict(),
    }, '登录成功')


@auth_bp.get('/profile')
@jwt_required()
def profile():
    user = get_current_user()
    if not user:
        return error('用户不存在', 401)
    return success(user.to_dict())


@auth_bp.post('/change-password')
@jwt_required()
def change_password():
    data = request.get_json() or {}
    old_pwd = data.get('old_password', '')
    new_pwd = data.get('new_password', '')

    if not old_pwd or not new_pwd:
        return error('请输入新旧密码')
    if len(new_pwd) < 6:
        return error('新密码至少6位')

    user = get_current_user()
    if not user.check_password(old_pwd):
        return error('原密码错误')

    user.set_password(new_pwd)
    db.session.commit()
    return success(msg='密码修改成功')


@auth_bp.get('/users')
@jwt_required()
def list_users():
    current = get_current_user()
    if current.role != 'admin':
        return error('仅管理员可查看', 403)

    users = User.query.order_by(User.created_at.desc()).all()
    return success([u.to_dict() for u in users])


def init_demo_users():
    """初始化演示用户"""
    demo_users = [
        ('admin', 'admin123', '系统管理员', 'admin', 'admin@company.com', '13800000000', None, None, None),
        ('buyer01', 'buyer123', '张采购', 'procurement', 'buyer@company.com', '13800000001', 1, None, None),
        ('manager01', 'manager123', '王经理', 'manager', 'manager@company.com', '13800000002', 1, None, None),
    ]

    expert_count = 0
    for exp in Expert.query.limit(5).all():
        username = f"expert{exp.id:02d}"
        demo_users.append((
            username, 'expert123', exp.name, 'expert',
            exp.email or f"{username}@expert.com", exp.phone,
            None, None, exp.id
        ))
        expert_count += 1
        if expert_count >= 3:
            break

    supplier_count = 0
    for sup in Supplier.query.limit(5).all():
        username = f"supplier{sup.id:02d}"
        demo_users.append((
            username, 'supplier123', sup.contact_person or sup.company_name, 'supplier',
            sup.contact_email or f"{username}@supplier.com", sup.contact_phone,
            None, sup.id, None
        ))
        supplier_count += 1
        if supplier_count >= 3:
            break

    created = 0
    for username, pwd, real_name, role, email, phone, dept_id, sup_id, exp_id in demo_users:
        existing = User.query.filter_by(username=username).first()
        if not existing:
            user = User(
                username=username,
                real_name=real_name,
                email=email,
                phone=phone,
                role=role,
                department_id=dept_id,
                supplier_id=sup_id,
                expert_id=exp_id,
            )
            user.set_password(pwd)
            db.session.add(user)
            created += 1

    if created > 0:
        db.session.commit()

    return created
