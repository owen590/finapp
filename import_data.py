from app import app
from models import db, Transaction, Loan, Distribution
from utils import import_from_excel
import os

with app.app_context():
    excel_file = 'e:\\账务系统\\恒驰泵业.xlsx'
    
    if not os.path.exists(excel_file):
        print(f"Excel文件不存在: {excel_file}")
        exit(1)
    
    print("开始导入Excel数据...")
    
    try:
        data = import_from_excel(excel_file)
        
        print(f"解析到 {len(data['transactions'])} 条交易记录")
        print(f"解析到 {len(data['loans'])} 条借款记录")
        print(f"解析到 {len(data['distributions'])} 条分配记录")
        
        db.session.add_all(data['transactions'])
        db.session.add_all(data['loans'])
        db.session.add_all(data['distributions'])
        db.session.commit()
        
        print("数据导入成功！")
        
        total_income = sum(t.amount for t in data['transactions'] if t.type == '收入')
        total_expense = sum(t.amount for t in data['transactions'] if t.type == '出账')
        total_withdrawal = sum(t.amount for t in data['transactions'] if t.type == '提现')
        
        print(f"\n导入统计:")
        print(f"总收入: ¥{total_income:,.2f}")
        print(f"总支出: ¥{total_expense:,.2f}")
        print(f"总提现: ¥{total_withdrawal:,.2f}")
        print(f"结余: ¥{total_income - total_expense - total_withdrawal:,.2f}")
        
    except Exception as e:
        db.session.rollback()
        print(f"导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
