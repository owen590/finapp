from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from config import Config
from models import Transaction, Loan, Distribution, Capital, User, db
from utils import import_from_excel, import_from_csv
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ledger')
def ledger():
    return render_template('ledger.html')

@app.route('/monthly')
def monthly():
    return render_template('monthly.html')

@app.route('/import')
def import_page():
    return render_template('import.html')

@app.route('/entry')
def entry():
    return render_template('entry.html')

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/export')
def export():
    return render_template('export.html')

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
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
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已注销', 'success')
    return redirect(url_for('login'))

@app.route('/api/export', methods=['GET'])
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

@app.route('/api/transactions', methods=['GET'])
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

@app.route('/api/transactions', methods=['POST'])
def create_transaction():
    data = request.json
    
    date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    
    transaction = Transaction(
        date=date,
        type=data['type'],
        category=data.get('category', ''),
        amount=float(data['amount']),
        description=data.get('description', ''),
        remark=data.get('remark', ''),
        month=date.month,
        year=date.year
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify(transaction.to_dict()), 201

@app.route('/api/transactions/<int:id>', methods=['GET'])
def get_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    return jsonify(transaction.to_dict())

@app.route('/api/transactions/<int:id>', methods=['PUT'])
def update_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    data = request.json
    
    if 'date' in data:
        date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        transaction.date = date
        transaction.month = date.month
        transaction.year = date.year
    
    if 'type' in data:
        transaction.type = data['type']
    if 'category' in data:
        transaction.category = data['category']
    if 'amount' in data:
        transaction.amount = float(data['amount'])
    if 'description' in data:
        transaction.description = data['description']
    if 'remark' in data:
        transaction.remark = data['remark']
    
    db.session.commit()
    
    return jsonify(transaction.to_dict())

@app.route('/api/transactions/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})

@app.route('/api/distributions', methods=['GET'])
def get_distributions():
    distributions = Distribution.query.order_by(Distribution.date.desc()).all()
    return jsonify([d.to_dict() for d in distributions])

@app.route('/api/distributions', methods=['POST'])
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

@app.route('/api/loans', methods=['GET'])
def get_loans():
    loans = Loan.query.order_by(Loan.date.desc()).all()
    return jsonify([l.to_dict() for l in loans])

@app.route('/api/loans', methods=['POST'])
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

@app.route('/api/loans/<int:id>', methods=['PUT'])
def update_loan(id):
    loan = Loan.query.get_or_404(id)
    data = request.json
    
    if 'status' in data:
        loan.status = data['status']
    if 'return_date' in data and data['return_date']:
        loan.return_date = datetime.strptime(data['return_date'], '%Y-%m-%d').date()
    
    db.session.commit()
    
    return jsonify(loan.to_dict())

@app.route('/api/loans/<int:id>', methods=['DELETE'])
def delete_loan(id):
    loan = Loan.query.get_or_404(id)
    db.session.delete(loan)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})

@app.route('/api/capital', methods=['GET'])
def get_capital():
    capital = Capital.query.order_by(Capital.date.desc()).all()
    return jsonify([c.to_dict() for c in capital])

@app.route('/api/capital', methods=['POST'])
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

@app.route('/api/capital/<int:id>', methods=['PUT'])
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

@app.route('/api/capital/<int:id>', methods=['DELETE'])
def delete_capital(id):
    capital = Capital.query.get_or_404(id)
    db.session.delete(capital)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})

@app.route('/api/statistics', methods=['GET'])
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

@app.route('/api/import', methods=['POST'])
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
@app.route('/api/reports', methods=['GET'])
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
@app.route('/api/export-pdf', methods=['POST'])
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
            # 尝试使用系统字体
            font_path = "C:\\Windows\\Fonts\\simsun.ttc"  # 宋体
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('SimSun', font_path))
                chinese_font = 'SimSun'
            else:
                # 如果没有系统字体，使用reportlab默认字体
                chinese_font = 'Helvetica'
        except:
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
        
        # 标题
        if report_type == 'daily':
            title = f"日报表 - {report_data['date']}"
        elif report_type == 'monthly':
            title = f"月报表 - {report_data['year']}年{report_data['month']}月"
        elif report_type == 'yearly':
            title = f"年度报表 - {report_data['year']}年"
        
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
        
        # 创建表格
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
    app.run(debug=True, host='0.0.0.0', port=5000)
