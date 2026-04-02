# 财务系统

简洁的个人/企业财务收支管理系统，支持多账户、多分类、报表生成与 PDF 导出。

## 默认账户

- **用户名**：`admin`
- **密码**：`admin123`
- **地址**：`http://43.134.137.240/finapp`

> 首次登录后请修改密码。

## 主要功能

### 交易录入
- 支出/收入分类，两级联动（大类 → 明细）
- 支持账户选择、备注、批量导入

### 报表系统
- **日报表**：每日收支明细 + 汇总
- **月报表**：按日汇总 + 月度总计
- **年度报表**：按月汇总 + 年度总计
- **图表分析**：月度对比、统计摘要
- 所有报表均支持 **PDF 导出**（中文正常显示）

### 账户管理
- 多账户支持（银行、证券、微信、支付宝等）
- 账户余额自动计算
- 密码修改（登录页 / 用户管理页均可）

### 数据安全
- 登录认证（Flask-Login）
- 支持"记住我"（一天内免登录）
- 数据存储在本地 SQLite，无需联网

## 快速部署

```bash
# 安装依赖
pip install flask flask-sqlalchemy flask-login werkzeug reportlab fpdf2

# 启动（默认端口 5000，访问 /finapp）
python app.py
```

访问 `http://localhost:5000/finapp`，使用默认账户登录。

## 技术栈

- **后端**：Python 3, Flask, SQLAlchemy, SQLite
- **前端**：HTML5, CSS3, JavaScript, ZUI
- **PDF**：`fpdf2` + 文泉驿中文字体
- **认证**：Flask-Login

## 目录结构

```
finapp/
├── app.py              # Flask 主应用
├── config.py           # 配置文件
├── data/               # SQLite 数据库
├── static/
│   ├── css/            # 样式表
│   └── js/             # 前端脚本
├── templates/          # HTML 模板
└── fonts/              # 中文字体（可选）
```
