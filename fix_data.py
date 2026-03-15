import sqlite3
import os

# 连接到数据库
db_path = 'e:\\账务系统\\data\\finance.db'

if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查transactions表的结构
cursor.execute("PRAGMA table_info(transactions)")
columns = cursor.fetchall()
print("表结构:")
for column in columns:
    print(f"{column[1]}: {column[2]}")

# 检查数据，寻找摘要和金额颠倒的记录
cursor.execute("SELECT id, description, amount FROM transactions LIMIT 20")
records = cursor.fetchall()
print("\n前20条记录:")
for record in records:
    print(f"ID: {record[0]}, 摘要: {record[1]}, 金额: {record[2]}")

# 修复逻辑：检查description是否为数字，amount是否为文本
# 如果description看起来是数字，amount看起来是文本，则交换它们
fixed_count = 0

cursor.execute("SELECT id, description, amount FROM transactions")
all_records = cursor.fetchall()

for record in all_records:
    id, description, amount = record
    
    # 检查description是否为数字，amount是否为文本
    description_is_number = False
    amount_is_text = False
    
    # 检查description是否可以转换为数字
    try:
        if description and isinstance(description, str):
            # 移除可能的货币符号和逗号
            clean_desc = description.replace('¥', '').replace(',', '').strip()
            float(clean_desc)
            description_is_number = True
    except:
        pass
    
    # 检查amount是否为文本
    try:
        if isinstance(amount, str) and not amount.replace('.', '', 1).isdigit():
            amount_is_text = True
    except:
        pass
    
    # 如果发现颠倒的情况，交换它们
    if description_is_number and amount_is_text:
        # 交换值
        new_description = amount
        new_amount = float(description.replace('¥', '').replace(',', '').strip())
        
        # 更新数据库
        cursor.execute(
            "UPDATE transactions SET description = ?, amount = ? WHERE id = ?",
            (new_description, new_amount, id)
        )
        fixed_count += 1
        print(f"修复记录 ID: {id}, 旧摘要: {description}, 旧金额: {amount}, 新摘要: {new_description}, 新金额: {new_amount}")

# 提交更改
conn.commit()

print(f"\n修复完成，共修复了 {fixed_count} 条记录")

# 验证修复结果
cursor.execute("SELECT id, description, amount FROM transactions LIMIT 20")
fixed_records = cursor.fetchall()
print("\n修复后的前20条记录:")
for record in fixed_records:
    print(f"ID: {record[0]}, 摘要: {record[1]}, 金额: {record[2]}")

# 关闭连接
conn.close()
