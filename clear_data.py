from app import app
from models import db, Transaction, Loan, Distribution

with app.app_context():
    print("开始清空数据...")
    
    # 删除所有交易记录
    transaction_count = Transaction.query.count()
    Transaction.query.delete()
    print(f"✓ 已删除 {transaction_count} 条交易记录")
    
    # 删除所有借款记录
    loan_count = Loan.query.count()
    Loan.query.delete()
    print(f"✓ 已删除 {loan_count} 条借款记录")
    
    # 删除所有分配记录
    distribution_count = Distribution.query.count()
    Distribution.query.delete()
    print(f"✓ 已删除 {distribution_count} 条分配记录")
    
    # 提交更改
    db.session.commit()
    
    print("\n数据清空完成！")
    print("数据库已重置为初始状态。")
