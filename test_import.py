from utils import safe_float

# 测试 safe_float 函数
test_cases = [
    ('1000', 1000.0),
    ('1000.50', 1000.5),
    (1000, 1000.0),
    (1000.5, 1000.5),
    ('天天五金店', 0),
    ('abc', 0),
    (None, 0),
    ('', 0),
    ('  ', 0),
]

print("测试 safe_float 函数:")
print("-" * 50)

for input_val, expected in test_cases:
    result = safe_float(input_val)
    status = "✓" if result == expected else "✗"
    print(f"{status} 输入: {repr(input_val)} → 输出: {result} (期望: {expected})")

print("-" * 50)
print("测试完成！")
