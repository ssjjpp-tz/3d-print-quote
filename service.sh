#!/bin/bash
# 3D 打印报价服务 - 守护脚本

SERVICE_NAME="3d-quote"
WEB_SCRIPT="/home/admin/.openclaw/workspace/skills/3d-print-quote/simple_web.py"
ADMIN_SCRIPT="/home/admin/.openclaw/workspace/skills/3d-print-quote/admin_server.py"
WEB_PORT=5000
ADMIN_PORT=5001
LOG_DIR="/home/admin/.openclaw/workspace/skills/3d-print-quote/logs"

mkdir -p "$LOG_DIR"

start_service() {
    echo "Starting $SERVICE_NAME..."
    
    # 启动 Web 服务
    pkill -f "simple_web.py" 2>/dev/null
    sleep 1
    cd /home/admin/.openclaw/workspace/skills/3d-print-quote
    nohup python3 simple_web.py $WEB_PORT > "$LOG_DIR/web.log" 2>&1 &
    echo "Web server started on port $WEB_PORT"
    
    # 启动管理服务
    pkill -f "admin_server.py" 2>/dev/null
    sleep 1
    nohup python3 admin_server.py $ADMIN_PORT > "$LOG_DIR/admin.log" 2>&1 &
    echo "Admin server started on port $ADMIN_PORT"
    
    sleep 2
    
    # 检查服务
    if curl -s http://localhost:$WEB_PORT > /dev/null; then
        echo "✅ Web service OK"
    else
        echo "❌ Web service FAILED"
    fi
    
    if curl -s http://localhost:$ADMIN_PORT > /dev/null; then
        echo "✅ Admin service OK"
    else
        echo "❌ Admin service FAILED"
    fi
}

stop_service() {
    echo "Stopping $SERVICE_NAME..."
    pkill -f "simple_web.py"
    pkill -f "admin_server.py"
    echo "Stopped"
}

restart_service() {
    stop_service
    sleep 2
    start_service
}

check_status() {
    echo "=== $SERVICE_NAME Status ==="
    
    WEB_PID=$(pgrep -f "simple_web.py" || echo "")
    ADMIN_PID=$(pgrep -f "admin_server.py" || echo "")
    
    if [ -n "$WEB_PID" ]; then
        echo "✅ Web server (PID: $WEB_PID) - Port $WEB_PORT"
    else
        echo "❌ Web server NOT RUNNING"
    fi
    
    if [ -n "$ADMIN_PID" ]; then
        echo "✅ Admin server (PID: $ADMIN_PID) - Port $ADMIN_PORT"
    else
        echo "❌ Admin server NOT RUNNING"
    fi
    
    echo ""
    echo "=== Nginx Status ==="
    systemctl is-active nginx
}

case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        check_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
