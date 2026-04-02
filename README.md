# 财务系统

简洁的个人/家庭财务收支管理系统，支持多账户、收支分类、账户互转、报表生成与 PDF 导出。中文友好，数据存储在本地 SQLite。

## 默认账户

- **用户名**：`admin`
- **密码**：`admin123`
- **访问地址**：`http://localhost:5000/finapp`

> 首次登录后请修改密码。

## 主要功能

### 💰 交易录入
- 支出/收入分类，**两级联动**（大类 → 明细）
- 支持账户选择、备注
- **批量录入**：文本批量导入多条交易

### 🔄 账户互转
- 转出账户和转入账户之间互转
- 仅变更两个账户的余额，**不记录为收入/支出**

### 📊 报表系统
- **日报表**：每日收支明细 + 汇总
- **月报表**：按日汇总 + 月度总计
- **年度报告**：按月汇总 + 年度总计
- **图表分析**：月度对比、统计摘要
- 所有报表均支持 **PDF 导出**（中文文泉驿字体，正常显示）

### 🏦 账户管理
- 多账户支持（银行、证券、微信、支付宝等）
- 账户余额自动计算（新增/编辑/删除交易后自动更新）
- 支持账户增删改

### 👤 用户管理
- 登录认证（Flask-Login）
- 支持"记住我"——勾选后一天内免登录
- 修改密码（登录页 / 用户管理页均可）

## 界面预览

导航栏统一：首页 | 录入 | 账户 | 报表 | 导出 | 用户 | 注销

## 快速部署

```bash
# 克隆项目
git clone https://github.com/owen590/finapp.git
cd finapp

# 安装依赖
pip install flask flask-sqlalchemy flask-login werkzeug reportlab fpdf2

# 启动（端口 5000，路径 /finapp）
python app.py
```

访问 `http://localhost:5000/finapp`，使用默认账户登录。

## 目录结构

```
finapp/
├── app.py              # Flask 主应用（含全部路由和业务逻辑）
├── models.py           # 数据库模型
├── config.py           # 配置文件
├── data/
│   └── finance.db     # SQLite 数据库（可替换为空数据）
├── static/
│   ├── css/           # 样式表（style.css / entry.css / reports.css）
│   └── js/            # 前端脚本（app.js / entry.js / reports.js）
├── templates/         # HTML 模板
└── README.md
```

## 技术栈

- **后端**：Python 3, Flask, SQLAlchemy, Flask-Login
- **前端**：HTML5, CSS3, JavaScript（原生），ZUI CSS
- **PDF 导出**：fpdf2 + 文泉驿中文字体
- **数据库**：SQLite

## 数据说明

- 数据库文件 `data/finance.db` 包含示例账户结构，**交易记录已清空**
- 替换为自己的 SQLite 文件即可使用
