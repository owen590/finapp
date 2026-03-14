恒驰泵业财务系统

## 项目结构

```
账务系统/
├── app.py                 # Flask主应用
├── models.py              # 数据库模型
├── config.py              # 配置文件
├── requirements.txt       # 依赖包
├── database.py            # 数据库初始化
├── utils.py               # 工具函数
├── static/                # 静态文件
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── templates/             # HTML模板
│   ├── index.html
│   ├── ledger.html
│   ├── monthly.html
│   ├── loans.html
│   └── import.html
└── data/                  # 数据目录
    └── finance.db         # SQLite数据库
```

## 功能模块

1. **总账管理** - 查看和管理所有财务记录
2. **月度账单** - 按月查看收入、支出和提现
3. **借款管理** - 记录和管理借款信息
4. **数据导入** - 从Excel导入财务数据
5. **统计分析** - 财务数据统计和报表

## 数据库设计

### 主要表结构

1. **transactions** - 交易记录表
   - id: 主键
   - date: 日期
   - type: 类型 (出账/收入/提现)
   - category: 类别
   - amount: 金额
   - description: 描述
   - month: 所属月份
   - year: 所属年份

2. **loans** - 借款表
   - id: 主键
   - date: 日期
   - lender: 放款人
   - amount: 金额
   - status: 归还状态

3. **distributions** - 分配表
   - id: 主键
   - date: 日期
   - person: 人员
   - amount: 金额

## 使用说明

1. 安装依赖: `pip install -r requirements.txt`
2. 运行应用: `python app.py`
3. 访问: http://localhost:5000
