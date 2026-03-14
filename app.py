from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from config import Config
from models import Transaction, Loan, Distribution, Capital, db
from utils import import_from_excel, import_from_csv
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

db.init_app(app)

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

@app.route('/export')
def export_page():
    return render_template('export.html')

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
