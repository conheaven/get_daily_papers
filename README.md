# 顶级安全会议论文爬取工具

自动爬取 NDSS、USENIX Security、CCS、S&P 等顶级安全会议的论文信息，支持定时任务和增量更新。

## 功能特性

- ✅ 支持多个顶级安全会议（NDSS, USENIX Security, CCS, S&P）
- ✅ 多数据源爬取（DBLP + 会议官网）
- ✅ SQLite 本地数据库存储
- ✅ 增量更新，避免重复爬取
- ✅ 定时任务自动执行
- ✅ 灵活的配置文件
- ✅ 完整的日志记录
- ✅ 统计信息查看

## 项目结构

```
get_paper/
├── config.yaml              # 配置文件
├── requirements.txt         # 依赖包
├── database.py             # 数据库管理
├── main.py                 # 主程序
├── scheduler.py            # 定时调度器
├── crawlers/               # 爬虫模块
│   ├── __init__.py
│   ├── base.py            # 基础爬虫类
│   └── conference_crawlers.py  # 各会议专用爬虫
├── papers.db              # 论文数据库（自动生成）
├── crawler.log            # 爬取日志
└── scheduler.log          # 调度器日志
```

## 安装

### 1. 克隆或下载项目

```bash
cd get_paper
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

编辑 `config.yaml` 文件：

```yaml
conferences:
  - name: NDSS
    enabled: true
    years: [2024, 2025]

  - name: USENIX Security
    enabled: true
    years: [2024, 2025]

crawler:
  download_pdf: false # 是否下载PDF
  pdf_directory: ./papers # PDF保存目录
  request_timeout: 30 # 请求超时（秒）
  retry_times: 3 # 重试次数
  delay_between_requests: 1 # 请求间隔（秒）

schedule:
  enabled: true # 是否启用定时任务
  time: "09:00" # 每天执行时间
```

## 使用方法

### 1. 一次性爬取所有配置的会议

```bash
python main.py
```

### 2. 爬取指定会议和年份

```bash
python main.py --conference "NDSS" --year 2024
```

### 3. 查看统计信息

```bash
python main.py --stats
```

### 4. 启动定时调度器

```bash
python scheduler.py
```

调度器会：

- 首次启动时立即执行一次爬取
- 之后每天在配置的时间自动执行
- 按 `Ctrl+C` 可停止调度器

## 数据查询

使用 Python 脚本查询数据库：

```python
from database import DatabaseManager

db = DatabaseManager()

# 查询所有NDSS 2024论文
papers = db.get_papers(conference='NDSS', year=2024)

# 查询最近10篇论文
recent = db.get_papers(limit=10)

# 获取统计信息
stats = db.get_statistics()
print(stats)
```

使用 SQLite 客户端：

```bash
sqlite3 papers.db
```

```sql
-- 查询所有论文
SELECT * FROM papers;

-- 按会议统计
SELECT conference, COUNT(*) FROM papers GROUP BY conference;

-- 查询最近添加的论文
SELECT title, conference, year FROM papers
ORDER BY created_at DESC LIMIT 10;
```

## 数据库结构

### papers 表

| 字段       | 类型      | 说明           |
| ---------- | --------- | -------------- |
| id         | INTEGER   | 主键           |
| title      | TEXT      | 论文标题       |
| authors    | TEXT      | 作者列表       |
| conference | TEXT      | 会议名称       |
| year       | INTEGER   | 年份           |
| abstract   | TEXT      | 摘要           |
| pdf_url    | TEXT      | PDF 链接       |
| paper_url  | TEXT      | 论文页面链接   |
| doi        | TEXT      | DOI            |
| downloaded | BOOLEAN   | 是否已下载 PDF |
| local_path | TEXT      | 本地路径       |
| created_at | TIMESTAMP | 创建时间       |
| updated_at | TIMESTAMP | 更新时间       |

### crawl_history 表

记录每次爬取的历史信息。

## 扩展新会议

1. 在 `crawlers/conference_crawlers.py` 中创建新的爬虫类：

```python
class NewConferenceCrawler(BaseCrawler):
    def crawl(self, year: int) -> List[Dict]:
        # 实现爬取逻辑
        pass
```

2. 在 `main.py` 的 `CrawlerManager.__init__` 中注册：

```python
self.crawlers = {
    'NewConference': [NewConferenceCrawler('NewConference', self.crawler_config)]
}
```

3. 在 `config.yaml` 中添加配置：

```yaml
conferences:
  - name: NewConference
    enabled: true
    years: [2024]
```

## 注意事项

1. **遵守爬虫规则**：请合理设置请求间隔，避免对目标网站造成压力
2. **网站结构变化**：会议官网结构可能会变化，需要相应更新爬虫代码
3. **数据准确性**：建议使用 DBLP 作为主要数据源，官网作为补充
4. **PDF 下载**：默认不下载 PDF，如需下载请修改配置并确保有足够存储空间

## 常见问题

### Q: 爬取失败怎么办？

A: 检查日志文件 `crawler.log`，可能原因：

- 网络连接问题
- 会议网站结构变化
- URL 失效

### Q: 如何更新已有论文的信息？

A: 重新运行爬虫，数据库会自动更新（基于标题+会议+年份去重）

### Q: 可以爬取历史年份的论文吗？

A: 可以，在配置文件中添加历史年份即可

## 依赖说明

- `requests`: HTTP 请求
- `beautifulsoup4`: HTML 解析
- `lxml`: 更快的 HTML 解析器
- `schedule`: 定时任务
- `pyyaml`: 配置文件解析
- `tqdm`: 进度条（可选）

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0 (2025-11-24)

- 初始版本
- 支持 NDSS, USENIX Security, CCS, S&P
- 实现 DBLP 和官网双数据源
- 添加定时任务功能
