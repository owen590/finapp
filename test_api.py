import requests

# 测试交易API
url = 'http://localhost:5000/api/transactions'

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print(f"总交易数: {data['total']}")
    print(f"当前页: {data['current_page']}")
    print(f"总页数: {data['pages']}")
    
    # 打印前5条交易
    print("\n前5条交易:")
    for i, transaction in enumerate(data['transactions'][:5]):
        print(f"交易 {i+1}:")
        print(f"  ID: {transaction['id']}")
        print(f"  日期: {transaction['date']}")
        print(f"  类型: {transaction['type']}")
        print(f"  分类: {transaction['category']}")
        print(f"  摘要: {transaction['description']}")
        print(f"  金额: {transaction['amount']}")
        print(f"  备注: {transaction['remark']}")
        print()
else:
    print(f"API请求失败: {response.status_code}")
    print(response.text)
