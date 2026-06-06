"""
权限装饰器和JWT工具
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from backend.models import User


def role_required(*roles):
    """
    角色权限装饰器
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            username = get_jwt_identity()
            user = User.query.filter_by(username=username).first()
            if not user:
                return jsonify(code=401, msg='用户不存在'), 401
            if user.role not in roles and user.role != 'admin':
                return jsonify(code=403, msg=f'无权限操作，需要角色: {roles}'), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper


def permission_required(permission):
    """
    细粒度权限装饰器
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            username = get_jwt_identity()
            user = User.query.filter_by(username=username).first()
            if not user:
                return jsonify(code=401, msg='用户不存在'), 401
            if not user.has_permission(permission):
                return jsonify(code=403, msg=f'无权限: {permission}'), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper


def get_current_user():
    username = get_jwt_identity()
    return User.query.filter_by(username=username).first()


def success(data=None, msg='success'):
    resp = {'code': 200, 'msg': msg}
    if data is not None:
        resp['data'] = data
    return jsonify(resp)


def error(msg='error', code=400):
    return jsonify({'code': code, 'msg': msg}), code
