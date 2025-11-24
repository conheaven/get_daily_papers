# 📚 顶级安全会议论文爬取工具

自动爬取NDSS、USENIX Security、CCS、S&P等顶级安全会议的论文信息，提供Web界面查看和管理。

## ✨ 功能特性

- ✅ 支持多个顶级安全会议（NDSS, USENIX Security, CCS, S&P等）
- ✅ 多数据源爬取（DBLP + 会议官网）
- ✅ **Web界面查看论文**（搜索、筛选、分页）
- ✅ SQLite本地数据库存储
- ✅ 增量更新，自动去重
- ✅ 灵活配置，易于扩展新会议
- ✅ 完整的日志记录
- ✅ 统计信息可视化

## 📁 项目结构

```
get_paper/
├── config.yaml              # 配置文件
├── requirements.txt         # 依赖包
├── database.py             # 数据库管理
├── main.py                 # 命令行主程序
├── app.py                  # Web应用（推荐使用）
├── crawlers/               # 爬虫模块
│   ├── __init__.py
│   ├── base.py            # 基础爬虫类（含DBLP爬虫）
│   └── conference_crawlers.py  # 各会议专用爬虫
├── templates/              # Web界面模板
│   ├── index.html         # 首页（论文列表）
│   ├── detail.html        # 论文详情
│   ├── crawl.html         # 爬取管理
│   ├── statistics.html    # 统计信息
│   └── config.html        # 配置查看
├── papers.db              # 论文数据库（自动生成）
└── crawler.log            # 爬取日志
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

## 📊 数据查询

### 方法1：Web界面（推荐）

访问 `http://127.0.0.1:5000` 查看所有论文

### 方法2：Python脚本

```python
from database import DatabaseManager

db = DatabaseManager()

# 查询NDSS 2024的所有论文
papers = db.get_papers(conference='NDSS', year=2024)
for paper in papers:
    print(f"{paper['title']} - {paper['authors']}")

# 查询最近10篇论文
recent = db.get_papers(limit=10)

# 获取统计信息
stats = db.get_statistics()
print(f"总论文数: {stats['total_papers']}")
```

### 方法3：SQLite命令行

```bash
sqlite3 papers.db
```

```sql
-- 查询所有论文
SELECT * FROM papers;

-- 按会议统计
SELECT conference, COUNT(*) as count 
FROM papers 
GROUP BY conference 
ORDER BY count DESC;

-- 查询2024年的所有论文
SELECT title, conference, authors 
FROM papers 
WHERE year = 2024 
ORDER BY created_at DESC;
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

## 🔧 如何添加新会议/期刊

### 方法1：使用DBLP（推荐，最简单）

DBLP已支持大部分计算机科学会议，只需在 `config.yaml` 中添加：

```yaml
conferences:
  - name: 新会议名称        # 例如: CRYPTO, EUROCRYPT
    enabled: true
    years: [2023, 2024]
    description: "会议完整名称"
```

DBLP会自动处理，无需编写代码！

### 方法2：实现专用爬虫（高级）

如果需要从会议官网获取更多信息（如摘要），可以实现专用爬虫：

1. 在 `crawlers/conference_crawlers.py` 中添加：

```python
class NewConferenceCrawler(BaseCrawler):
    def crawl(self, year: int) -> List[Dict]:
        url = f"https://example.com/conference{year}"
        html = self.fetch_page(url)
        soup = self.parse_html(html)
        
        # 解析网页并返回论文列表
        papers = []
        # ... 实现解析逻辑 ...
        return papers
```

2. 在 `main.py` 的 `CrawlerManager.__init__` 中注册：

```python
self.crawlers = {
    'NewConference': [
        DBLPCrawler('NewConference', self.crawler_config),
        NewConferenceCrawler('NewConference', self.crawler_config)
    ]
}
```

3. 在 `config.yaml` 中启用：

```yaml
conferences:
  - name: NewConference
    enabled: true
    years: [2024]
```

**提示**：系统会自动合并多个数据源的结果并去重。

## ⚠️ 注意事项

1. **遵守爬虫规则** - 请合理设置请求间隔（默认1秒），避免对目标网站造成压力
2. **网站结构变化** - 会议官网结构可能会变化，DBLP相对稳定
3. **数据准确性** - DBLP作为主要数据源，官网作为补充
4. **首次爬取** - 建议先爬取最近1-2年的数据测试

## 💡 常见问题

### Q: 爬取失败怎么办？

**A**: 查看 `crawler.log` 日志文件，常见原因：
- 网络连接问题 → 检查网络
- 会议网站变化 → 使用DBLP数据源（更稳定）
- URL失效 → 更新爬虫代码

### Q: 如何更新已有论文？

**A**: 重新爬取同一会议和年份，数据库会自动更新（基于标题+会议+年份去重）

### Q: 可以爬取历史年份吗？

**A**: 可以！在 `config.yaml` 中的 `years` 数组添加任意年份即可

### Q: 支持哪些会议？

**A**: 
- **已配置**: NDSS, USENIX Security, CCS, S&P, CRYPTO, EUROCRYPT等
- **可添加**: 任何在DBLP收录的计算机科学会议
- **自定义**: 实现专用爬虫支持任何会议官网

### Q: Web界面无法访问？

**A**: 
1. 确保运行了 `python app.py`
2. 检查端口5000是否被占用
3. 尝试访问 `http://localhost:5000`

## 📦 依赖说明

- `requests` - HTTP请求
- `beautifulsoup4` - HTML解析
- `lxml` - 高性能HTML/XML解析器
- `flask` - Web框架
- `pyyaml` - 配置文件解析
- `python-dateutil` - 日期处理

## 🎯 技术架构

```
用户界面层: Flask Web应用 (app.py)
    ↓
业务逻辑层: 爬虫管理器 (main.py)
    ↓
数据访问层: 数据库管理 (database.py)
    ↓
爬虫引擎层: 基类 + 具体实现 (crawlers/)
    ↓
数据源: DBLP + 会议官网
```

## 📸 功能预览

启动后访问Web界面，你将看到：
- 📄 **论文列表** - 清晰的列表展示，支持搜索和筛选
- 🔍 **论文详情** - 完整的论文信息和链接
- 📊 **统计图表** - 数据可视化展示
- ⚙️ **爬取管理** - 一键爬取任意会议

## 🤝 贡献

欢迎提交Issue和Pull Request！

如果这个项目对你有帮助，请给个⭐️

## 📄 许可证

MIT License

## 📝 更新日志

### v2.0.0 (2025-11-24)
- ✨ 新增Web界面，支持在线查看和管理
- 🎨 美化UI设计，提升用户体验
- 🔧 移除定时任务，改为手动触发
- 📚 优化配置文件，更易扩展新会议
- 🐛 修复多处bug，提升稳定性

### v1.0.0 (2025-11-24)
- 🎉 初始版本
- 支持NDSS, USENIX Security, CCS, S&P
- 实现DBLP和官网双数据源
- 命令行界面

---

**Made with ❤️ for Security Researchers**
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
