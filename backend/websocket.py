"""
WebSocket事件处理器 - 实时推送项目群消息
"""
from flask_socketio import emit
from backend.extensions import socketio


connected_clients = set()


@socketio.on('connect')
def handle_connect():
    from flask import request
    connected_clients.add(request.sid)
    print(f'[WebSocket] 客户端连接: {request.sid} (当前在线: {len(connected_clients)})')
    emit('connected', {
        'status': 'ok',
        'message': '已连接到招投标系统实时推送',
        'online_count': len(connected_clients),
    })


@socketio.on('disconnect')
def handle_disconnect():
    from flask import request
    if request.sid in connected_clients:
        connected_clients.remove(request.sid)
    print(f'[WebSocket] 客户端断开: {request.sid} (当前在线: {len(connected_clients)})')


@socketio.on('join_project_group')
def handle_join_group(data):
    project_id = data.get('project_id', 'all')
    from flask import request
    print(f'[WebSocket] 客户端 {request.sid} 加入项目群: {project_id}')
    emit('group_joined', {'project_id': project_id, 'status': 'ok'})


@socketio.on('send_group_message')
def handle_group_message(data):
    from flask import request
    from datetime import datetime
    message = {
        'type': 'group_chat',
        'from': data.get('from', 'user'),
        'content': data.get('content', ''),
        'project_id': data.get('project_id'),
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    emit('project_notification', message, broadcast=True)


def broadcast_log_operation(log_data):
    """将操作日志广播到所有WebSocket客户端"""
    try:
        socketio.emit('project_notification', {
            'type': 'operation_log',
            'title': f"[{log_data.get('module', '')}] {log_data.get('operation_type', '')}",
            'content': log_data.get('detail', ''),
            'operator': log_data.get('operator', ''),
            'time': log_data.get('created_at', ''),
            'raw': log_data,
        })
    except Exception:
        pass
