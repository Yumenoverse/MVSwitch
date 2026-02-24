import customtkinter as ctk
import json
import logging
import threading
import os
from core.manager import MySQLServiceManager
from core.env_handler import EnvironmentHandler

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("MySQL Context Manager")
        self.root.geometry("1200x700")
        self.root.minsize(900, 500)
        
        # 初始化服务管理器和环境处理器
        self.service_manager = MySQLServiceManager()
        self.env_handler = EnvironmentHandler()
        
        # 加载配置
        self.config = self.load_config()
        
        # UI主题已在main.py中设置
        
        # 统一字体配置
        self.fonts = {
            "title": ctk.CTkFont(family="Microsoft YaHei UI", size=20, weight="bold"),
            "subtitle": ctk.CTkFont(family="Microsoft YaHei UI", size=16, weight="bold"),
            "body": ctk.CTkFont(family="Microsoft YaHei UI", size=14),
            "button": ctk.CTkFont(family="Microsoft YaHei UI", size=14),
            "small": ctk.CTkFont(family="Microsoft YaHei UI", size=12)
        }
        
        # 获取当前激活的环境
        self.current_env = self.env_handler.get_current_mysql_home()
        
        # 创建主布局
        self.create_layout()
        
        # 初始化日志
        self.setup_logging()
        
        # 刷新服务状态
        self.refresh_service_status()
    
    def load_config(self):
        """
        加载配置文件
        """
        try:
            # 使用绝对路径加载配置文件
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
            return {"mysql_versions": []}
    
    def create_layout(self):
        """
        创建主窗口布局
        """
        # 使用grid布局管理器替代pack，实现更灵活的响应式设计
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_columnconfigure(0, weight=0)
        self.root.grid_columnconfigure(1, weight=1)
        
        # 创建侧边栏
        self.sidebar = ctk.CTkFrame(self.root, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        # 侧边栏内容
        self.create_sidebar_content()
        
        # 创建主内容区
        self.main_content = ctk.CTkFrame(self.root, corner_radius=0)
        self.main_content.grid(row=0, column=1, sticky="nsew")
        
        # 主内容区布局
        self.create_main_content()
        
        # 创建底部日志栏
        self.create_log_panel()
    
    def create_sidebar_content(self):
        """
        创建侧边栏内容
        """
        # Logo (使用文字替代)
        logo_label = ctk.CTkLabel(self.sidebar, text="MySQL Context Manager", font=self.fonts["title"])
        logo_label.pack(pady=30, padx=20)
        
        # 服务状态总览标题
        status_label = ctk.CTkLabel(self.sidebar, text="服务状态总览", font=self.fonts["subtitle"])
        status_label.pack(pady=(20, 10), padx=20)
        
        # 服务状态列表
        self.status_frames = []
        for mysql_config in self.config["mysql_versions"]:
            status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            status_frame.pack(fill="x", padx=20, pady=5)
            
            # 检查是否为当前环境
            is_current = self.current_env == mysql_config["path"]
            font = ctk.CTkFont(family="Microsoft YaHei UI", size=14, weight="bold" if is_current else "normal")
            
            name_label = ctk.CTkLabel(status_frame, text=mysql_config["name"], font=font)
            name_label.pack(side="left")
            
            status_indicator = ctk.CTkLabel(status_frame, text="●", font=ctk.CTkFont(family="Microsoft YaHei UI", size=16))
            status_indicator.pack(side="right")
            
            self.status_frames.append((mysql_config["service_name"], status_indicator, name_label))
        
        # 添加MySQL版本按钮
        add_button = ctk.CTkButton(self.sidebar, text="添加MySQL版本", font=self.fonts["body"], command=self.open_edit_dialog)
        add_button.pack(pady=20, padx=20, fill="x")
    
    def create_main_content(self):
        """
        创建主内容区
        """
        # 使用grid布局确保主内容区能正确扩展
        self.main_content.grid_rowconfigure(0, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)
        
        # 创建滚动框架
        self.scrollable_frame = ctk.CTkScrollableFrame(self.main_content)
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # 创建版本卡片
        self.version_cards = []
        for i, mysql_config in enumerate(self.config["mysql_versions"]):
            card = self.create_version_card(mysql_config, i)
            self.version_cards.append(card)
    
    def create_version_card(self, mysql_config, index):
        """
        创建版本卡片
        """
        card_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10)
        card_frame.grid(row=index, column=0, sticky="nsew", pady=15, padx=10)
        card_frame.grid_columnconfigure(0, weight=1)
        
        # 卡片标题
        title_label = ctk.CTkLabel(card_frame, text=mysql_config["name"], font=self.fonts["subtitle"])
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 15))
        
        # 版本信息
        info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        info_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        
        # 路径信息
        info_frame.grid_columnconfigure(0, weight=0, minsize=80)
        info_frame.grid_columnconfigure(1, weight=0, minsize=80)
        info_frame.grid_columnconfigure(2, weight=1)
        
        version_label = ctk.CTkLabel(info_frame, text=f"版本: {mysql_config['version']}", font=self.fonts["body"])
        version_label.grid(row=0, column=0, padx=(0, 20), sticky="w")
        
        port_label = ctk.CTkLabel(info_frame, text=f"PORT: {mysql_config['port']}", font=self.fonts["body"])
        port_label.grid(row=0, column=1, padx=(0, 20), sticky="w")
        
        # 使用自动换行的标签显示路径信息
        path_label = ctk.CTkLabel(info_frame, text=f"路径: {mysql_config['path']}", 
                                  font=self.fonts["body"], wraplength=500, anchor="w")
        path_label.grid(row=0, column=2, sticky="ew", padx=(0, 10))
        
        # 服务控制按钮
        control_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        control_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(15, 20))
        
        # 添加一个权重列，将按钮推到右边
        control_frame.grid_columnconfigure(0, weight=1)
        
        # 添加控制按钮
        start_button = ctk.CTkButton(control_frame, text="启动服务", font=self.fonts["button"], 
                                    command=lambda: threading.Thread(target=self.perform_service_action,
                                                                     args=(mysql_config["service_name"], 
                                                                           self.service_manager.start_service, 
                                                                           start_button)).start())
        start_button.grid(row=0, column=1, padx=(0, 10))
        
        stop_button = ctk.CTkButton(control_frame, text="停止服务", font=self.fonts["button"], 
                                   command=lambda: threading.Thread(target=self.perform_service_action,
                                                                    args=(mysql_config["service_name"], 
                                                                          self.service_manager.stop_service, 
                                                                          stop_button)).start())
        stop_button.grid(row=0, column=2, padx=(0, 10))
        
        restart_button = ctk.CTkButton(control_frame, text="重启服务", font=self.fonts["button"], 
                                      command=lambda: threading.Thread(target=self.perform_service_action,
                                                                       args=(mysql_config["service_name"], 
                                                                             self.service_manager.restart_service, 
                                                                             restart_button)).start())
        restart_button.grid(row=0, column=3, padx=(0, 10))
        
        # 编辑按钮
        edit_button = ctk.CTkButton(control_frame, text="编辑", font=self.fonts["button"], 
                                   command=lambda: self.open_edit_dialog(mysql_config, index))
        edit_button.grid(row=0, column=4, padx=(0, 10))
        
        # 删除按钮
        delete_button = ctk.CTkButton(control_frame, text="删除", font=self.fonts["button"], 
                                     fg_color="#D32F2F", hover_color="#B71C1C",
                                     command=lambda: self.delete_version(mysql_config, index))
        delete_button.grid(row=0, column=5)
        
        # 返回创建的卡片帧
        return card_frame
    
    def create_log_panel(self):
        """
        创建底部日志面板
        """
        # 使用grid布局将日志面板放置在主内容区下方
        log_frame = ctk.CTkFrame(self.root, corner_radius=0)
        log_frame.grid(row=1, column=1, sticky="ew", padx=0, pady=0)
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        # 日志标题栏
        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 5))
        log_header.grid_columnconfigure(0, weight=1)
        
        log_title = ctk.CTkLabel(log_header, text="操作日志", font=self.fonts["subtitle"])
        log_title.grid(row=0, column=0, sticky="w")
        
        # 清空日志按钮
        clear_log_button = ctk.CTkButton(log_header, text="清空", width=60, font=self.fonts["small"], command=self.clear_logs)
        clear_log_button.grid(row=0, column=1, sticky="e")
        
        # 日志文本框
        self.log_text = ctk.CTkTextbox(log_frame, height=100)
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.log_text.configure(state="disabled")
    
    def setup_logging(self):
        """
        设置日志系统
        """
        # 创建日志处理器
        class TextboxHandler(logging.Handler):
            def __init__(self, textbox):
                super().__init__()
                self.textbox = textbox
                self.setFormatter(logging.Formatter("%(asctime)s - %(message)s", datefmt="%H:%M:%S"))
            
            def emit(self, record):
                msg = self.format(record)
                self.textbox.configure(state="normal")
                self.textbox.insert("end", msg + "\n")
                self.textbox.see("end")
                self.textbox.configure(state="disabled")
        
        # 设置日志级别
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # 添加文本框处理器
        logger.addHandler(TextboxHandler(self.log_text))
    
    def clear_logs(self):
        """
        清空日志
        """
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
    
    def perform_service_action(self, service_name, action_func, button=None):
        """
        执行服务操作并处理结果
        :param service_name: 服务名称
        :param action_func: 服务操作函数
        :param button: 触发操作的按钮，用于状态显示
        """
        # 如果提供了按钮，禁用它并更改文本
        if button:
            original_text = button.cget("text")
            button.configure(text="处理中...", state="disabled")
        
        try:
            # 执行服务操作
            # 先找到对应的配置，获取版本号
            version = None
            for config in self.config["mysql_versions"]:
                if config["service_name"] == service_name:
                    version = config["version"]
                    break
            
            if version:
                # 如果有版本号，传递给action_func
                success, message = action_func(service_name, version)
            else:
                # 兼容旧版调用方式
                success, message = action_func(service_name)
            
            # 记录日志
            logging.info(message)
            
            # 更新服务状态
            self.refresh_service_status()
        except Exception as e:
            success = False
            message = f"操作失败: {str(e)}"
            logging.error(message)
        finally:
            # 如果提供了按钮，恢复原始状态
            if button:
                button.configure(text=original_text, state="normal")

    def refresh_service_status(self):
        """
        刷新服务状态指示器
        """
        for service_name, status_indicator, name_label in self.status_frames:
            # 获取服务状态
            status = self.service_manager.get_service_status(service_name)
            
            # 根据状态设置不同的颜色
            if status == "running":
                status_indicator.configure(text_color="green")
            elif status == "stopped":
                status_indicator.configure(text_color="red")
            elif status == "paused":
                status_indicator.configure(text_color="orange")
            else:
                status_indicator.configure(text_color="gray")
    
    def open_edit_dialog(self, mysql_config=None, index=None):
        """
        打开编辑对话框
        :param mysql_config: MySQL配置字典，None表示添加新配置
        :param index: 配置索引，None表示添加新配置
        """
        # 创建对话框
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("编辑MySQL配置" if mysql_config else "添加MySQL配置")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        
        # 直接设置居中位置
        width, height = 500, 400
        x = int((dialog.winfo_screenwidth()/2) - (width/2))
        y = int((dialog.winfo_screenheight()/2) - (height/2))
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # 输入框标签配置
        label_width = 120
        entry_width = 300
        
        # 名称
        name_label = ctk.CTkLabel(dialog, text="名称:", width=label_width, font=self.fonts["body"])
        name_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        self.name_entry = ctk.CTkEntry(dialog, width=entry_width, font=self.fonts["body"])
        self.name_entry.grid(row=0, column=1, padx=20, pady=(20, 10))
        
        # 版本 - 标签显示
        version_label = ctk.CTkLabel(dialog, text="版本:", width=label_width, font=self.fonts["body"])
        version_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.version_label = ctk.CTkLabel(dialog, text="", width=entry_width, font=self.fonts["body"])
        self.version_label.grid(row=1, column=1, padx=20, pady=10, sticky="w")
        
        # 服务名 - 标签显示
        service_name_label = ctk.CTkLabel(dialog, text="服务名:", width=label_width, font=self.fonts["body"])
        service_name_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.service_name_label = ctk.CTkLabel(dialog, text="", width=entry_width, font=self.fonts["body"])
        self.service_name_label.grid(row=2, column=1, padx=20, pady=10, sticky="w")
        
        # 路径
        path_label = ctk.CTkLabel(dialog, text="路径:", width=label_width, font=self.fonts["body"])
        path_label.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.path_entry = ctk.CTkEntry(dialog, width=entry_width, font=self.fonts["body"])
        self.path_entry.grid(row=3, column=1, padx=20, pady=10)
        
        # 添加路径输入变化事件监听
        self.path_entry.bind("<KeyRelease>", lambda event: self.auto_parse_path(dialog))
        self.path_entry.bind("<FocusOut>", lambda event: self.auto_parse_path(dialog))
        
        # 端口
        port_label = ctk.CTkLabel(dialog, text="PORT:", width=label_width, font=self.fonts["body"])
        port_label.grid(row=4, column=0, padx=20, pady=10, sticky="w")
        self.port_entry = ctk.CTkEntry(dialog, width=entry_width, font=self.fonts["body"])
        self.port_entry.grid(row=4, column=1, padx=20, pady=10)
        
        # 如果是编辑模式，填充现有数据
        if mysql_config:
            self.name_entry.insert(0, mysql_config["name"])
            # 设置版本和服务名标签文本
            self.version_label.configure(text=mysql_config["version"])
            self.service_name_label.configure(text=mysql_config["service_name"])
            self.path_entry.insert(0, mysql_config["path"])
            self.port_entry.insert(0, mysql_config["port"])
        
        # 按钮框架
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 20))
        button_frame.grid_columnconfigure(0, weight=1)
        
        # 保存按钮
        save_button = ctk.CTkButton(button_frame, text="保存", font=self.fonts["button"], 
                                   command=lambda: self.save_mysql_config(dialog, mysql_config, index))
        save_button.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="e")
        
        # 取消按钮
        cancel_button = ctk.CTkButton(button_frame, text="取消", font=self.fonts["button"], 
                                     command=lambda: dialog.destroy())
        cancel_button.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="w")
        
        # 聚焦对话框
        dialog.focus_force()
        
        # 刷新服务状态
        self.refresh_service_status()
    
    def auto_parse_path(self, dialog):
        """
        自动解析路径，提取版本号并生成服务名
        :param dialog: 对话框实例
        """
        # 清除可能存在的错误消息
        for widget in dialog.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text_color") == "red":
                widget.destroy()
        
        # 获取路径
        path = self.path_entry.get().strip()
        if not path:
            return
        
        # 从路径中提取版本号
        version = self.env_handler.extract_version_from_path(path)
        if version:
            # 生成服务名
            service_name = self.env_handler.generate_service_name(version)
            
            # 更新版本号和服务名标签
            self.version_label.configure(text=version)
            
            if service_name:
                self.service_name_label.configure(text=service_name)
            else:
                self.service_name_label.configure(text="")
        else:
            # 显示版本解析错误
            error_label = ctk.CTkLabel(dialog, text="无法从路径中识别MySQL版本号", text_color="red", font=self.fonts["body"])
            error_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10))
            
            # 清空版本号和服务名标签
            self.version_label.configure(text="")
            self.service_name_label.configure(text="")
        
    def save_mysql_config(self, dialog, mysql_config, index):
        """
        保存MySQL配置
        :param dialog: 对话框实例
        :param mysql_config: 原始配置
        :param index: 配置索引
        """
        # 获取输入值
        name = self.name_entry.get().strip()
        path = self.path_entry.get().strip()
        port = self.port_entry.get().strip()
        
        # 清除可能存在的错误消息
        for widget in dialog.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text_color") == "red":
                widget.destroy()
        
        # 从路径中重新提取版本号和生成服务名（确保最新）
        version = self.env_handler.extract_version_from_path(path)
        if not version:
            # 显示版本解析错误
            error_label = ctk.CTkLabel(dialog, text="无法从路径中识别MySQL版本号，请检查路径格式", text_color="red", font=self.fonts["body"])
            error_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10))
            return
        
        # 生成服务名
        service_name = self.env_handler.generate_service_name(version)
        if not service_name:
            # 显示服务名生成错误
            error_label = ctk.CTkLabel(dialog, text="无法根据版本号生成服务名", text_color="red", font=self.fonts["body"])
            error_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10))
            return
        
        # 验证输入
        if not all([name, path, port]):
            # 显示错误消息
            error_label = ctk.CTkLabel(dialog, text="请填写所有必填字段", text_color="red", font=self.fonts["body"])
            error_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10))
            return
        
        # 验证端口号
        try:
            port_num = int(port)
            if port_num < 1 or port_num > 65535:
                raise ValueError("端口号必须在1-65535之间")
        except ValueError as e:
            error_label = ctk.CTkLabel(dialog, text=f"端口号无效: {str(e)}", text_color="red", font=self.fonts["body"])
            error_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10))
            return
        
        # 验证路径是否存在
        import os
        if not os.path.exists(path):
            error_label = ctk.CTkLabel(dialog, text="MySQL安装路径不存在", text_color="red", font=self.fonts["body"])
            error_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10))
            return
        
        # 验证是否包含mysqld.exe
        mysqld_path = os.path.join(path, "bin", "mysqld.exe")
        if not os.path.exists(mysqld_path):
            error_label = ctk.CTkLabel(dialog, text="该路径下未找到mysqld.exe", text_color="red", font=self.fonts["body"])
            error_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10))
            return
        
        # 更新显示的版本号和服务名标签（确保保存的是最新解析的结果）
        self.version_label.configure(text=version)
        self.service_name_label.configure(text=service_name)
        
        # 创建新配置
        new_config = {
            "name": name,
            "version": version,
            "service_name": service_name,
            "path": path,
            "port": port_num
        }
        
        # 更新配置
        if mysql_config and index is not None:
            # 编辑现有配置
            self.config["mysql_versions"][index] = new_config
        else:
            # 添加新配置
            self.config["mysql_versions"].append(new_config)
        
        # 保存到文件
        try:
            # 使用绝对路径保存配置文件
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            # 保存成功后，设置对应的版本变量
            self.env_handler.set_version_specific_var(version, path)
            
            # 刷新UI
            self.refresh_ui()
            
            # 关闭对话框
            dialog.destroy()
        except Exception as e:
            # 显示错误消息
            error_label = ctk.CTkLabel(dialog, text=f"保存失败: {e}", text_color="red", font=self.fonts["body"])
            error_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10))
    
    def delete_version(self, mysql_config, index):
        """
        删除MySQL版本配置
        :param mysql_config: MySQL配置
        :param index: 配置索引
        """
        # 确认删除
        confirm_dialog = ctk.CTkToplevel(self.root)
        confirm_dialog.title("确认删除")
        confirm_dialog.resizable(False, False)
        confirm_dialog.attributes("-topmost", True)
        
        # 直接设置居中位置
        width, height = 300, 200
        x = int((confirm_dialog.winfo_screenwidth()/2) - (width/2))
        y = int((confirm_dialog.winfo_screenheight()/2) - (height/2))
        confirm_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # 确认消息
        confirm_label = ctk.CTkLabel(confirm_dialog, text=f"确定要删除 {mysql_config['name']} 吗？", 
                                   font=self.fonts["body"])
        confirm_label.pack(pady=30, padx=20)
        
        # 按钮框架
        button_frame = ctk.CTkFrame(confirm_dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)
        button_frame.grid_columnconfigure(0, weight=1)
        
        # 确认按钮
        confirm_button = ctk.CTkButton(button_frame, text="确认", font=self.fonts["button"], 
                                      fg_color="#D32F2F", hover_color="#B71C1C",
                                      command=lambda: self.confirm_delete(confirm_dialog, mysql_config, index))
        confirm_button.grid(row=0, column=0, padx=(0, 10), sticky="e")
        
        # 取消按钮
        cancel_button = ctk.CTkButton(button_frame, text="取消", font=self.fonts["button"], 
                                     command=lambda: confirm_dialog.destroy())
        cancel_button.grid(row=0, column=1, padx=(10, 0), sticky="w")
    
    def confirm_delete(self, dialog, mysql_config, index):
        """
        确认删除MySQL配置
        :param dialog: 确认对话框
        :param mysql_config: MySQL配置
        :param index: 配置索引
        """
        # 删除配置
        self.config["mysql_versions"].pop(index)
        
        # 保存到文件
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            # 刷新UI
            self.refresh_ui()
            
            # 关闭对话框
            dialog.destroy()
        except Exception as e:
            # 记录错误
            logging.error(f"删除配置失败: {e}")
            
            # 关闭对话框
            dialog.destroy()
    
    def refresh_ui(self):
        """
        刷新UI界面
        """
        # 清除现有版本卡片
        for card in self.version_cards:
            card.destroy()
        
        # 重新创建版本卡片
        self.version_cards = []
        for i, mysql_config in enumerate(self.config["mysql_versions"]):
            card = self.create_version_card(mysql_config, i)
            self.version_cards.append(card)
        
        # 刷新服务状态
        self.refresh_service_status()
        
        # 刷新侧边栏
        for widget in self.sidebar.winfo_children():
            widget.destroy()
        
        # 重新创建侧边栏内容
        self.create_sidebar_content()