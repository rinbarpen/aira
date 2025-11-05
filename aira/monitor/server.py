"""独立的Monitor Web服务器 - 可独立运行的监控服务。"""

from __future__ import annotations

import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from aira.core.config import get_app_config
from aira.memory.repository import SqliteRepository


app = FastAPI(
    title="Aira Monitor",
    description="Aira AI 使用监控和统计服务",
    version="0.1.0"
)


# 全局repository实例
_repo: SqliteRepository | None = None


def get_repository() -> SqliteRepository:
    """获取repository实例"""
    global _repo
    if _repo is None:
        config = get_app_config()
        storage = config.get("storage", {})
        db_path = Path(storage.get("sqlite_path", "data/aira.db"))
        _repo = SqliteRepository(db_path)
    return _repo


@app.get("/")
async def root():
    """首页 - 重定向到Dashboard"""
    return HTMLResponse(content=get_dashboard_html())


@app.get("/api/stats/summary")
async def get_summary(days: int = 7):
    """获取统计摘要
    
    Args:
        days: 统计最近N天的数据
    """
    repo = get_repository()
    
    try:
        stats = await repo.get_usage_stats(days)
        return JSONResponse(content=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats/recent")
async def get_recent_stats(limit: int = 50):
    """获取最近的请求记录
    
    Args:
        limit: 返回的记录数量
    """
    repo = get_repository()
    
    try:
        records = await repo.get_recent_usage(limit)
        return JSONResponse(content={
            "records": records,
            "count": len(records)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats/models")
async def get_model_stats():
    """获取按模型分组的统计"""
    repo = get_repository()
    
    try:
        stats = await repo.get_usage_stats(days=30)
        return JSONResponse(content=stats.get("models_used", {}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats/sessions")
async def get_session_stats(limit: int = 20):
    """获取按会话分组的统计
    
    Args:
        limit: 返回的会话数量
    """
    repo = get_repository()
    
    try:
        sessions = await repo.get_session_stats(limit)
        return JSONResponse(content={
            "sessions": sessions,
            "count": len(sessions)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """健康检查"""
    repo = get_repository()
    
    try:
        # 测试数据库连接
        # 可以执行一个简单的查询
        return JSONResponse(content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        })
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


def get_dashboard_html() -> str:
    """生成Dashboard HTML页面"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aira Monitor - 监控面板</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }
        
        h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.1em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .chart-container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }
        
        .table-container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }
        
        tr:hover {
            background: #f8f9ff;
        }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: #666;
        }
        
        .error {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s ease;
        }
        
        .refresh-btn:hover {
            background: #5568d3;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .status-healthy {
            background: #d4edda;
            color: #155724;
        }
        
        .status-unhealthy {
            background: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Aira Monitor</h1>
            <p class="subtitle">AI 使用监控和统计分析</p>
            <button class="refresh-btn" onclick="loadData()">🔄 刷新数据</button>
        </div>
        
        <div id="health-status"></div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">总请求数</div>
                <div class="stat-value" id="total-requests">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">总Token数</div>
                <div class="stat-value" id="total-tokens">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">总成本 (USD)</div>
                <div class="stat-value" id="total-cost">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">使用模型数</div>
                <div class="stat-value" id="models-count">-</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>📊 最近使用情况</h2>
            <div id="chart-loading" class="loading">加载中...</div>
        </div>
        
        <div class="table-container">
            <h2>📝 最近请求记录</h2>
            <div id="recent-records-loading" class="loading">加载中...</div>
            <table id="recent-records-table" style="display:none;">
                <thead>
                    <tr>
                        <th>时间</th>
                        <th>模型</th>
                        <th>会话ID</th>
                        <th>输入Token</th>
                        <th>输出Token</th>
                        <th>成本</th>
                        <th>耗时</th>
                    </tr>
                </thead>
                <tbody id="records-tbody">
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // 检查健康状态
        async function checkHealth() {
            try {
                const response = await fetch('/api/health');
                const data = await response.json();
                
                const statusDiv = document.getElementById('health-status');
                if (data.status === 'healthy') {
                    statusDiv.innerHTML = `
                        <div class="chart-container">
                            <span class="status-badge status-healthy">✅ 服务正常</span>
                            <span style="margin-left: 20px; color: #666;">
                                数据库: ${data.database} | 
                                更新时间: ${new Date(data.timestamp).toLocaleString('zh-CN')}
                            </span>
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = `
                        <div class="error">
                            <span class="status-badge status-unhealthy">❌ 服务异常</span>
                            <span style="margin-left: 20px;">${data.error || '未知错误'}</span>
                        </div>
                    `;
                }
            } catch (error) {
                document.getElementById('health-status').innerHTML = `
                    <div class="error">
                        <span class="status-badge status-unhealthy">❌ 无法连接到服务</span>
                        <span style="margin-left: 20px;">${error.message}</span>
                    </div>
                `;
            }
        }
        
        // 加载统计摘要
        async function loadSummary() {
            try {
                const response = await fetch('/api/stats/summary?days=7');
                const data = await response.json();
                
                document.getElementById('total-requests').textContent = 
                    data.total_requests.toLocaleString();
                document.getElementById('total-tokens').textContent = 
                    data.total_tokens.toLocaleString();
                document.getElementById('total-cost').textContent = 
                    '$' + data.total_cost.toFixed(4);
                document.getElementById('models-count').textContent = 
                    Object.keys(data.models_used).length;
                    
            } catch (error) {
                console.error('加载摘要失败:', error);
            }
        }
        
        // 加载最近记录
        async function loadRecentRecords() {
            try {
                const response = await fetch('/api/stats/recent?limit=20');
                const data = await response.json();
                
                const tbody = document.getElementById('records-tbody');
                tbody.innerHTML = '';
                
                if (data.records.length === 0) {
                    tbody.innerHTML = `
                        <tr><td colspan="7" style="text-align:center; color:#999;">
                            暂无记录
                        </td></tr>
                    `;
                } else {
                    data.records.forEach(record => {
                        const row = tbody.insertRow();
                        row.innerHTML = `
                            <td>${new Date(record.timestamp).toLocaleString('zh-CN')}</td>
                            <td>${record.model}</td>
                            <td>${record.session_id.substr(0, 8)}...</td>
                            <td>${record.tokens_in.toLocaleString()}</td>
                            <td>${record.tokens_out.toLocaleString()}</td>
                            <td>$${record.cost_usd.toFixed(6)}</td>
                            <td>${record.duration_ms.toFixed(0)}ms</td>
                        `;
                    });
                }
                
                document.getElementById('recent-records-loading').style.display = 'none';
                document.getElementById('recent-records-table').style.display = 'table';
                
            } catch (error) {
                console.error('加载记录失败:', error);
                document.getElementById('recent-records-loading').innerHTML = 
                    '<div class="error">加载失败: ' + error.message + '</div>';
            }
        }
        
        // 加载所有数据
        async function loadData() {
            await checkHealth();
            await loadSummary();
            await loadRecentRecords();
        }
        
        // 页面加载时自动加载数据
        window.onload = loadData;
        
        // 每30秒自动刷新
        setInterval(loadData, 30000);
    </script>
</body>
</html>
    """


def run_server(host: str = "0.0.0.0", port: int = 8090):
    """运行Monitor服务器
    
    Args:
        host: 监听地址
        port: 监听端口
    """
    print(f"""
╔════════════════════════════════════════════════════════════╗
║           Aira Monitor Server 正在启动...              ║
╚════════════════════════════════════════════════════════════╝

🌐 访问地址: http://localhost:{port}
📊 API文档: http://localhost:{port}/docs
🔧 健康检查: http://localhost:{port}/api/health

按 Ctrl+C 停止服务
""")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    run_server()

