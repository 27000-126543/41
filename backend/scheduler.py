"""
定时任务 - APScheduler每周一自动统计
"""
import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


def weekly_statistics_job():
    """每周一上午9点自动生成周统计"""
    print(f"\n[定时任务] 执行每周统计 - {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        from modules.statistics import generate_weekly_statistics
        from backend.extensions import socketio

        stats, content, path = generate_weekly_statistics()

        socketio.emit('project_notification', {
            'type': 'weekly_report',
            'title': '📊 周统计报告已生成',
            'content': f"本周项目 {stats['total_projects']} 个，节约资金 ¥{stats['saved_amount']:,.2f}",
            'stats': stats,
            'report_path': path,
            'time': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })

        print(f"[定时任务] 周统计完成 - 节约¥{stats['saved_amount']:,.2f}")
        return stats
    except Exception as e:
        print(f"[定时任务] 周统计失败: {e}")
        return None


def daily_performance_check_job():
    """每日检查履约超期节点"""
    print(f"\n[定时任务] 每日履约检查")
    try:
        from modules.performance import check_overdue_milestones
        from backend.extensions import socketio

        warnings = check_overdue_milestones()
        if warnings:
            socketio.emit('project_notification', {
                'type': 'performance_warning',
                'title': f"⚠️ 发现 {len(warnings)} 个超期履约节点",
                'content': '请相关项目经理立即处理',
                'count': len(warnings),
                'time': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })
        print(f"[定时任务] 履约检查完成 - 预警{len(warnings)}个")
        return warnings
    except Exception as e:
        print(f"[定时任务] 履约检查失败: {e}")
        return []


def init_scheduler():
    """初始化定时任务"""
    from backend.extensions import scheduler

    if not scheduler.running:
        try:
            scheduler.add_job(
                id='weekly_statistics',
                func=weekly_statistics_job,
                trigger='cron',
                day_of_week='mon',
                hour=9,
                minute=0,
                replace_existing=True,
            )
            scheduler.add_job(
                id='daily_performance_check',
                func=daily_performance_check_job,
                trigger='cron',
                hour=9,
                minute=30,
                replace_existing=True,
            )
            scheduler.start()
            print("[定时任务] APScheduler已启动: 每周一9点统计, 每日9:30履约检查")
        except Exception as e:
            print(f"[定时任务] 启动失败: {e}")
