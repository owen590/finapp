import os
from flask import Flask
from config import Config
from models import db, Transaction, Loan, Distribution

def init_db():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    with app.app_context():
        data_dir = os.path.dirname(Config.DATABASE_PATH)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        db.create_all()
        print("数据库初始化完成！")
        print(f"数据库位置: {Config.DATABASE_PATH}")

if __name__ == '__main__':
    init_db()
