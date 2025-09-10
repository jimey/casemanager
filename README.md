# 患者病例管理系统（Flask + SQLite）

一个基于 Flask 的简易 B/S 架构患者病例管理系统。功能包括：
- 患者基本信息管理（新增/列表/编辑/删除）
- 就诊记录管理（按患者新增/编辑/删除）
- 关键字搜索（姓名/电话/证件号）

## 运行环境
- Python 3.8+
- Flask（无需数据库 ORM，使用标准库 sqlite3）

## 快速开始

1. 创建虚拟环境并安装 Flask
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install Flask
   ```

2. 启动应用
   ```bash
   python app.py
   ```
   访问 http://127.0.0.1:5000

首次访问会自动在 `data/app.db` 初始化数据库（SQLite）。

## 项目结构
```
app.py                 # Flask 入口与路由
db.py                  # 数据库连接与初始化（sqlite3）
templates/             # Jinja2 模板
  base.html
  patients/
    index.html         # 患者列表 + 搜索
    new_edit.html      # 患者新增/编辑表单
    detail.html        # 患者详情 + 就诊列表
  visits/
    new_edit.html      # 就诊新增/编辑表单
static/
  style.css            # 简易样式
README.md
```

## 说明
- 数据库存储于 `data/app.db`，已开启外键约束，删除患者将级联删除其就诊记录。
- 表单为原生 HTML，做了最小化校验（例如姓名必填、日期格式）。
- 若需部署生产环境，请配置：
  - 设置环境变量 `SECRET_KEY`（用于 Flash/会话安全）
  - 使用生产 WSGI（如 gunicorn/uwsgi）和反向代理
  - 增强表单校验、权限控制与审计日志

## 可拓展方向
- 用户认证与权限（医生/管理员）
- 更多字段与上传（检查影像/报告）
- 导出为 PDF/Excel
- 高级搜索与分页
- 基于 SQLAlchemy 迁移到 ORM

