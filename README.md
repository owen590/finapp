# 财务管理系统

一个基于Flask的Web财务管理系统，支持数据录入、筛选、导入导出功能。

## 功能特性

- **数据录入**：支持单条交易录入和批量录入
- **数据筛选**：支持按日期范围、年份、月份、收支类型筛选
- **数据导出**：支持按条件筛选并导出CSV文件
- **响应式设计**：支持PC端和移动端自适应显示
- **批量导入**：支持从Excel复制内容直接导入

## 技术栈

- **后端**：Flask, SQLAlchemy, SQLite
- **前端**：HTML5, CSS3, JavaScript
- **数据库**：SQLite

## 项目结构

```
账务系统/
├── app.py                 # Flask主应用
├── models.py              # 数据库模型
├── config.py              # 配置文件
├── requirements.txt       # 依赖包
├── static/                # 静态文件
│   ├── css/              # 样式文件
│   └── js/               # JavaScript文件
├── templates/             # 模板文件
│   ├── index.html        # 首页
│   ├── entry.html        # 数据录入页
│   └── export.html       # 数据导出页
├── data/                  # 数据库文件
└── utils.py              # 工具函数
```

## 安装和运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 初始化数据库：
```bash
python create_tables.py
```

3. 启动应用：
```bash
python app.py
```

4. 访问应用：
打开浏览器访问 http://localhost:5000

## 使用说明

### 数据录入
- **交易录入**：单条录入交易信息
- **批量录入**：支持制表符、竖线或逗号分隔的批量数据导入

### 数据筛选
- **日期范围**：按开始日期和结束日期筛选
- **年份月份**：按特定年份和月份筛选
- **收支类型**：按入账/出账类型筛选

### 数据导出
- 支持按筛选条件导出CSV文件
- 导出文件包含完整的交易信息

## 开发说明

### 数据库模型
系统使用SQLite数据库，主要包含以下表：
- `transactions`：交易记录表

### API接口
- `GET /api/transactions`：获取交易列表
- `POST /api/transactions`：创建交易记录
- `GET /api/statistics`：获取统计数据
- `GET /api/export`：导出数据

## 许可证

MIT License