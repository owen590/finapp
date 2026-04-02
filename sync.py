"""
飞书多维表格同步模块
使用原生requests调用飞书Open API
"""
import requests
import time

# 恒驰泵业多维表格 - 使用个人账本结构
FEISHU_APP_TOKEN = "CV9bbls3EarizcshYgecYLiKnuh"
FEISHU_TABLE_TRANSACTIONS = "tblP3eLTqlj8PwNB"   # 交易记录
FEISHU_TABLE_ACCOUNTS = "tblNma25DEHywitS"        # 账户资产

# 飞书开放平台应用凭证
FEISHU_APP_ID = "cli_a9397430b178dceb"
FEISHU_APP_SECRET = "QkE1tSU3QzVT3U3RuQyFGgqDT4b8VvZe"

# 缓存access_token
_cached_token = None
_token_expires_at = 0


def get_access_token():
    """获取飞书access_token"""
    global _cached_token, _token_expires_at
    
    if _cached_token and time.time() < _token_expires_at - 60:
        return _cached_token
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    
    resp = requests.post(url, headers=headers, json=data, timeout=10)
    resp.raise_for_status()
    result = resp.json()
    
    if result.get("code") != 0:
        raise Exception(f"获取token失败: {result}")
    
    _cached_token = result["tenant_access_token"]
    _token_expires_at = time.time() + result.get("expire", 7200)
    return _cached_token


def api_call(method, path, params=None, data=None, token=None):
    """通用飞书API调用"""
    if token is None:
        token = get_access_token()
    
    url = f"https://open.feishu.cn/open-apis{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    resp = requests.request(method, url, headers=headers, params=params, json=data, timeout=15)
    resp.raise_for_status()
    result = resp.json()
    
    if result.get("code") != 0:
        raise Exception(f"API调用失败 {path}: {result}")
    
    return result.get("data", {})


def sync_transaction_to_feishu(transaction_dict):
    """
    同步交易记录到飞书多维表格
    transaction_dict包含: date, type, category, description, amount, remark, account_name
    返回飞书记录ID
    """
    # 构建字段数据
    type_map = {"入账": "收入", "出账": "支出"}
    fields = {
        "交易时间": int(time.mktime(time.strptime(transaction_dict["date"], "%Y-%m-%d")) * 1000),
        "收支类型": type_map.get(transaction_dict["type"], "支出"),
        "交易金额": float(transaction_dict["amount"]),
        "一级分类": transaction_dict.get("category", ""),
        "二级分类": transaction_dict.get("sub_category", ""),
        "交易商户": transaction_dict.get("merchant", ""),
        "资金账户": transaction_dict.get("account_name", ""),
        "备注": transaction_dict.get("remark", ""),
    }
    
    data = api_call("POST", f"/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_TRANSACTIONS}/records", data={"fields": fields})
    record_id = data.get("record", {}).get("record_id")
    return record_id


def update_feishu_transaction_record(record_id, transaction_dict):
    """更新飞书交易记录"""
    type_map = {"入账": "收入", "出账": "支出"}
    fields = {
        "交易时间": int(time.mktime(time.strptime(transaction_dict["date"], "%Y-%m-%d")) * 1000),
        "收支类型": type_map.get(transaction_dict["type"], "支出"),
        "交易金额": float(transaction_dict["amount"]),
        "一级分类": transaction_dict.get("category", ""),
        "二级分类": transaction_dict.get("sub_category", ""),
        "交易商户": transaction_dict.get("merchant", ""),
        "资金账户": transaction_dict.get("account_name", ""),
        "备注": transaction_dict.get("remark", ""),
    }
    
    api_call("PUT", f"/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_TRANSACTIONS}/records/{record_id}", data={"fields": fields})


def delete_feishu_transaction_record(record_id):
    """删除飞书交易记录"""
    try:
        api_call("DELETE", f"/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_TRANSACTIONS}/records/{record_id}")
    except Exception as e:
        print(f"删除飞书记录失败: {e}")


def sync_account_to_feishu(account_dict):
    """
    同步账户到飞书多维表格
    account_dict包含: name, account_type, initial_balance, current_balance, remark
    返回飞书记录ID
    """
    fields = {
        "账户名称": account_dict["name"],
        "账户类型": account_dict.get("account_type", ""),
        "期初余额": float(account_dict.get("initial_balance", 0)),
        "当前余额": float(account_dict.get("current_balance", 0)),
        "备注": account_dict.get("remark", ""),
    }
    
    data = api_call("POST", f"/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ACCOUNTS}/records", data={"fields": fields})
    record_id = data.get("record", {}).get("record_id")
    return record_id


def update_feishu_account_record(record_id, account_dict):
    """更新飞书账户记录"""
    fields = {
        "账户名称": account_dict["name"],
        "账户类型": account_dict.get("account_type", ""),
        "期初余额": float(account_dict.get("initial_balance", 0)),
        "当前余额": float(account_dict.get("current_balance", 0)),
        "备注": account_dict.get("remark", ""),
    }
    
    api_call("PUT", f"/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ACCOUNTS}/records/{record_id}", data={"fields": fields})
