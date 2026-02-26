import customtkinter as ctk
import json
import logging
import threading
import os
from core.manager import MVSwitchServiceManager
from core.env_handler import EnvironmentHandler

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("MVSwitch")
        self.root.geometry("1100x700")
        self.root.minsize(900, 500)
        
        # 初始化服务管理器和环境处理器
        self.service_manager = MVSwitchServiceManager()
        self.env_handler = EnvironmentHandler()
        
        # 加载配置
        self.config = self.load_config()
        
        # UI主题已在main.py中设置
        
        # 统一字体配置
        self.fonts = {
            "title": ctk.CTkFont(family="Microsoft YaHei UI", size=23),
            "subtitle": ctk.CTkFont(family="Microsoft YaHei UI", size=18),
            "body": ctk.CTkFont(family="Microsoft YaHei UI", size=14),
            "button": ctk.CTkFont(family="Microsoft YaHei UI", size=14),
            "small": ctk.CTkFont(family="Microsoft YaHei UI", size=12)
        }
        
        # 获取当前激活的环境
        self.current_env = self.env_handler.get_current_mysql_home()
        
        # 初始化调整大小相关变量
        self.start_y = 0
        self.window_height = 0
        self.sash_y = 0
        
        # 创建主布局
        self.create_layout()
        
        # 初始化日志
        self.setup_logging()
        
        # 刷新服务状态
        self.refresh_service_status()
    
    def get_config_path(self):
        """
        获取配置文件的绝对路径
        """
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
    
    def load_config(self):
        """
        加载配置文件
        """
        try:
            # 使用绝对路径加载配置文件
            config_path = self.get_config_path()
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
        # 使用整数权重，乘以100以获得更精细的调整
        self.root.grid_rowconfigure(0, weight=300)  # 主内容区初始权重
        self.root.grid_rowconfigure(1, weight=0)    # 分割条权重为0
        self.root.grid_rowconfigure(2, weight=100)  # 日志面板初始权重
        self.root.grid_columnconfigure(0, weight=0)
        self.root.grid_columnconfigure(1, weight=1)
        
        # 创建侧边栏
        self.sidebar = ctk.CTkFrame(self.root, width=250, corner_radius=0, fg_color="#F3F3F3")
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")
        
        # 侧边栏内容
        self.create_sidebar_content()
        
        # 创建主内容区
        self.main_content = ctk.CTkFrame(self.root, corner_radius=0, fg_color="#EAEAEA")
        self.main_content.grid(row=0, column=1, sticky="nsew")
        
        # 主内容区布局
        self.create_main_content()
        
        # 创建可拖动的分割条
        self.sash = ctk.CTkFrame(self.root, height=5, fg_color="#CCCCCC")
        self.sash.grid(row=1, column=1, sticky="ew")
        # 绑定鼠标事件
        self.sash.bind("<Button-1>", self.start_resize)
        self.sash.bind("<B1-Motion>", self.resize)
        
        # 创建底部日志栏
        self.log_frame = None
        self.create_log_panel()
        
        # 初始化权重设置（使用整数，*100）
        self.main_content_weight = 300
        self.log_panel_weight = 100
        self.min_log_weight = 50   # 最小日志面板权重
        self.max_log_weight = 500  # 最大日志面板权重
    
    def create_sidebar_content(self):
        """
        创建侧边栏内容
        """
        # Logo (使用文字替代)
        logo_label = ctk.CTkLabel(self.sidebar, text="MVSwitch", font=self.fonts["title"])
        logo_label.pack(pady=30, padx=20)
        
        # 服务状态总览标题
        status_label = ctk.CTkLabel(self.sidebar, text="服务状态总览", font=self.fonts["subtitle"])
        status_label.pack(pady=(20, 10), padx=20)
        
        # 服务状态列表
        self.status_frames = []
        for mysql_config in self.config["mysql_versions"]:
            status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            status_frame.pack(fill="x", padx=20, pady=5)
            
            font = ctk.CTkFont(family="Microsoft YaHei UI", size=14, weight="normal")
            
            name_label = ctk.CTkLabel(status_frame, text=mysql_config["name"], font=font)
            name_label.pack(side="left")
            
            status_indicator = ctk.CTkLabel(status_frame, text="●", font=ctk.CTkFont(family="Microsoft YaHei UI", size=16))
            status_indicator.pack(side="right")
            
            self.status_frames.append((mysql_config["service_name"], status_indicator, name_label))
        
        # 添加MySQL版本按钮
        add_button = ctk.CTkButton(self.sidebar, text="添加 MySQL 版本", font=self.fonts["body"], text_color="#FFFFFF", command=self.open_edit_dialog)
        add_button.pack(pady=20, padx=20, fill="x")
    
    def create_main_content(self):
        """
        创建主内容区
        """
        # 使用grid布局确保主内容区能正确扩展
        self.main_content.grid_rowconfigure(0, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)
        
        # 创建滚动框架
        self.scrollable_frame = ctk.CTkScrollableFrame(self.main_content, fg_color="#EAEAEA")
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
        # 创建版本卡片
        card_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10, fg_color="#FDFDFD")
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
        start_button = ctk.CTkButton(control_frame, text="启动服务", font=self.fonts["button"], text_color="#FFFFFF",
                                    command=lambda: threading.Thread(target=self.perform_service_action,
                                                                     args=(mysql_config["service_name"], 
                                                                           self.service_manager.start_service, 
                                                                           start_button)).start())
        start_button.grid(row=0, column=1, padx=(0, 10))
        
        stop_button = ctk.CTkButton(control_frame, text="停止服务", font=self.fonts["button"], text_color="#FFFFFF",
                                   command=lambda: threading.Thread(target=self.perform_service_action,
                                                                    args=(mysql_config["service_name"], 
                                                                          self.service_manager.stop_service, 
                                                                          stop_button)).start())
        stop_button.grid(row=0, column=2, padx=(0, 10))
        
        restart_button = ctk.CTkButton(control_frame, text="重启服务", font=self.fonts["button"], text_color="#FFFFFF",
                                      command=lambda: threading.Thread(target=self.perform_service_action,
                                                                       args=(mysql_config["service_name"], 
                                                                             self.service_manager.restart_service, 
                                                                             restart_button)).start())
        restart_button.grid(row=0, column=3, padx=(0, 10))
        
        # 编辑按钮
        edit_button = ctk.CTkButton(control_frame, text="编辑", font=self.fonts["button"], text_color="#FFFFFF",
                                   command=lambda: self.open_edit_dialog(mysql_config, index))
        edit_button.grid(row=0, column=4, padx=(0, 10))
        
        # 删除按钮
        delete_button = ctk.CTkButton(control_frame, text="删除", font=self.fonts["button"], 
                                     fg_color="#D32F2F", hover_color="#B71C1C", text_color="#FFFFFF",
                                     command=lambda: self.delete_version(mysql_config, index))
        delete_button.grid(row=0, column=5)
        
        # 返回创建的卡片帧
        return card_frame
    
    def create_log_panel(self):
        """
        创建底部日志面板
        """
        # 使用grid布局将日志面板放置在主内容区下方
        self.log_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="#F3F3F3")
        self.log_frame.grid(row=2, column=1, sticky="nsew", padx=0, pady=0)
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        # 日志标题栏
        log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 5))
        log_header.grid_columnconfigure(0, weight=1)
        
        log_title = ctk.CTkLabel(log_header, text="操作日志", font=self.fonts["subtitle"])
        log_title.grid(row=0, column=0, sticky="w")
        
        # 清空日志按钮
        clear_log_button = ctk.CTkButton(log_header, text="清空", width=60, font=self.fonts["small"], text_color="#FFFFFF", command=self.clear_logs)
        clear_log_button.grid(row=0, column=1, sticky="e")
        
        # 日志文本框
        self.log_text = ctk.CTkTextbox(self.log_frame, height=100, fg_color="#FFFFFF", font=self.fonts["body"])
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
        
        # 移除之前可能存在的处理器，避免重复记录
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 添加文本框处理器
        logger.addHandler(TextboxHandler(self.log_text))
    
    def clear_logs(self):
        """
        清空日志
        """
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
    
    def start_resize(self, event):
        """
        开始调整大小
        """
        self.start_y = event.y_root
        # 获取窗口总高度
        self.window_height = self.root.winfo_height()
        # 获取分割条的y坐标
        self.sash_y = self.sash.winfo_y()
    
    def resize(self, event):
        """
        调整大小
        """
        # 获取当前鼠标在窗口中的y坐标
        current_y = event.y_root - self.root.winfo_rooty()
        
        # 计算鼠标位置相对于窗口高度的比例
        # 排除分割条高度，并确保在有效范围内
        min_y = 100  # 主内容区最小高度
        max_y = self.window_height - 100  # 日志面板最小高度
        current_y = max(min_y, min(current_y, max_y))
        
        # 计算主内容区和日志面板的高度比例
        # 主内容区高度 = 当前y坐标 - 顶部边距
        # 日志面板高度 = 窗口高度 - 当前y坐标 - 分割条高度
        main_height = current_y
        log_height = self.window_height - current_y
        
        # 将高度比例转换为权重
        total_height = main_height + log_height
        new_main_weight = int((main_height / total_height) * 1000)
        new_log_weight = 1000 - new_main_weight  # 总权重固定为1000
        
        # 限制权重范围
        new_main_weight = max(50, min(new_main_weight, 950))  # 保持合理比例
        new_log_weight = 1000 - new_main_weight
        
        # 更新权重
        self.main_content_weight = new_main_weight
        self.log_panel_weight = new_log_weight
        
        # 应用新的行权重
        self.root.grid_rowconfigure(0, weight=new_main_weight)
        self.root.grid_rowconfigure(2, weight=new_log_weight)
    
    def perform_service_action(self, service_name, action_func, button=None):
        """
        执行服务操作并处理结果
        :param service_name: 服务名称
        :param action_func: 服务操作函数
        :param button: 触发操作的按钮，用于状态显示
        """
        # 初始化变量，避免未定义错误
        success = False
        message = ""
        original_text = ""
        
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
            
            # 获取所有服务名称列表
            start_services = [config["service_name"] for config in self.config["mysql_versions"]]
            
            # 直接传递版本号（可能为None）和服务名称列表
            success, message = action_func(service_name, version, start_services=start_services)
            
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
        dialog.title("编辑 MySQL 配置" if mysql_config else "添加MySQL配置")
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
        name_entry = ctk.CTkEntry(dialog, width=entry_width, font=self.fonts["body"])
        name_entry.grid(row=0, column=1, padx=20, pady=(20, 10))
        
        # 版本 - 标签显示
        version_label = ctk.CTkLabel(dialog, text="版本:", width=label_width, font=self.fonts["body"])
        version_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        version_display_label = ctk.CTkLabel(dialog, text="", width=entry_width, font=self.fonts["body"])
        version_display_label.grid(row=1, column=1, padx=20, pady=10, sticky="w")
        
        # 服务名 - 标签显示
        service_name_label = ctk.CTkLabel(dialog, text="服务名:", width=label_width, font=self.fonts["body"])
        service_name_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        service_name_display_label = ctk.CTkLabel(dialog, text="", width=entry_width, font=self.fonts["body"])
        service_name_display_label.grid(row=2, column=1, padx=20, pady=10, sticky="w")
        
        # 路径
        path_label = ctk.CTkLabel(dialog, text="路径:", width=label_width, font=self.fonts["body"])
        path_label.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        path_entry = ctk.CTkEntry(dialog, width=entry_width, font=self.fonts["body"])
        path_entry.grid(row=3, column=1, padx=20, pady=10)
        
        # 端口
        port_label = ctk.CTkLabel(dialog, text="PORT:", width=label_width, font=self.fonts["body"])
        port_label.grid(row=4, column=0, padx=20, pady=10, sticky="w")
        port_entry = ctk.CTkEntry(dialog, width=entry_width, font=self.fonts["body"])
        port_entry.grid(row=4, column=1, padx=20, pady=10)
        
        # 存储对话框控件引用，供auto_parse_path和save_mysql_config使用
        dialog.controls = {
            "name_entry": name_entry,
            "version_display_label": version_display_label,
            "service_name_display_label": service_name_display_label,
            "path_entry": path_entry,
            "port_entry": port_entry
        }
        
        # 添加路径输入变化事件监听
        path_entry.bind("<KeyRelease>", lambda event: self.auto_parse_path(dialog))
        path_entry.bind("<FocusOut>", lambda event: self.auto_parse_path(dialog))
        
        # 如果是编辑模式，填充现有数据
        if mysql_config:
            name_entry.insert(0, mysql_config["name"])
            # 设置版本和服务名标签文本
            version_display_label.configure(text=mysql_config["version"])
            service_name_display_label.configure(text=mysql_config["service_name"])
            path_entry.insert(0, mysql_config["path"])
            port_entry.insert(0, mysql_config["port"])
        
        # 按钮框架
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 20))
        button_frame.grid_columnconfigure(0, weight=1)
        
        # 保存按钮
        save_button = ctk.CTkButton(button_frame, text="保存", font=self.fonts["button"], text_color="#FFFFFF",
                                   command=lambda: self.save_mysql_config(dialog, mysql_config, index))
        save_button.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="e")
        
        # 取消按钮
        cancel_button = ctk.CTkButton(button_frame, text="取消", font=self.fonts["button"], text_color="#FFFFFF",
                                     command=lambda: dialog.destroy())
        cancel_button.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="w")
        
        # 聚焦对话框
        dialog.focus_force()
    
    def auto_parse_path(self, dialog):
        """
        自动解析路径，提取版本号并查找服务名
        :param dialog: 对话框实例
        """
        # 清除可能存在的错误消息
        for widget in dialog.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text_color") == "red":
                widget.destroy()
        
        # 获取路径
        path = dialog.controls["path_entry"].get().strip()
        if not path:
            return
        
        # 从路径中提取版本号
        version = self.env_handler.extract_version_from_path(path)
        if version:
            # 尝试根据路径查找实际的服务名
            service_name = self.env_handler.find_service_by_path(path)
            
            if service_name:
                # 更新版本号和服务名标签
                dialog.controls["version_display_label"].configure(text=version)
                dialog.controls["service_name_display_label"].configure(text=service_name)
            else:
                # 显示服务查找错误
                error_label = ctk.CTkLabel(dialog, text="未找到该服务，请检查服务配置", text_color="red", font=self.fonts["body"])
                error_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10))
                
                # 清空版本号和服务名标签
                dialog.controls["version_display_label"].configure(text="")
                dialog.controls["service_name_display_label"].configure(text="")
        else:
            # 显示版本解析错误
            error_label = ctk.CTkLabel(dialog, text="无法从路径中识别 MySQL 版本号", text_color="red", font=self.fonts["body"])
            error_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10))
            
            # 清空版本号和服务名标签
            dialog.controls["version_display_label"].configure(text="")
            dialog.controls["service_name_display_label"].configure(text="")
        
    def save_mysql_config(self, dialog, mysql_config, index):
        """
        保存MySQL配置
        :param dialog: 对话框实例
        :param mysql_config: 原始配置
        :param index: 配置索引
        """
        # 获取输入值
        name = dialog.controls["name_entry"].get().strip()
        path = dialog.controls["path_entry"].get().strip()
        port = dialog.controls["port_entry"].get().strip()
        
        # 清除可能存在的错误消息
        for widget in dialog.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text_color") == "red":
                widget.destroy()
        
        # 从路径中重新提取版本号和生成服务名
        version = self.env_handler.extract_version_from_path(path)
        if not version:
            # 显示版本解析错误
            error_label = ctk.CTkLabel(dialog, text="无法从路径中识别 MySQL 版本号，请检查路径格式", text_color="red", font=self.fonts["body"])
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
        if not os.path.exists(path):
            error_label = ctk.CTkLabel(dialog, text="MySQL 安装路径不存在", text_color="red", font=self.fonts["body"])
            error_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10))
            return
        
        # 验证是否包含mysqld.exe
        mysqld_path = os.path.join(path, "bin", "mysqld.exe")
        if not os.path.exists(mysqld_path):
            error_label = ctk.CTkLabel(dialog, text="该路径下未找到 mysqld.exe", text_color="red", font=self.fonts["body"])
            error_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10))
            return
        
        # 验证服务是否存在
        service_name = self.env_handler.find_service_by_path(path)
        if not service_name:
            error_label = ctk.CTkLabel(dialog, text="未找到该服务，请检查服务配置", text_color="red", font=self.fonts["body"])
            error_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10))
            return
        
        # 更新显示的版本号和服务名标签（确保保存的是最新解析的结果）
        dialog.controls["version_display_label"].configure(text=version)
        dialog.controls["service_name_display_label"].configure(text=service_name)
        
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
            config_path = self.get_config_path()
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
                                      fg_color="#D32F2F", hover_color="#B71C1C", text_color="#FFFFFF",
                                      command=lambda: self.confirm_delete(confirm_dialog, mysql_config, index))
        confirm_button.grid(row=0, column=0, padx=(0, 10), sticky="e")
        
        # 取消按钮
        cancel_button = ctk.CTkButton(button_frame, text="取消", font=self.fonts["button"], text_color="#FFFFFF",
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
            # 使用绝对路径保存配置文件，与load_config方法保持一致
            config_path = self.get_config_path()
            with open(config_path, "w", encoding="utf-8") as f:
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