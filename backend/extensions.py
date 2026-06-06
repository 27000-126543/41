"""
Flask扩展集中管理
"""
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_apscheduler import APScheduler

from backend.models import db

jwt = JWTManager()
cors = CORS()
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
scheduler = APScheduler()
