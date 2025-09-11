#!/bin/bash
# -*- coding: utf-8 -*-
# Lark机器人后台服务管理脚本
# 支持 start/stop/restart/status/logs 命令

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/start_lark_with_logging.py"
PID_FILE="$SCRIPT_DIR/lark_bot.pid"
LOG_DIR="$SCRIPT_DIR/logs"
DAEMON_LOG="$LOG_DIR/daemon.log"

# 服务配置
HOST="0.0.0.0"
PORT="8080"
PYTHON_CMD="python3"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_info() {
    print_message "$BLUE" "ℹ️  $1"
}

print_success() {
    print_message "$GREEN" "✅ $1"
}

print_warning() {
    print_message "$YELLOW" "⚠️  $1"
}

print_error() {
    print_message "$RED" "❌ $1"
}

# 创建必要的目录
create_directories() {
    mkdir -p "$LOG_DIR"
    touch "$DAEMON_LOG"
}

# 检查Python脚本是否存在
check_python_script() {
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Python脚本不存在: $PYTHON_SCRIPT"
        exit 1
    fi
}

# 获取进程ID
get_pid() {
    if [[ -f "$PID_FILE" ]]; then
        cat "$PID_FILE"
    else
        echo ""
    fi
}

# 检查进程是否在运行
is_running() {
    local pid=$(get_pid)
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# 启动服务
start_service() {
    print_info "启动Lark机器人服务..."
    
    # 检查是否已经在运行
    if is_running; then
        local pid=$(get_pid)
        print_warning "服务已经在运行 (PID: $pid)"
        return 1
    fi
    
    # 检查Python脚本
    check_python_script
    
    # 创建目录
    create_directories
    
    # 记录启动日志
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 启动Lark机器人服务" >> "$DAEMON_LOG"
    
    # 启动服务
    cd "$SCRIPT_DIR"
    nohup $PYTHON_CMD "$PYTHON_SCRIPT" --host "$HOST" --port "$PORT" --log-dir "$LOG_DIR" > "$DAEMON_LOG" 2>&1 &
    local pid=$!
    
    # 保存PID
    echo "$pid" > "$PID_FILE"
    
    # 等待一下确保启动成功
    sleep 2
    
    if is_running; then
        print_success "Lark机器人服务启动成功!"
        print_info "PID: $pid"
        print_info "服务地址: http://$HOST:$PORT"
        print_info "Webhook地址: http://$HOST:$PORT/webhook"
        print_info "日志目录: $LOG_DIR"
        
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 服务启动成功 (PID: $pid)" >> "$DAEMON_LOG"
    else
        print_error "服务启动失败!"
        rm -f "$PID_FILE"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 服务启动失败" >> "$DAEMON_LOG"
        return 1
    fi
}

# 停止服务
stop_service() {
    print_info "停止Lark机器人服务..."
    
    if ! is_running; then
        print_warning "服务未运行"
        rm -f "$PID_FILE"
        return 1
    fi
    
    local pid=$(get_pid)
    print_info "正在停止进程 $pid..."
    
    # 尝试优雅停止
    kill -TERM "$pid" 2>/dev/null
    
    # 等待进程停止
    local count=0
    while is_running && [[ $count -lt 10 ]]; do
        sleep 1
        count=$((count + 1))
        print_info "等待进程停止... ($count/10)"
    done
    
    # 如果还在运行，强制停止
    if is_running; then
        print_warning "优雅停止失败，强制终止进程..."
        kill -KILL "$pid" 2>/dev/null
        sleep 1
    fi
    
    # 检查是否成功停止
    if ! is_running; then
        print_success "Lark机器人服务已停止"
        rm -f "$PID_FILE"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 服务已停止 (PID: $pid)" >> "$DAEMON_LOG"
    else
        print_error "无法停止服务"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 服务停止失败 (PID: $pid)" >> "$DAEMON_LOG"
        return 1
    fi
}

# 重启服务
restart_service() {
    print_info "重启Lark机器人服务..."
    stop_service
    sleep 2
    start_service
}

# 查看服务状态
status_service() {
    print_info "Lark机器人服务状态:"
    echo "=================================="
    
    if is_running; then
        local pid=$(get_pid)
        print_success "服务状态: 运行中"
        print_info "进程ID: $pid"
        print_info "服务地址: http://$HOST:$PORT"
        print_info "Webhook地址: http://$HOST:$PORT/webhook"
        
        # 显示进程信息
        if command -v ps >/dev/null 2>&1; then
            echo ""
            print_info "进程详情:"
            ps -p "$pid" -o pid,ppid,user,start,time,command 2>/dev/null || print_warning "无法获取进程详情"
        fi
        
        # 显示端口监听状态
        if command -v lsof >/dev/null 2>&1; then
            echo ""
            print_info "端口监听:"
            lsof -i :$PORT 2>/dev/null | head -5 || print_warning "无法获取端口信息"
        fi
        
    else
        print_warning "服务状态: 未运行"
        if [[ -f "$PID_FILE" ]]; then
            print_warning "发现残留PID文件，正在清理..."
            rm -f "$PID_FILE"
        fi
    fi
    
    # 显示日志文件信息
    echo ""
    print_info "日志文件:"
    if [[ -d "$LOG_DIR" ]]; then
        ls -la "$LOG_DIR"/*.log 2>/dev/null | while read line; do
            echo "  $line"
        done
    else
        print_warning "日志目录不存在: $LOG_DIR"
    fi
}

# 查看日志
show_logs() {
    local log_type=${1:-"main"}
    local lines=${2:-50}
    
    case $log_type in
        "main"|"m")
            local log_file="$LOG_DIR/lark_bot.log"
            ;;
        "error"|"e")
            local log_file="$LOG_DIR/lark_error.log"
            ;;
        "access"|"a")
            local log_file="$LOG_DIR/lark_access.log"
            ;;
        "performance"|"perf"|"p")
            local log_file="$LOG_DIR/lark_performance.log"
            ;;
        "daemon"|"d")
            local log_file="$DAEMON_LOG"
            ;;
        *)
            print_error "不支持的日志类型: $log_type"
            echo "支持的类型: main(m), error(e), access(a), performance(perf/p), daemon(d)"
            return 1
            ;;
    esac
    
    if [[ -f "$log_file" ]]; then
        print_info "显示 $log_type 日志 (最后 $lines 行):"
        print_info "文件: $log_file"
        echo "=================================="
        tail -n "$lines" "$log_file"
    else
        print_warning "日志文件不存在: $log_file"
    fi
}

# 实时查看日志
follow_logs() {
    local log_type=${1:-"main"}
    
    case $log_type in
        "main"|"m")
            local log_file="$LOG_DIR/lark_bot.log"
            ;;
        "error"|"e")
            local log_file="$LOG_DIR/lark_error.log"
            ;;
        "access"|"a")
            local log_file="$LOG_DIR/lark_access.log"
            ;;
        "performance"|"perf"|"p")
            local log_file="$LOG_DIR/lark_performance.log"
            ;;
        "daemon"|"d")
            local log_file="$DAEMON_LOG"
            ;;
        *)
            print_error "不支持的日志类型: $log_type"
            echo "支持的类型: main(m), error(e), access(a), performance(perf/p), daemon(d)"
            return 1
            ;;
    esac
    
    if [[ -f "$log_file" ]]; then
        print_info "实时查看 $log_type 日志:"
        print_info "文件: $log_file"
        print_info "按 Ctrl+C 退出"
        echo "=================================="
        tail -f "$log_file"
    else
        print_warning "日志文件不存在: $log_file"
        print_info "启动服务后再试"
    fi
}

# 清理日志
clean_logs() {
    print_info "清理日志文件..."
    
    if [[ -d "$LOG_DIR" ]]; then
        local log_count=$(find "$LOG_DIR" -name "*.log*" | wc -l)
        
        if [[ $log_count -gt 0 ]]; then
            echo -n "确定要删除所有日志文件吗? (y/N): "
            read -r confirm
            
            if [[ $confirm == "y" || $confirm == "Y" ]]; then
                rm -f "$LOG_DIR"/*.log*
                rm -f "$DAEMON_LOG"
                print_success "日志文件已清理"
                echo "$(date '+%Y-%m-%d %H:%M:%S') - 日志文件已清理" >> "$DAEMON_LOG"
            else
                print_info "取消清理操作"
            fi
        else
            print_info "没有日志文件需要清理"
        fi
    else
        print_info "日志目录不存在"
    fi
}

# 显示帮助信息
show_help() {
    echo "Lark机器人后台服务管理脚本"
    echo "==============================="
    echo ""
    echo "用法: $0 <命令> [参数]"
    echo ""
    echo "命令:"
    echo "  start             启动服务"
    echo "  stop              停止服务"
    echo "  restart           重启服务"
    echo "  status            查看服务状态"
    echo "  logs [类型] [行数] 查看日志"
    echo "  follow [类型]     实时查看日志"
    echo "  clean             清理日志文件"
    echo "  help              显示帮助信息"
    echo ""
    echo "日志类型:"
    echo "  main, m           主日志 (默认)"
    echo "  error, e          错误日志"
    echo "  access, a         访问日志"
    echo "  performance, p    性能日志"
    echo "  daemon, d         守护进程日志"
    echo ""
    echo "示例:"
    echo "  $0 start                    # 启动服务"
    echo "  $0 logs error 100           # 查看错误日志最后100行"
    echo "  $0 follow main              # 实时查看主日志"
    echo ""
    echo "配置:"
    echo "  服务地址: $HOST:$PORT"
    echo "  Python脚本: $PYTHON_SCRIPT"
    echo "  PID文件: $PID_FILE"
    echo "  日志目录: $LOG_DIR"
}

# 主函数
main() {
    local command=$1
    
    case $command in
        "start")
            start_service
            ;;
        "stop")
            stop_service
            ;;
        "restart")
            restart_service
            ;;
        "status")
            status_service
            ;;
        "logs")
            show_logs "$2" "$3"
            ;;
        "follow")
            follow_logs "$2"
            ;;
        "clean")
            clean_logs
            ;;
        "help"|"-h"|"--help"|"")
            show_help
            ;;
        *)
            print_error "未知命令: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"