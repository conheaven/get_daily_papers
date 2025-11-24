from flask import Flask, render_template, request, jsonify, redirect, url_for
import yaml
import logging
from typing import Dict, List, Optional
from src.models.database import DatabaseManager
from main import CrawlerManager
import os

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

# 加载配置
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

db = DatabaseManager(config["database"]["path"])
crawler_manager = CrawlerManager("config.yaml")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/")
def index():
    """首页 - 论文列表"""
    # 获取查询参数
    page = request.args.get("page", 1, type=int)
    conference = request.args.get("conference", "")
    year = request.args.get("year", "", type=str)
    search = request.args.get("search", "")
    per_page = config["web"]["per_page"]

    # 构建查询条件
    query = "SELECT * FROM papers WHERE 1=1"
    params = []

    if conference:
        query += " AND conference = ?"
        params.append(conference)

    if year:
        query += " AND year = ?"
        params.append(int(year))

    if search:
        query += " AND (title LIKE ? OR authors LIKE ?)"
        search_term = f"%{search}%"
        params.append(search_term)
        params.append(search_term)

    query += " ORDER BY year DESC, created_at DESC"

    # 获取总数
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    import sqlite3

    conn = sqlite3.connect(config["database"]["path"])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    # 分页
    offset = (page - 1) * per_page
    query += f" LIMIT {per_page} OFFSET {offset}"

    cursor.execute(query, params)
    papers = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # 计算总页数
    total_pages = (total + per_page - 1) // per_page

    # 获取统计信息
    stats = db.get_statistics()

    # 获取所有会议列表
    conferences = sorted(list(stats["by_conference"].keys()))

    # 获取所有年份
    cursor = sqlite3.connect(config["database"]["path"]).cursor()
    cursor.execute("SELECT DISTINCT year FROM papers ORDER BY year DESC")
    years = [row[0] for row in cursor.fetchall()]
    cursor.connection.close()

    return render_template(
        "index.html",
        papers=papers,
        page=page,
        total_pages=total_pages,
        total=total,
        conference=conference,
        year=year,
        search=search,
        conferences=conferences,
        years=years,
        stats=stats,
    )


@app.route("/paper/<int:paper_id>")
def paper_detail(paper_id):
    """论文详情页"""
    import sqlite3

    conn = sqlite3.connect(config["database"]["path"])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
    paper = cursor.fetchone()
    conn.close()

    if paper:
        paper = dict(paper)
        return render_template("detail.html", paper=paper)
    else:
        return "论文不存在", 404


@app.route("/statistics")
def statistics():
    """统计信息页"""
    stats = db.get_statistics()

    # 获取爬取历史
    import sqlite3

    conn = sqlite3.connect(config["database"]["path"])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT conference, year, papers_count, status, created_at
        FROM crawl_history
        ORDER BY created_at DESC
        LIMIT 50
    """
    )
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return render_template("statistics.html", stats=stats, history=history)


@app.route("/crawl", methods=["GET", "POST"])
def crawl():
    """爬取管理页"""
    if request.method == "POST":
        # 处理爬取请求
        conference = request.form.get("conference")
        year = request.form.get("year", type=int)

        if conference and year:
            try:
                crawler_manager.crawl_conference(conference, year)
                return jsonify(
                    {"success": True, "message": f"成功爬取 {conference} {year}"}
                )
            except Exception as e:
                logger.error(f"爬取失败: {e}")
                return jsonify({"success": False, "message": str(e)})
        else:
            return jsonify({"success": False, "message": "参数错误"})

    # GET请求，显示爬取页面
    conferences_config = config.get("conferences", [])
    return render_template("crawl.html", conferences=conferences_config)


@app.route("/api/crawl_all", methods=["POST"])
def crawl_all():
    """爬取所有启用的会议"""
    try:
        crawler_manager.crawl_all()
        return jsonify({"success": True, "message": "批量爬取完成"})
    except Exception as e:
        logger.error(f"批量爬取失败: {e}")
        return jsonify({"success": False, "message": str(e)})


@app.route("/config")
def show_config():
    """配置管理页"""
    return render_template("config.html", config=config)


@app.route("/api/papers")
def api_papers():
    """API: 获取论文列表"""
    conference = request.args.get("conference")
    year = request.args.get("year", type=int)
    limit = request.args.get("limit", 20, type=int)

    papers = db.get_papers(conference=conference, year=year, limit=limit)
    return jsonify(papers)


@app.route("/api/stats")
def api_stats():
    """API: 获取统计信息"""
    stats = db.get_statistics()
    return jsonify(stats)


def main():
    """启动Web服务"""
    host = config["web"]["host"]
    port = config["web"]["port"]
    debug = config["web"]["debug"]

    print(
        f"""
╔══════════════════════════════════════════════════════╗
║     论文爬取工具 - Web界面                            ║
╚══════════════════════════════════════════════════════╝

🌐 访问地址: http://{host}:{port}
📊 论文总数: {db.get_statistics()['total_papers']}
🔧 调试模式: {'开启' if debug else '关闭'}

按 Ctrl+C 停止服务器
    """
    )

    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
