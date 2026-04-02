from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # 账户名称
    account_type = db.Column(db.String(50))  # 账户类型：银行/微信/支付宝/现金/其他
    initial_balance = db.Column(db.Float, default=0)  # 期初余额
    current_balance = db.Column(db.Float, default=0)  # 当前余额
    remark = db.Column(db.Text)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'account_type': self.account_type,
            'initial_balance': self.initial_balance,
            'current_balance': self.current_balance,
            'remark': self.remark,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 收支分类：入账/出账
    category = db.Column(db.String(100))  # 大类分类
    sub_category = db.Column(db.String(100))  # 明细分类
    description = db.Column(db.Text)  # 摘要
    amount = db.Column(db.Float, nullable=False)
    remark = db.Column(db.Text)  # 备注
    month = db.Column(db.Integer)
    year = db.Column(db.Integer)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))  # 账户
    bitable_record_id = db.Column(db.String(100))  # 飞书多维表格记录ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'type': self.type,
            'category': self.category,
            'sub_category': self.sub_category,
            'description': self.description,
            'amount': self.amount,
            'remark': self.remark,
            'month': self.month,
            'year': self.year,
            'account_id': self.account_id,
            'bitable_record_id': self.bitable_record_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Loan(db.Model):
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    lender = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='未归还')  # 已归还/未归还
    return_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'lender': self.lender,
            'amount': self.amount,
            'status': self.status,
            'return_date': self.return_date.strftime('%Y-%m-%d') if self.return_date else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Distribution(db.Model):
    __tablename__ = 'distributions'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    person = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'person': self.person,
            'amount': self.amount,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Capital(db.Model):
    __tablename__ = 'capital'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    investor = db.Column(db.String(100), nullable=False)  # 投资者
    amount = db.Column(db.Float, nullable=False)  # 投入金额
    description = db.Column(db.Text)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'investor': self.investor,
            'amount': self.amount,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='viewer')  # viewer: 可查看, editor: 可编辑
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
