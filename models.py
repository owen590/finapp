from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 收支分类：入账/出账
    category = db.Column(db.String(100))  # 明细分类
    description = db.Column(db.Text)  # 摘要
    amount = db.Column(db.Float, nullable=False)
    remark = db.Column(db.Text)  # 备注
    month = db.Column(db.Integer)
    year = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'type': self.type,
            'category': self.category,
            'description': self.description,
            'amount': self.amount,
            'remark': self.remark,
            'month': self.month,
            'year': self.year,
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
