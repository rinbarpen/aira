#!/usr/bin/env python3
"""运行Aira Monitor独立服务

这个脚本会启动Monitor Web服务器，提供：
- 实时统计监控
- Web界面访问
- REST API接口

即使主程序关闭，Monitor服务也会继续运行。
"""

import argparse
from aira.monitor.server import run_server


def main():
    parser = argparse.ArgumentParser(
        description="Aira Monitor 独立监控服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认配置启动
  python run_monitor.py
  
  # 自定义端口启动
  python run_monitor.py --port 9090
  
  # 监听所有网络接口
  python run_monitor.py --host 0.0.0.0
  
  # 后台运行（Windows使用start命令）
  start /B python run_monitor.py
  
  # 后台运行（Linux/Mac）
  nohup python run_monitor.py > logs/monitor.log 2>&1 &
        """
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="监听地址（默认: 127.0.0.1，使用0.0.0.0监听所有网络接口）"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8090,
        help="监听端口（默认: 8090）"
    )
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()

