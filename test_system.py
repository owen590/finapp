import unittest
import json
import tempfile
import os
from app import app, db
from models import User, Transaction
from datetime import date, datetime

class TestFinanceSystem(unittest.TestCase):
    def setUp(self):
        # 创建测试客户端
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        
        # 初始化数据库
        with app.app_context():
            db.create_all()
            # 创建测试用户
            test_user = User(username='testuser', role='admin')
            test_user.set_password('test123')
            db.session.add(test_user)
            db.session.commit()
            
            # 登录
            self.client.post('/login', data={
                'username': 'testuser',
                'password': 'test123'
            })
    
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_daily_report_api(self):
        """测试日报表API"""
        # 添加测试数据
        with app.app_context():
            # 上期交易
            prev_transaction = Transaction(
                date=date(2026, 3, 14),
                type='入账',
                category='销售收入',
                description='测试收入',
                amount=1000.00,
                remark='测试'
            )
            # 当日交易
            today_transaction = Transaction(
                date=date(2026, 3, 15),
                type='出账',
                category='办公费用',
                description='测试支出',
                amount=200.00,
                remark='测试'
            )
            db.session.add_all([prev_transaction, today_transaction])
            db.session.commit()
        
        # 测试日报表API
        response = self.client.get('/api/reports?type=daily&date=2026-03-15')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['type'], 'daily')
        self.assertEqual(data['date'], '2026-03-15')
        self.assertEqual(data['opening_balance'], 1000.00)
        self.assertEqual(data['total_income'], 0.00)
        self.assertEqual(data['total_expense'], 200.00)
        self.assertEqual(data['balance'], -200.00)
    
    def test_monthly_report_api(self):
        """测试月报表API"""
        # 添加测试数据
        with app.app_context():
            # 上月交易
            prev_transaction = Transaction(
                date=date(2026, 2, 28),
                type='入账',
                category='销售收入',
                description='测试收入',
                amount=5000.00,
                remark='测试'
            )
            # 当月交易
            current_transaction = Transaction(
                date=date(2026, 3, 1),
                type='出账',
                category='办公费用',
                description='测试支出',
                amount=500.00,
                remark='测试'
            )
            db.session.add_all([prev_transaction, current_transaction])
            db.session.commit()
        
        # 测试月报表API
        response = self.client.get('/api/reports?type=monthly&year=2026&month=3')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['type'], 'monthly')
        self.assertEqual(data['year'], 2026)
        self.assertEqual(data['month'], 3)
        self.assertEqual(data['opening_balance'], 5000.00)
        self.assertEqual(data['total_income'], 0.00)
        self.assertEqual(data['total_expense'], 500.00)
        self.assertEqual(data['balance'], -500.00)
    
    def test_yearly_report_api(self):
        """测试年度报表API"""
        # 添加测试数据
        with app.app_context():
            # 去年交易
            prev_transaction = Transaction(
                date=date(2025, 12, 31),
                type='入账',
                category='销售收入',
                description='测试收入',
                amount=10000.00,
                remark='测试'
            )
            # 今年交易
            current_transaction = Transaction(
                date=date(2026, 1, 1),
                type='出账',
                category='办公费用',
                description='测试支出',
                amount=1000.00,
                remark='测试'
            )
            db.session.add_all([prev_transaction, current_transaction])
            db.session.commit()
        
        # 测试年度报表API
        response = self.client.get('/api/reports?type=yearly&year=2026')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['type'], 'yearly')
        self.assertEqual(data['year'], 2026)
        self.assertEqual(data['opening_balance'], 10000.00)
        self.assertEqual(data['total_income'], 0.00)
        self.assertEqual(data['total_expense'], 1000.00)
        self.assertEqual(data['balance'], -1000.00)
    
    def test_transaction_creation(self):
        """测试交易创建"""
        response = self.client.post('/api/transactions', data=json.dumps({
            'date': '2026-03-15',
            'type': '入账',
            'category': '销售收入',
            'description': '测试交易',
            'amount': 500.00,
            'remark': '测试'
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('id', data)
    
    def test_pagination_api(self):
        """测试分页API"""
        # 添加测试数据
        with app.app_context():
            for i in range(15):
                transaction = Transaction(
                    date=date(2026, 3, 15),
                    type='入账' if i % 2 == 0 else '出账',
                    category='测试分类',
                    description=f'测试交易 {i}',
                    amount=100.00,
                    remark='测试'
                )
                db.session.add(transaction)
            db.session.commit()
        
        # 测试分页API
        response = self.client.get('/api/transactions?page=1&per_page=10')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['current_page'], 1)
        self.assertEqual(len(data['transactions']), 10)
        self.assertEqual(data['pages'], 2)

if __name__ == '__main__':
    unittest.main()
