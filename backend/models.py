"""
SQLAlchemy ORM 数据库模型 - 用户/角色/权限 + 业务数据模型
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(80))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False, default='supplier')
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    expert_id = db.Column(db.Integer, db.ForeignKey('experts.id'), nullable=True)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)

    department = db.relationship('Department', backref='users', foreign_keys=[department_id])
    supplier = db.relationship('Supplier', backref='user', foreign_keys=[supplier_id], uselist=False)
    expert = db.relationship('Expert', backref='user', foreign_keys=[expert_id], uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'role_name': {
                'admin': '系统管理员',
                'procurement': '采购员',
                'expert': '评审专家',
                'supplier': '供应商',
                'manager': '部门经理',
            }.get(self.role, self.role),
            'department_id': self.department_id,
            'supplier_id': self.supplier_id,
            'expert_id': self.expert_id,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None,
        }

    def has_permission(self, permission):
        from backend.config import PERMISSIONS
        perms = PERMISSIONS.get(self.role, [])
        return 'all' in perms or permission in perms


class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    budget_limit = db.Column(db.Float, default=0.0)
    budget_used = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'budget_limit': self.budget_limit,
            'budget_used': self.budget_used,
            'available_budget': self.budget_limit - self.budget_used,
            'usage_percent': round((self.budget_used / self.budget_limit * 100), 2) if self.budget_limit > 0 else 0,
        }


class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_name = db.Column(db.String(200), nullable=False)
    unified_social_code = db.Column(db.String(50), unique=True)
    legal_representative = db.Column(db.String(80))
    contact_person = db.Column(db.String(80))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(120))
    address = db.Column(db.String(500))
    business_scope = db.Column(db.Text)
    qualification_level = db.Column(db.String(50))
    credit_score = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'unified_social_code': self.unified_social_code,
            'legal_representative': self.legal_representative,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'address': self.address,
            'business_scope': self.business_scope,
            'qualification_level': self.qualification_level,
            'credit_score': self.credit_score,
            'status': self.status,
        }


class Expert(db.Model):
    __tablename__ = 'experts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    expert_code = db.Column(db.String(50), unique=True, nullable=False)
    gender = db.Column(db.String(10))
    title = db.Column(db.String(80))
    organization = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    specialty = db.Column(db.String(200), nullable=False)
    sub_specialty = db.Column(db.String(200))
    years_of_experience = db.Column(db.Integer)
    is_active = db.Column(db.Integer, default=1)
    avoid_suppliers = db.Column(db.Text)
    avoid_companies = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'expert_code': self.expert_code,
            'gender': self.gender,
            'title': self.title,
            'organization': self.organization,
            'phone': self.phone,
            'email': self.email,
            'specialty': self.specialty,
            'sub_specialty': self.sub_specialty,
            'years_of_experience': self.years_of_experience,
            'is_active': self.is_active,
            'avoid_suppliers': self.avoid_suppliers,
            'avoid_companies': self.avoid_companies,
        }
