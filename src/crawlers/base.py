from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import time
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """爬虫基类"""

    def __init__(self, conference_name: str, config: Optional[Dict] = None):
        self.conference_name = conference_name
        self.config = config or {}
        self.timeout = self.config.get("request_timeout", 30)
        self.retry_times = self.config.get("retry_times", 3)
        self.delay = self.config.get("delay_between_requests", 1)

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    @abstractmethod
    def crawl(self, year: int) -> List[Dict]:
        """爬取指定年份的论文"""
        pass

    def fetch_page(self, url: str) -> str:
        """获取网页内容，带重试机制"""
        for attempt in range(self.retry_times):
            try:
                logger.info(f"正在访问: {url} (尝试 {attempt + 1}/{self.retry_times})")
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                time.sleep(self.delay)
                return response.text
            except requests.RequestException as e:
                logger.warning(f"请求失败: {e}")
                if attempt < self.retry_times - 1:
                    time.sleep(2**attempt)  # 指数退避
                else:
                    logger.error(f"多次尝试后仍失败: {url}")
                    raise
        return ""

    def parse_html(self, html: str) -> BeautifulSoup:
        """解析HTML"""
        return BeautifulSoup(html, "lxml")


class DBLPCrawler(BaseCrawler):
    """DBLP爬虫 - 通用解决方案"""

    CONFERENCE_MAPPING = {
        "NDSS": "ndss",
        "USENIX Security": "uss",
        "CCS": "ccs",
        "S&P": "sp",
    }

    def __init__(self, conference_name: str, config: Optional[Dict] = None):
        super().__init__(conference_name, config)
        self.dblp_key = self.CONFERENCE_MAPPING.get(
            conference_name, conference_name.lower()
        )

    def crawl(self, year: int) -> List[Dict]:
        """从DBLP爬取论文"""
        papers = []

        # 根据会议构建DBLP URL
        if self.conference_name == "NDSS":
            url = f"https://dblp.org/db/conf/ndss/ndss{year}.html"
        elif self.conference_name == "USENIX Security":
            url = f"https://dblp.org/db/conf/uss/uss{year}.html"
        elif self.conference_name == "CCS":
            url = f"https://dblp.org/db/conf/ccs/ccs{year}.html"
        elif self.conference_name == "S&P":
            url = f"https://dblp.org/db/conf/sp/sp{year}.html"
        else:
            logger.error(f"不支持的会议: {self.conference_name}")
            return papers

        try:
            html = self.fetch_page(url)
            soup = self.parse_html(html)

            # 查找所有论文条目
            entries = soup.find_all("li", class_="entry")

            for entry in entries:
                paper = self._parse_entry(entry, year)
                if paper:
                    papers.append(paper)

            logger.info(
                f"从DBLP爬取到 {len(papers)} 篇论文 ({self.conference_name} {year})"
            )

        except Exception as e:
            logger.error(f"DBLP爬取失败: {e}")

        return papers

    def _parse_entry(self, entry, year: int) -> Optional[Dict]:
        """解析单个论文条目"""
        try:
            # 标题
            title_tag = entry.find("span", class_="title")
            title = title_tag.get_text(strip=True) if title_tag else None

            if not title:
                return None

            # 作者
            authors = []
            author_tags = entry.find_all("span", itemprop="author")
            for author_tag in author_tags:
                author_name = author_tag.find("span", itemprop="name")
                if author_name:
                    authors.append(author_name.get_text(strip=True))

            # PDF链接
            pdf_url = None
            ee_tags = entry.find_all("a", class_="ee")
            for ee_tag in ee_tags:
                href = ee_tag.get("href", "")
                if ".pdf" in href:
                    pdf_url = href
                    break

            # 论文页面链接
            paper_url = None
            if ee_tags:
                paper_url = ee_tags[0].get("href")

            # DOI
            doi = None
            doi_tag = entry.find("a", href=lambda x: x and "doi.org" in x)
            if doi_tag:
                doi = doi_tag.get("href")

            return {
                "title": title,
                "authors": ", ".join(authors),
                "conference": self.conference_name,
                "year": year,
                "abstract": None,  # DBLP不提供摘要
                "pdf_url": pdf_url,
                "paper_url": paper_url,
                "doi": doi,
            }

        except Exception as e:
            logger.warning(f"解析论文条目失败: {e}")
            return None
