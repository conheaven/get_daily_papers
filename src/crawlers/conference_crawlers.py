from typing import List, Dict, Optional
from .base import BaseCrawler
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class NDSSCrawler(BaseCrawler):
    """NDSS会议专用爬虫"""

    def crawl(self, year: int) -> List[Dict]:
        """爬取NDSS论文"""
        papers = []

        # NDSS官网URL
        url = f"https://www.ndss-symposium.org/ndss{year}/accepted-papers/"

        try:
            html = self.fetch_page(url)
            soup = self.parse_html(html)

            # 根据NDSS网站结构解析
            # 注意：实际结构可能需要根据网站调整
            paper_items = soup.find_all("div", class_="paper")

            for item in paper_items:
                paper = self._parse_paper(item, year)
                if paper:
                    papers.append(paper)

            logger.info(f"从NDSS官网爬取到 {len(papers)} 篇论文 ({year})")

        except Exception as e:
            logger.error(f"NDSS爬取失败: {e}")

        return papers

    def _parse_paper(self, item, year: int) -> Optional[Dict]:
        """解析论文条目"""
        try:
            title = item.find("h4")
            if title:
                title = title.get_text(strip=True)

            authors = item.find("p", class_="authors")
            if authors:
                authors = authors.get_text(strip=True)

            # 查找PDF链接
            pdf_link = item.find("a", href=lambda x: x and ".pdf" in x)
            pdf_url = pdf_link.get("href") if pdf_link else None

            if title:
                return {
                    "title": title,
                    "authors": authors,
                    "conference": "NDSS",
                    "year": year,
                    "abstract": None,
                    "pdf_url": pdf_url,
                    "paper_url": None,
                    "doi": None,
                }
        except Exception as e:
            logger.warning(f"解析NDSS论文失败: {e}")

        return None


class USENIXSecurityCrawler(BaseCrawler):
    """USENIX Security会议专用爬虫"""

    def crawl(self, year: int) -> List[Dict]:
        """爬取USENIX Security论文"""
        papers = []

        # USENIX官网URL
        url = f"https://www.usenix.org/conference/usenixsecurity{year % 100}/technical-sessions"

        try:
            html = self.fetch_page(url)
            soup = self.parse_html(html)

            # 查找所有论文条目
            paper_items = soup.find_all("div", class_="views-row")

            for item in paper_items:
                paper = self._parse_paper(item, year)
                if paper:
                    papers.append(paper)

            logger.info(f"从USENIX官网爬取到 {len(papers)} 篇论文 ({year})")

        except Exception as e:
            logger.error(f"USENIX Security爬取失败: {e}")

        return papers

    def _parse_paper(self, item, year: int) -> Optional[Dict]:
        """解析论文条目"""
        try:
            # 标题
            title_tag = item.find("h4") or item.find("h3")
            title = title_tag.get_text(strip=True) if title_tag else None

            # 作者
            authors_tag = item.find("div", class_="field-name-field-person-public-name")
            authors = authors_tag.get_text(strip=True) if authors_tag else None

            # 摘要
            abstract_tag = item.find("div", class_="field-name-body")
            abstract = abstract_tag.get_text(strip=True) if abstract_tag else None

            # PDF链接
            pdf_link = item.find(
                "a", href=lambda x: x and "presentation" in str(x).lower()
            )
            paper_url = None
            if pdf_link and pdf_link.get("href"):
                paper_url = "https://www.usenix.org" + pdf_link.get("href")

            if title:
                return {
                    "title": title,
                    "authors": authors,
                    "conference": "USENIX Security",
                    "year": year,
                    "abstract": abstract,
                    "pdf_url": None,
                    "paper_url": paper_url,
                    "doi": None,
                }
        except Exception as e:
            logger.warning(f"解析USENIX论文失败: {e}")

        return None


class CCSCrawler(BaseCrawler):
    """ACM CCS会议专用爬虫"""

    def crawl(self, year: int) -> List[Dict]:
        """爬取CCS论文"""
        papers = []

        # CCS使用ACM Digital Library
        # 注意：可能需要特殊处理或API
        logger.info(f"CCS {year} 建议使用DBLP爬虫")

        return papers


class SPCrawler(BaseCrawler):
    """IEEE S&P (Oakland) 会议专用爬虫"""

    def crawl(self, year: int) -> List[Dict]:
        """爬取S&P论文"""
        papers = []

        # S&P官网URL
        url = f"https://www.ieee-security.org/TC/SP{year}/program-papers.html"

        try:
            html = self.fetch_page(url)
            soup = self.parse_html(html)

            # 查找论文列表
            paper_items = soup.find_all("div", class_="paper")

            for item in paper_items:
                paper = self._parse_paper(item, year)
                if paper:
                    papers.append(paper)

            logger.info(f"从S&P官网爬取到 {len(papers)} 篇论文 ({year})")

        except Exception as e:
            logger.error(f"S&P爬取失败: {e}")

        return papers

    def _parse_paper(self, item, year: int) -> Optional[Dict]:
        """解析论文条目"""
        try:
            # 标题
            title_tag = item.find("span", class_="title")
            title = title_tag.get_text(strip=True) if title_tag else None

            # 作者
            authors_tag = item.find("span", class_="authors")
            authors = authors_tag.get_text(strip=True) if authors_tag else None

            # PDF链接
            pdf_link = item.find("a", href=lambda x: x and ".pdf" in x)
            pdf_url = pdf_link.get("href") if pdf_link else None

            if title:
                return {
                    "title": title,
                    "authors": authors,
                    "conference": "S&P",
                    "year": year,
                    "abstract": None,
                    "pdf_url": pdf_url,
                    "paper_url": None,
                    "doi": None,
                }
        except Exception as e:
            logger.warning(f"解析S&P论文失败: {e}")

        return None
