import sqlite3
from datetime import datetime
from typing import List, Optional, Dict
import os


class DatabaseManager:
    """数据库管理类"""

    def __init__(self, db_path: str = "./data/papers.db"):
        self.db_path = db_path
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()

    def init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建论文表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                conference TEXT NOT NULL,
                year INTEGER NOT NULL,
                abstract TEXT,
                pdf_url TEXT,
                paper_url TEXT,
                doi TEXT,
                downloaded BOOLEAN DEFAULT 0,
                local_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(title, conference, year)
            )
        """
        )

        # 创建爬取记录表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS crawl_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conference TEXT NOT NULL,
                year INTEGER NOT NULL,
                papers_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 创建索引
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conference_year 
            ON papers(conference, year)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON papers(created_at)
        """
        )

        conn.commit()
        conn.close()

    def insert_paper(self, paper_data: Dict) -> bool:
        """插入或更新论文数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO papers (
                    title, authors, conference, year, abstract, 
                    pdf_url, paper_url, doi, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(title, conference, year) 
                DO UPDATE SET
                    authors = excluded.authors,
                    abstract = excluded.abstract,
                    pdf_url = excluded.pdf_url,
                    paper_url = excluded.paper_url,
                    doi = excluded.doi,
                    updated_at = excluded.updated_at
            """,
                (
                    paper_data.get("title"),
                    paper_data.get("authors"),
                    paper_data.get("conference"),
                    paper_data.get("year"),
                    paper_data.get("abstract"),
                    paper_data.get("pdf_url"),
                    paper_data.get("paper_url"),
                    paper_data.get("doi"),
                    datetime.now(),
                ),
            )

            conn.commit()
            return True
        except Exception as e:
            print(f"插入论文失败: {e}")
            return False
        finally:
            conn.close()

    def insert_papers_batch(self, papers: List[Dict]) -> int:
        """批量插入论文"""
        success_count = 0
        for paper in papers:
            if self.insert_paper(paper):
                success_count += 1
        return success_count

    def get_papers(
        self,
        conference: Optional[str] = None,
        year: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """查询论文"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM papers WHERE 1=1"
        params = []

        if conference:
            query += " AND conference = ?"
            params.append(conference)

        if year:
            query += " AND year = ?"
            params.append(year)

        query += " ORDER BY created_at DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def paper_exists(self, title: str, conference: str, year: int) -> bool:
        """检查论文是否已存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) FROM papers 
            WHERE title = ? AND conference = ? AND year = ?
        """,
            (title, conference, year),
        )

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    def log_crawl_history(
        self,
        conference: str,
        year: int,
        papers_count: int,
        status: str = "success",
        error_message: Optional[str] = None,
    ):
        """记录爬取历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO crawl_history (conference, year, papers_count, status, error_message)
            VALUES (?, ?, ?, ?, ?)
        """,
            (conference, year, papers_count, status, error_message),
        )

        conn.commit()
        conn.close()

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 总论文数
        cursor.execute("SELECT COUNT(*) FROM papers")
        total_papers = cursor.fetchone()[0]

        # 各会议论文数
        cursor.execute(
            """
            SELECT conference, COUNT(*) as count 
            FROM papers 
            GROUP BY conference
        """
        )
        by_conference = dict(cursor.fetchall())

        # 最近更新时间
        cursor.execute("SELECT MAX(created_at) FROM papers")
        last_update = cursor.fetchone()[0]

        conn.close()

        return {
            "total_papers": total_papers,
            "by_conference": by_conference,
            "last_update": last_update,
        }
