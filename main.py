import yaml
import logging
from typing import Dict, List
from src.crawlers.base import DBLPCrawler
from src.crawlers.conference_crawlers import (
    NDSSCrawler,
    USENIXSecurityCrawler,
    CCSCrawler,
    SPCrawler,
)
from src.models.database import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/crawler.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class CrawlerManager:
    """爬虫管理器"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self.load_config(config_path)
        self.db = DatabaseManager(self.config["database"]["path"])
        self.crawler_config = self.config["crawler"]

        # 注册爬虫
        self.crawlers = {
            "NDSS": [
                DBLPCrawler("NDSS", self.crawler_config),
                NDSSCrawler("NDSS", self.crawler_config),
            ],
            "USENIX Security": [
                DBLPCrawler("USENIX Security", self.crawler_config),
                USENIXSecurityCrawler("USENIX Security", self.crawler_config),
            ],
            "CCS": [DBLPCrawler("CCS", self.crawler_config)],
            "S&P": [
                DBLPCrawler("S&P", self.crawler_config),
                SPCrawler("S&P", self.crawler_config),
            ],
        }

    def load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"配置文件未找到: {config_path}")
            raise

    def crawl_conference(self, conference_name: str, year: int):
        """爬取指定会议的论文"""
        logger.info(f"开始爬取 {conference_name} {year}")

        all_papers = []
        crawlers = self.crawlers.get(conference_name, [])

        for crawler in crawlers:
            try:
                papers = crawler.crawl(year)
                all_papers.extend(papers)
            except Exception as e:
                logger.error(f"{crawler.__class__.__name__} 爬取失败: {e}")

        # 去重
        unique_papers = self._deduplicate_papers(all_papers)

        # 保存到数据库
        if unique_papers:
            saved_count = self.db.insert_papers_batch(unique_papers)
            logger.info(f"成功保存 {saved_count}/{len(unique_papers)} 篇论文")

            # 记录爬取历史
            self.db.log_crawl_history(conference_name, year, saved_count)
        else:
            logger.warning(f"未爬取到任何论文: {conference_name} {year}")
            self.db.log_crawl_history(conference_name, year, 0, "empty")

    def _deduplicate_papers(self, papers: List[Dict]) -> List[Dict]:
        """去重论文列表"""
        seen = set()
        unique = []

        for paper in papers:
            key = (paper["title"], paper["conference"], paper["year"])
            if key not in seen:
                seen.add(key)
                unique.append(paper)

        return unique

    def crawl_all(self):
        """爬取所有配置的会议"""
        conferences = self.config.get("conferences", [])

        for conf in conferences:
            if not conf.get("enabled", True):
                continue

            name = conf["name"]
            years = conf.get("years", [])

            for year in years:
                try:
                    self.crawl_conference(name, year)
                except Exception as e:
                    logger.error(f"爬取失败 {name} {year}: {e}")

    def show_statistics(self):
        """显示统计信息"""
        stats = self.db.get_statistics()

        print("\n" + "=" * 50)
        print("论文数据库统计")
        print("=" * 50)
        print(f"总论文数: {stats['total_papers']}")
        print(f"\n各会议论文数:")
        for conf, count in stats["by_conference"].items():
            print(f"  {conf}: {count}")
        print(f"\n最后更新: {stats['last_update']}")
        print("=" * 50 + "\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="顶级安全会议论文爬取工具")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--conference", help="指定会议名称")
    parser.add_argument("--year", type=int, help="指定年份")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")

    args = parser.parse_args()

    manager = CrawlerManager(args.config)

    if args.stats:
        manager.show_statistics()
    elif args.conference and args.year:
        manager.crawl_conference(args.conference, args.year)
    else:
        manager.crawl_all()
        manager.show_statistics()


if __name__ == "__main__":
    main()
