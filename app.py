from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from config import Config
from models import Transaction, Loan, Distribution, Capital, User, Account, db
from utils import import_from_excel, import_from_csv
from sync import sync_transaction_to_feishu, update_feishu_transaction_record, delete_feishu_transaction_record, sync_account_to_feishu, update_feishu_account_record
from datetime import datetime, date, timedelta
import os

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

db.init_app(app)

# Flask-Login配置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录以访问此页面'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/finapp/')
@login_required
def index():
    return render_template('index.html')

@app.route('/finapp/accounts')
@login_required
def accounts_page():
    return render_template('accounts.html')

@app.route('/finapp/ledger')
@login_required
def ledger():
    return render_template('ledger.html')

@app.route('/finapp/monthly')
@login_required
def monthly():
    return render_template('monthly.html')

@app.route('/finapp/import')
@login_required
def import_page():
    return render_template('import.html')

@app.route('/finapp/entry')
@login_required
def entry():
    return render_template('entry.html')

@app.route('/finapp/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/finapp/export')
@login_required
def export():
    return render_template('export.html')

# 登录路由
@app.route('/finapp/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('登录成功', 'success')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

# 注销路由
@app.route('/finapp/logout')
@login_required
def logout():
    logout_user()
    flash('已注销', 'success')
    return redirect(url_for('login'))

# 用户管理路由
@app.route('/finapp/users')
@login_required
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/finapp/users/create', methods=['POST'])
@login_required
def create_user():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    
    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('用户名已存在', 'error')
        return redirect(url_for('users'))
    
    # 创建新用户
    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    flash('用户创建成功', 'success')
    return redirect(url_for('users'))

@app.route('/finapp/users/update', methods=['POST'])
@login_required
def update_user():
    user_id = request.form['id']
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    
    user = User.query.get(user_id)
    if not user:
        flash('用户不存在', 'error')
        return redirect(url_for('users'))
    
    # 检查用户名是否已被其他用户使用
    existing_user = User.query.filter_by(username=username).filter(User.id != user_id).first()
    if existing_user:
        flash('用户名已存在', 'error')
        return redirect(url_for('users'))
    
    user.username = username
    user.role = role
    if password:
        user.set_password(password)
    
    db.session.commit()
    flash('用户更新成功', 'success')
    return redirect(url_for('users'))

@app.route('/finapp/users/delete/<int:id>')
@login_required
def delete_user(id):
    user = User.query.get(id)
    if not user:
        flash('用户不存在', 'error')
        return redirect(url_for('users'))
    
    # 不允许删除当前登录用户
    if user.id == current_user.id:
        flash('不能删除当前登录用户', 'error')
        return redirect(url_for('users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('用户删除成功', 'success')
    return redirect(url_for('users'))

@app.route('/finapp/api/export', methods=['GET'])
@login_required
def export_transactions():
    transaction_type = request.args.get('type')
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    query = Transaction.query
    
    if transaction_type:
        query = query.filter_by(type=transaction_type)
    if year:
        query = query.filter_by(year=year)
    if month:
        query = query.filter_by(month=month)
    
    transactions = query.order_by(Transaction.date.desc()).all()
    
    return jsonify({
        'transactions': [t.to_dict() for t in transactions]
    })

@app.route('/finapp/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    transaction_type = request.args.get('type')
    start_date = request.args.get('start_date', type=str)
    end_date = request.args.get('end_date', type=str)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    query = Transaction.query
    
    if transaction_type:
        query = query.filter_by(type=transaction_type)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if year:
        query = query.filter_by(year=year)
    if month:
        query = query.filter_by(month=month)
    
    pagination = query.order_by(Transaction.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'transactions': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@app.route('/finapp/api/transactions', methods=['POST'])
@login_required
def create_transaction():
    data = request.json
    
    date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    
    transaction = Transaction(
        date=date,
        type=data['type'],
        category=data.get('category', ''),
        sub_category=data.get('sub_category', ''),
        amount=float(data['amount']),
        description=data.get('description', ''),
        remark=data.get('remark', ''),
        month=date.month,
        year=date.year,
        account_id=data.get('account_id')
    )
    
    db.session.add(transaction)
    db.session.flush()
    
    # 更新账户余额
    if transaction.account_id:
        account = Account.query.get(transaction.account_id)
        if account:
            if transaction.type == '入账':
                account.current_balance += transaction.amount
            else:
                account.current_balance -= transaction.amount
    
    db.session.commit()
    
    # 同步到飞书
    try:
        account_name = ""
        if transaction.account_id:
            account = Account.query.get(transaction.account_id)
            if account:
                account_name = account.name
        
        t_dict = {
            "date": data['date'],
            "type": transaction.type,
            "category": transaction.category,
            "sub_category": transaction.sub_category,
            "description": transaction.description,
            "amount": transaction.amount,
            "remark": transaction.remark,
            "account_name": account_name
        }
        record_id = sync_transaction_to_feishu(t_dict)
        if record_id:
            transaction.bitable_record_id = record_id
            db.session.commit()
    except Exception as e:
        print(f"飞书同步失败: {e}")
    
    return jsonify(transaction.to_dict()), 201

@app.route('/finapp/api/transactions/<int:id>', methods=['GET'])
@login_required
def get_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    return jsonify(transaction.to_dict())

@app.route('/finapp/api/transactions/<int:id>', methods=['PUT'])
@login_required
def update_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    data = request.json
    
    # 记录旧值，用于余额调整
    old_amount = transaction.amount
    old_type = transaction.type
    old_account_id = transaction.account_id
    
    if 'date' in data:
        date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        transaction.date = date
        transaction.month = date.month
        transaction.year = date.year
    
    if 'type' in data:
        transaction.type = data['type']
    if 'category' in data:
        transaction.category = data['category']
    if 'sub_category' in data:
        transaction.sub_category = data['sub_category']
    if 'amount' in data:
        transaction.amount = float(data['amount'])
    if 'description' in data:
        transaction.description = data['description']
    if 'remark' in data:
        transaction.remark = data['remark']
    if 'account_id' in data:
        transaction.account_id = data['account_id']
    
    # 重新计算账户余额
    # 1. 恢复旧账户的余额
    if old_account_id:
        old_account = Account.query.get(old_account_id)
        if old_account:
            if old_type == '入账':
                old_account.current_balance -= old_amount
            else:
                old_account.current_balance += old_amount
    
    # 2. 应用新账户的余额变动
    if transaction.account_id:
        new_account = Account.query.get(transaction.account_id)
        if new_account:
            if transaction.type == '入账':
                new_account.current_balance += transaction.amount
            else:
                new_account.current_balance -= transaction.amount
    
    db.session.commit()
    
    # 同步到飞书
    try:
        account_name = ""
        if transaction.account_id:
            account = Account.query.get(transaction.account_id)
            if account:
                account_name = account.name
        
        t_dict = {
            "date": transaction.date.strftime('%Y-%m-%d'),
            "type": transaction.type,
            "category": transaction.category,
            "sub_category": transaction.sub_category,
            "description": transaction.description,
            "amount": transaction.amount,
            "remark": transaction.remark,
            "account_name": account_name
        }
        if transaction.bitable_record_id:
            update_feishu_transaction_record(transaction.bitable_record_id, t_dict)
    except Exception as e:
        print(f"飞书同步失败: {e}")
    
    return jsonify(transaction.to_dict())

@app.route('/finapp/api/transactions/<int:id>', methods=['DELETE'])
@login_required
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    
    # 更新账户余额
    if transaction.account_id:
        account = Account.query.get(transaction.account_id)
        if account:
            if transaction.type == '入账':
                account.current_balance -= transaction.amount
            else:
                account.current_balance += transaction.amount
    
    # 删除飞书记录
    if transaction.bitable_record_id:
        try:
            delete_feishu_transaction_record(transaction.bitable_record_id)
        except Exception as e:
            print(f"飞书删除失败: {e}")
    
    db.session.delete(transaction)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})

@app.route('/finapp/api/distributions', methods=['GET'])
@login_required
def get_distributions():
    distributions = Distribution.query.order_by(Distribution.date.desc()).all()
    return jsonify([d.to_dict() for d in distributions])

@app.route('/finapp/api/distributions', methods=['POST'])
@login_required
def create_distribution():
    data = request.json
    
    date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    
    distribution = Distribution(
        date=date,
        person=data['person'],
        amount=float(data['amount'])
    )
    
    db.session.add(distribution)
    db.session.commit()
    
    return jsonify(distribution.to_dict()), 201

@app.route('/finapp/api/loans', methods=['GET'])
@login_required
def get_loans():
    loans = Loan.query.order_by(Loan.date.desc()).all()
    return jsonify([l.to_dict() for l in loans])

@app.route('/finapp/api/loans', methods=['POST'])
@login_required
def create_loan():
    data = request.json
    
    date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    
    loan = Loan(
        date=date,
        lender=data['lender'],
        amount=float(data['amount']),
        status=data.get('status', '未归还')
    )
    
    db.session.add(loan)
    db.session.commit()
    
    return jsonify(loan.to_dict()), 201

@app.route('/finapp/api/loans/<int:id>', methods=['PUT'])
@login_required
def update_loan(id):
    loan = Loan.query.get_or_404(id)
    data = request.json
    
    if 'status' in data:
        loan.status = data['status']
    if 'return_date' in data and data['return_date']:
        loan.return_date = datetime.strptime(data['return_date'], '%Y-%m-%d').date()
    
    db.session.commit()
    
    return jsonify(loan.to_dict())

@app.route('/finapp/api/loans/<int:id>', methods=['DELETE'])
@login_required
def delete_loan(id):
    loan = Loan.query.get_or_404(id)
    db.session.delete(loan)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})

@app.route('/finapp/api/capital', methods=['GET'])
@login_required
def get_capital():
    capital = Capital.query.order_by(Capital.date.desc()).all()
    return jsonify([c.to_dict() for c in capital])

@app.route('/finapp/api/capital', methods=['POST'])
@login_required
def create_capital():
    data = request.json
    
    date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    
    capital = Capital(
        date=date,
        investor=data['investor'],
        amount=float(data['amount']),
        description=data.get('description', '')
    )
    
    db.session.add(capital)
    db.session.commit()
    
    return jsonify(capital.to_dict()), 201

@app.route('/finapp/api/capital/<int:id>', methods=['PUT'])
@login_required
def update_capital(id):
    capital = Capital.query.get_or_404(id)
    data = request.json
    
    if 'date' in data:
        capital.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    if 'investor' in data:
        capital.investor = data['investor']
    if 'amount' in data:
        capital.amount = float(data['amount'])
    if 'description' in data:
        capital.description = data['description']
    
    db.session.commit()
    
    return jsonify(capital.to_dict())

@app.route('/finapp/api/capital/<int:id>', methods=['DELETE'])
@login_required
def delete_capital(id):
    capital = Capital.query.get_or_404(id)
    db.session.delete(capital)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})

@app.route('/finapp/api/statistics', methods=['GET'])
@login_required
def get_statistics():
    start_date = request.args.get('start_date', type=str)
    end_date = request.args.get('end_date', type=str)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    trans_type = request.args.get('type', type=str)
    
    query = Transaction.query
    
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if year:
        query = query.filter_by(year=year)
    if month:
        query = query.filter_by(month=month)
    if trans_type:
        query = query.filter_by(type=trans_type)
    
    transactions = query.all()
    
    total_income = sum(t.amount for t in transactions if t.type == '入账')
    total_expense = sum(t.amount for t in transactions if t.type == '出账')
    
    return jsonify({
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense,
        'transaction_count': len(transactions)
    })

# ----------- 账户资产 API -----------
@app.route('/finapp/api/accounts', methods=['GET'])
@login_required
def get_accounts():
    accounts = Account.query.order_by(Account.id.desc()).all()
    return jsonify([a.to_dict() for a in accounts])

@app.route('/finapp/api/accounts', methods=['POST'])
@login_required
def create_account():
    data = request.json
    
    account = Account(
        name=data['name'],
        account_type=data.get('account_type', ''),
        initial_balance=float(data.get('initial_balance', 0)),
        current_balance=float(data.get('initial_balance', 0)),
        remark=data.get('remark', '')
    )
    
    db.session.add(account)
    db.session.commit()
    
    # 同步到飞书
    try:
        record_id = sync_account_to_feishu(account.to_dict())
        if record_id:
            # 保存飞书记录ID需要扩展account模型，这里只打印
            print(f"飞书账户同步成功: {record_id}")
    except Exception as e:
        print(f"飞书账户同步失败: {e}")
    
    return jsonify(account.to_dict()), 201

@app.route('/finapp/api/accounts/<int:id>', methods=['GET'])
@login_required
def get_account(id):
    account = Account.query.get_or_404(id)
    return jsonify(account.to_dict())

@app.route('/finapp/api/accounts/<int:id>', methods=['PUT'])
@login_required
def update_account(id):
    account = Account.query.get_or_404(id)
    data = request.json
    
    if 'name' in data:
        account.name = data['name']
    if 'account_type' in data:
        account.account_type = data['account_type']
    if 'remark' in data:
        account.remark = data['remark']
    if 'initial_balance' in data:
        # 调整初始余额变化对当前余额的影响
        diff = float(data['initial_balance']) - account.initial_balance
        account.initial_balance = float(data['initial_balance'])
        account.current_balance += diff
    
    db.session.commit()
    return jsonify(account.to_dict())

@app.route('/finapp/api/accounts/<int:id>', methods=['DELETE'])
@login_required
def delete_account(id):
    account = Account.query.get_or_404(id)
    
    # 检查是否有关联交易
    if Transaction.query.filter_by(account_id=id).first():
        return jsonify({'error': '该账户有关联交易，无法删除'}), 400
    
    db.session.delete(account)
    db.session.commit()
    return jsonify({'message': '删除成功'})

@app.route('/finapp/api/accounts/recalculate', methods=['POST'])
@login_required
def recalculate_account_balances():
    """重新计算所有账户余额"""
    for account in Account.query.all():
        balance = account.initial_balance
        for t in Transaction.query.filter_by(account_id=account.id).order_by(Transaction.date):
            if t.type == '入账':
                balance += t.amount
            else:
                balance -= t.amount
        account.current_balance = balance
    db.session.commit()
    return jsonify({'message': '余额重算完成'})

# ----------- 数据管理 API -----------
@app.route('/finapp/api/clear-data', methods=['POST'])
@login_required
def clear_all_data():
    """清空所有交易数据（保留账户和用户）"""
    Transaction.query.delete()
    Loan.query.delete()
    Distribution.query.delete()
    Capital.query.delete()
    db.session.commit()
    
    # 重置账户余额为初始值
    for account in Account.query.all():
        account.current_balance = account.initial_balance
    db.session.commit()
    
    return jsonify({'message': '所有交易数据已清空，账户余额已重置'})

@app.route('/finapp/api/clear-accounts', methods=['POST'])
@login_required
def clear_accounts():
    """清空所有账户"""
    Transaction.query.delete()
    Account.query.delete()
    db.session.commit()
    return jsonify({'message': '所有账户和交易数据已清空'})

@app.route('/finapp/api/import', methods=['POST'])
@login_required
def import_excel():
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        return jsonify({'error': '只支持Excel和CSV文件'}), 400
    
    upload_dir = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    filepath = os.path.join(upload_dir, file.filename)
    file.save(filepath)
    
    try:
        if file.filename.endswith('.csv'):
            data = import_from_csv(filepath)
        else:
            data = import_from_excel(filepath)
        
        db.session.add_all(data['transactions'])
        db.session.commit()
        
        os.remove(filepath)
        
        return jsonify({
            'message': '导入成功',
            'transactions_count': len(data['transactions']),
            'loans_count': len(data['loans']),
            'distributions_count': len(data['distributions'])
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 报表API
@app.route('/finapp/api/reports', methods=['GET'])
@login_required
def get_reports():
    report_type = request.args.get('type', type=str)
    date = request.args.get('date', type=str)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if not report_type:
        return jsonify({'error': '缺少报表类型参数'}), 400
    
    try:
        if report_type == 'daily':
            return get_daily_report(date)
        elif report_type == 'monthly':
            return get_monthly_report(year, month)
        elif report_type == 'yearly':
            return get_yearly_report(year)
        else:
            return jsonify({'error': '无效的报表类型'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_daily_report(date):
    if not date:
        return jsonify({'error': '缺少日期参数'}), 400
    
    # 解析日期
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': '日期格式错误，应为YYYY-MM-DD'}), 400
    
    # 查询当日交易
    transactions = Transaction.query.filter_by(date=target_date).all()
    
    # 计算统计数据
    total_income = sum(t.amount for t in transactions if t.type == '入账')
    total_expense = sum(t.amount for t in transactions if t.type == '出账')
    
    # 计算上期结余（当天之前的所有交易结余）
    previous_transactions = Transaction.query.filter(Transaction.date < target_date).all()
    previous_income = sum(t.amount for t in previous_transactions if t.type == '入账')
    previous_expense = sum(t.amount for t in previous_transactions if t.type == '出账')
    opening_balance = previous_income - previous_expense
    
    # 格式化交易数据
    transaction_data = []
    for t in transactions:
        transaction_data.append({
            'id': t.id,
            'date': t.date.strftime('%Y-%m-%d'),
            'type': t.type,
            'category': t.category,
            'description': t.description,
            'amount': t.amount,
            'remark': t.remark,
            'created_at': t.created_at.isoformat()
        })
    
    return jsonify({
        'type': 'daily',
        'date': date,
        'transactions': transaction_data,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense,
        'opening_balance': opening_balance
    })

def get_monthly_report(year, month):
    if not year or not month:
        return jsonify({'error': '缺少年份或月份参数'}), 400
    
    # 构建日期范围
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # 查询该月交易
    transactions = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()
    
    # 计算上期结余（当月1日之前所有交易的结余）
    previous_transactions = Transaction.query.filter(Transaction.date < start_date).all()
    previous_income = sum(t.amount for t in previous_transactions if t.type == '入账')
    previous_expense = sum(t.amount for t in previous_transactions if t.type == '出账')
    opening_balance = previous_income - previous_expense
    
    # 按日期分组
    daily_data = {}
    total_income = 0
    total_expense = 0
    
    for t in transactions:
        date_str = t.date.strftime('%Y-%m-%d')
        if date_str not in daily_data:
            daily_data[date_str] = {
                'income': [],
                'expense': []
            }
        
        transaction_info = {
            'id': t.id,
            'category': t.category,
            'description': t.description,
            'amount': t.amount,
            'remark': t.remark,
            'created_at': t.created_at.isoformat()
        }
        
        if t.type == '入账':
            daily_data[date_str]['income'].append(transaction_info)
            total_income += t.amount
        else:
            daily_data[date_str]['expense'].append(transaction_info)
            total_expense += t.amount
    
    return jsonify({
        'type': 'monthly',
        'year': year,
        'month': month,
        'daily_data': daily_data,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense,
        'total_count': len(transactions),
        'opening_balance': opening_balance
    })

def get_yearly_report(year):
    if not year:
        return jsonify({'error': '缺少年份参数'}), 400
    
    # 构建日期范围
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    # 查询该年交易
    transactions = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()
    
    # 计算上期结余（当年1月1日之前所有交易的结余）
    previous_transactions = Transaction.query.filter(Transaction.date < start_date).all()
    previous_income = sum(t.amount for t in previous_transactions if t.type == '入账')
    previous_expense = sum(t.amount for t in previous_transactions if t.type == '出账')
    opening_balance = previous_income - previous_expense
    
    # 按月份分组
    monthly_data = {}
    total_income = 0
    total_expense = 0
    
    for t in transactions:
        month_str = str(t.date.month)
        if month_str not in monthly_data:
            monthly_data[month_str] = {
                'total_income': 0,
                'total_expense': 0,
                'transaction_count': 0
            }
        
        if t.type == '入账':
            monthly_data[month_str]['total_income'] += t.amount
            total_income += t.amount
        else:
            monthly_data[month_str]['total_expense'] += t.amount
            total_expense += t.amount
        
        monthly_data[month_str]['transaction_count'] += 1
    
    return jsonify({
        'type': 'yearly',
        'year': year,
        'monthly_data': monthly_data,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense,
        'total_count': len(transactions),
        'opening_balance': opening_balance
    })

# PDF导出API
@app.route('/finapp/api/export-pdf', methods=['POST'])
@login_required
def export_pdf():
    data = request.json
    report_type = data.get('type')
    report_data = data.get('data')
    
    if not report_type or not report_data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import io
        import os
        
        # 注册中文字体
        try:
            # Windows系统字体路径
            windows_fonts_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
            
            # 优先使用微软雅黑，如果不存在则使用宋体
            font_paths = [
                os.path.join(windows_fonts_dir, 'msyh.ttc'),  # 微软雅黑
                os.path.join(windows_fonts_dir, 'simsun.ttc'),  # 宋体
                os.path.join(windows_fonts_dir, 'simhei.ttf'),  # 黑体
            ]
            
            chinese_font = 'Helvetica'
            
            # 尝试注册字体
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font_name = os.path.splitext(os.path.basename(font_path))[0]
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        chinese_font = font_name
                        print(f"成功注册字体: {font_name} from {font_path}")
                        break
                    except Exception as e:
                        print(f"注册字体失败: {font_path}, error: {e}")
                        continue
            
            # 如果仍然没有找到中文字体，使用默认字体
            if chinese_font == 'Helvetica':
                print("未找到中文字体，使用默认字体")
                
        except Exception as e:
            print(f"字体检测错误: {e}")
            chinese_font = 'Helvetica'
        
        # 创建PDF内存缓冲区
        buffer = io.BytesIO()
        # 减少左右边距，增加内容宽度
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=0.5*cm, rightMargin=0.5*cm, topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        
        # 添加标题
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            fontName=chinese_font
        )
        
        normal_style = ParagraphStyle(
            'NormalChinese',
            parent=styles['Normal'],
            fontName=chinese_font
        )
        
        # 初始化table_data变量
        table_data = []
        
        # 标题
        if report_type == 'daily':
            title = f"日报表 - {report_data['date']}"
        elif report_type == 'monthly':
            title = f"月报表 - {report_data['year']}年{report_data['month']}月"
        elif report_type == 'yearly':
            title = f"年度报表 - {report_data['year']}年"
        elif report_type == 'chart':
            title = report_data.get('title', '图表分析报告')
        
        # 标题居中
        title_para = Paragraph(title, title_style)
        title_para.alignment = 1  # 1表示居中
        elements.append(title_para)
        elements.append(Spacer(1, 20))
        
        # 生成表格数据
        if report_type == 'daily':
            # 日报表
            table_data = [[Paragraph('时间', normal_style), Paragraph('收支<br/>分类', normal_style), Paragraph('明细<br/>分类', normal_style), Paragraph('摘要', normal_style), Paragraph('入账', normal_style), Paragraph('出账', normal_style), Paragraph('结余', normal_style)]]
            running_balance = report_data.get('opening_balance', 0)
            # 如果有上期结余，添加首行
            if running_balance != 0:
                table_data.append([
                    Paragraph('-', normal_style),
                    Paragraph('上期结余', normal_style),
                    Paragraph('-', normal_style),
                    Paragraph('上期结余转入', normal_style),
                    Paragraph('', normal_style),
                    Paragraph('', normal_style),
                    Paragraph(f"{running_balance:,.2f}", normal_style)
                ])
            for t in report_data.get('transactions', []):
                time = datetime.fromisoformat(t['created_at']).strftime('%H:%M')
                income = t['amount'] if t['type'] == '入账' else 0
                expense = t['amount'] if t['type'] == '出账' else 0
                running_balance = running_balance + income - expense
                income_str = f"{income:,.2f}" if income > 0 else ''
                expense_str = f"{expense:,.2f}" if expense > 0 else ''
                table_data.append([
                    Paragraph(time, normal_style),
                    Paragraph(t['type'], normal_style),
                    Paragraph(t['category'], normal_style),
                    Paragraph(t['description'], normal_style),
                    Paragraph(income_str, normal_style),
                    Paragraph(expense_str, normal_style),
                    Paragraph(f"{running_balance:,.2f}", normal_style)
                ])
            # 添加汇总行
            table_data.append([
                Paragraph('', normal_style),
                Paragraph('', normal_style),
                Paragraph('', normal_style),
                Paragraph('当日汇总', normal_style),
                Paragraph(f"{report_data['total_income']:,.2f}", normal_style),
                Paragraph(f"{report_data['total_expense']:,.2f}", normal_style),
                Paragraph(f"{running_balance:,.2f}", normal_style)
            ])
        
        elif report_type == 'monthly':
            # 月报表
            table_data = [[Paragraph('日期', normal_style), Paragraph('收支<br/>分类', normal_style), Paragraph('明细<br/>分类', normal_style), Paragraph('摘要', normal_style), Paragraph('入账', normal_style), Paragraph('出账', normal_style), Paragraph('结余', normal_style)]]
            running_balance = report_data.get('opening_balance', 0)
            # 如果有上期结余，添加首行
            if running_balance != 0:
                start_date = f"{report_data['month']:02d}-01"
                table_data.append([
                    Paragraph(start_date, normal_style),
                    Paragraph('上期结余', normal_style),
                    Paragraph('-', normal_style),
                    Paragraph('上期结余转入', normal_style),
                    Paragraph('', normal_style),
                    Paragraph('', normal_style),
                    Paragraph(f"{running_balance:,.2f}", normal_style)
                ])
            # 按日期排序
            sorted_dates = sorted(report_data.get('daily_data', {}).keys())
            for date_str in sorted_dates:
                day_data = report_data['daily_data'][date_str]
                # 移除年份，只显示月-日，以节省宽度
                short_date = date_str.split('-')[1:]  # 移除年份部分
                short_date_str = '-'.join(short_date)
                # 先添加收入记录
                for t in day_data.get('income', []):
                    running_balance = running_balance + t['amount']
                    table_data.append([
                        Paragraph(short_date_str, normal_style),
                        Paragraph('入账', normal_style),
                        Paragraph(t['category'], normal_style),
                        Paragraph(t['description'], normal_style),
                        Paragraph(f"{t['amount']:,.2f}", normal_style),
                        Paragraph('', normal_style),
                        Paragraph(f"{running_balance:,.2f}", normal_style)
                    ])
                # 再添加支出记录
                for t in day_data.get('expense', []):
                    running_balance = running_balance - t['amount']
                    table_data.append([
                        Paragraph(short_date_str, normal_style),
                        Paragraph('出账', normal_style),
                        Paragraph(t['category'], normal_style),
                        Paragraph(t['description'], normal_style),
                        Paragraph('', normal_style),
                        Paragraph(f"{t['amount']:,.2f}", normal_style),
                        Paragraph(f"{running_balance:,.2f}", normal_style)
                    ])
            # 添加汇总行
            table_data.append([
                Paragraph('', normal_style),
                Paragraph('', normal_style),
                Paragraph('', normal_style),
                Paragraph('月度汇总', normal_style),
                Paragraph(f"{report_data['total_income']:,.2f}", normal_style),
                Paragraph(f"{report_data['total_expense']:,.2f}", normal_style),
                Paragraph(f"{running_balance:,.2f}", normal_style)
            ])
        
        elif report_type == 'yearly':
            # 年度报表
            table_data = [[Paragraph('月份', normal_style), Paragraph('入账总额', normal_style), Paragraph('出账总额', normal_style), Paragraph('结余', normal_style), Paragraph('交易笔数', normal_style)]]
            running_balance = report_data.get('opening_balance', 0)
            # 如果有上期结余，添加首行
            if running_balance != 0:
                table_data.append([
                    Paragraph('年初', normal_style),
                    Paragraph('', normal_style),
                    Paragraph('', normal_style),
                    Paragraph(f"{running_balance:,.2f}", normal_style),
                    Paragraph('', normal_style)
                ])
            # 按月份排序
            sorted_months = sorted(report_data.get('monthly_data', {}).keys(), key=lambda x: int(x))
            for month_str in sorted_months:
                month_data = report_data['monthly_data'][month_str]
                month_balance = month_data['total_income'] - month_data['total_expense']
                running_balance = running_balance + month_balance
                table_data.append([
                    Paragraph(f"{month_str}月", normal_style),
                    Paragraph(f"{month_data['total_income']:,.2f}", normal_style),
                    Paragraph(f"{month_data['total_expense']:,.2f}", normal_style),
                    Paragraph(f"{running_balance:,.2f}", normal_style),
                    Paragraph(str(month_data['transaction_count']), normal_style)
                ])
            # 添加汇总行
            table_data.append([
                Paragraph('年度汇总', normal_style),
                Paragraph(f"{report_data['total_income']:,.2f}", normal_style),
                Paragraph(f"{report_data['total_expense']:,.2f}", normal_style),
                Paragraph(f"{running_balance:,.2f}", normal_style),
                Paragraph(str(report_data['total_count']), normal_style)
            ])
        
        elif report_type == 'chart':
            # 图表分析报告
            chart_data = report_data.get('chart_data', {})
            
            # 添加统计摘要
            elements.append(Paragraph('统计摘要', title_style))
            
            summary_data = [
                ['项目', '数值'],
                ['总收入', f"{chart_data.get('total_income', 0):,.2f}"],
                ['总支出', f"{chart_data.get('total_expense', 0):,.2f}"],
                ['结余', f"{chart_data.get('balance', 0):,.2f}"],
                ['交易笔数', str(chart_data.get('transaction_count', 0))]
            ]
            
            summary_table = Table(summary_data, colWidths=[4*cm, 4*cm])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, -1), chinese_font)
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 20))
            
            # 添加月度数据表格（如果是年度分析）
            if chart_data.get('monthly_data'):
                elements.append(Paragraph('月度数据', title_style))
                monthly_table_data = [['月份', '收入', '支出', '结余', '交易笔数']]
                
                for month in range(1, 13):
                    month_data = chart_data['monthly_data'].get(str(month), {})
                    monthly_table_data.append([
                        f"{month}月",
                        f"{month_data.get('total_income', 0):,.2f}",
                        f"{month_data.get('total_expense', 0):,.2f}",
                        f"{(month_data.get('total_income', 0) - month_data.get('total_expense', 0)):,.2f}",
                        str(month_data.get('transaction_count', 0))
                    ])
                
                monthly_table = Table(monthly_table_data, colWidths=[2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 1.5*cm])
                monthly_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('ALIGN', (1, 1), (3, -1), 'RIGHT'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 0), (-1, -1), chinese_font)
                ]))
                elements.append(monthly_table)
        
        # 创建表格（仅适用于日报、月报、年报）
        if table_data:
            # 调整列宽，适应新的表头结构
            if report_type == 'daily' or report_type == 'monthly':
                # 日报表和月报表：使用新的7列结构
                # 调整列宽，确保能显示百万位数字，摘要和明细分类有足够宽度
                col_widths = [1.5*cm, 1.5*cm, 2.5*cm, 5*cm, 2.5*cm, 2.5*cm, 2.5*cm]
            else:
                # 年度报表：调整列宽，确保对齐
                col_widths = [2.5*cm, 3*cm, 3*cm, 3*cm, 2.5*cm]
            
            table = Table(table_data, colWidths=col_widths)
            
            # 表格样式
            if report_type == 'daily' or report_type == 'monthly':
                # 日报表和月报表样式
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # 表头水平居中
                    ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),  # 表头垂直居中
                    ('ALIGN', (4, 1), (6, -1), 'RIGHT'),  # 入账、出账、结余列右对齐
                    ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),  # 内容垂直居中
                    ('FONTNAME', (0, 0), (-1, 0), chinese_font),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.lightgrey, colors.white])
                ]))
            else:
                # 年度报表样式
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # 表头水平居中
                    ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),  # 表头垂直居中
                    ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # 月份列居中
                    ('ALIGN', (1, 1), (3, -1), 'RIGHT'),  # 入账总额、出账总额、结余列右对齐
                    ('ALIGN', (4, 1), (4, -1), 'RIGHT'),  # 交易笔数列右对齐
                    ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),  # 内容垂直居中
                    ('FONTNAME', (0, 0), (-1, 0), chinese_font),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.lightgrey, colors.white])
                ]))
            elements.append(table)
        
        # 生成PDF
        doc.build(elements)
        buffer.seek(0)
        
        # 返回PDF文件
        from flask import send_file
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'财务报表_{report_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # 初始化默认管理员用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('默认管理员用户已创建: username=admin, password=admin123')
    import os
    port = int(os.environ.get('PORT', 5000))
    
    app.run(debug=True, host='0.0.0.0', port=port)
