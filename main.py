import sys
import ctypes
import customtkinter as ctk
from ui.main_window import MainWindow

# 检查管理员权限
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    # 设置UI主题
    ctk.set_appearance_mode("System")  # 使用系统主题
    ctk.set_default_color_theme("blue")  # 设置蓝色主题
    
    # 检查管理员权限
    if not is_admin():
        # 创建错误对话框
        error_window = ctk.CTkToplevel()
        error_window.title("权限错误")
        error_window.resizable(False, False)
        error_window.attributes("-topmost", True)
        
        # 直接设置居中位置
        width, height = 400, 150
        x = int((error_window.winfo_screenwidth()/2) - (width/2))
        y = int((error_window.winfo_screenheight()/2) - (height/2))
        error_window.geometry(f"{width}x{height}+{x}+{y}")
        
        error_label = ctk.CTkLabel(error_window, text="错误：需要管理员权限运行此应用！", font=ctk.CTkFont(family="Microsoft YaHei UI", size=14, weight="bold"))
        error_label.pack(pady=20, padx=20)
        
        ok_button = ctk.CTkButton(error_window, text="确定", text_color="#FFFFFF", command=lambda: sys.exit(1))
        ok_button.pack(pady=10)
        
        # 聚焦对话框
        error_window.focus_force()
        error_window.mainloop()
        sys.exit(1)
    
    # 创建主窗口
    app = ctk.CTk()
    main_window = MainWindow(app)
    app.mainloop()

if __name__ == "__main__":
    main()