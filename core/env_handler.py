import win32api
import win32con
import winreg as reg
import logging

class EnvironmentHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.env_key_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
    
    def set_mysql_home(self, path):
        """
        设置系统环境变量MYSQL_HOME
        :param path: MySQL安装路径
        :return: (成功标志, 消息)
        """
        try:
            # 打开系统环境变量注册表项
            hkey = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, self.env_key_path, 0, reg.KEY_ALL_ACCESS)
            
            # 设置MYSQL_HOME
            reg.SetValueEx(hkey, "MYSQL_HOME", 0, reg.REG_EXPAND_SZ, path)
            reg.CloseKey(hkey)
            
            # 广播环境变量变更消息
            self.broadcast_env_change()
            
            return True, f"MYSQL_HOME 设置为: {path}"
        except Exception as e:
            self.logger.error(f"设置MYSQL_HOME失败: {e}")
            return False, f"设置MYSQL_HOME失败: {str(e)}"
    
    def get_current_mysql_home(self):
        """
        获取当前MYSQL_HOME值
        :return: MYSQL_HOME路径或None
        """
        try:
            hkey = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, self.env_key_path, 0, reg.KEY_READ)
            value, _ = reg.QueryValueEx(hkey, "MYSQL_HOME")
            reg.CloseKey(hkey)
            return value
        except Exception as e:
            self.logger.error(f"获取MYSQL_HOME失败: {e}")
            return None
    
    def broadcast_env_change(self):
        """
        广播环境变量变更消息，通知所有窗口更新环境变量
        """
        try:
            # 广播WM_SETTINGCHANGE消息
            win32api.SendMessage(
                win32con.HWND_BROADCAST,
                win32con.WM_SETTINGCHANGE,
                0,
                "Environment"
            )
            self.logger.info("环境变量变更消息已广播")
        except Exception as e:
            self.logger.error(f"广播环境变量变更消息失败: {e}")