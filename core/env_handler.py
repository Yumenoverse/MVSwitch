import win32api
import win32con
import winreg as reg
import logging
import re
import win32serviceutil
import win32service

class EnvironmentHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.env_key_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
    
    def _set_environment_variable(self, var_name, value):
        """
        设置系统环境变量的公共方法
        :param var_name: 环境变量名称
        :param value: 环境变量值
        :return: (成功标志, 消息)
        """
        try:
            # 打开系统环境变量注册表项
            hkey = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, self.env_key_path, 0, reg.KEY_ALL_ACCESS)
            
            # 设置环境变量
            reg.SetValueEx(hkey, var_name, 0, reg.REG_EXPAND_SZ, value)
            reg.CloseKey(hkey)
            
            # 广播环境变量变更消息
            self.broadcast_env_change()
            
            return True, f"{var_name} 设置为: {value}"
        except Exception as e:
            self.logger.error(f"设置{var_name}失败: {e}")
            return False, f"设置{var_name}失败: {str(e)}"
    
    def set_mysql_home(self, path):
        """
        设置系统环境变量MYSQL_HOME
        :param path: MySQL安装路径
        :return: (成功标志, 消息)
        """
        return self._set_environment_variable("MYSQL_HOME", path)
    
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
            self.logger.error(f"获取 MYSQL_HOME 失败: {e}")
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
    
    def get_path(self):
        """
        获取当前系统PATH环境变量
        :return: PATH环境变量值
        """
        try:
            hkey = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, self.env_key_path, 0, reg.KEY_READ)
            value, _ = reg.QueryValueEx(hkey, "Path")
            reg.CloseKey(hkey)
            return value
        except Exception as e:
            self.logger.error(f"获取 PATH 环境变量失败: {e}")
            return None
    
    def check_and_update_path(self):
        """
        检查系统PATH变量，若不存在%MYSQL_HOME%\bin，则将其追加到PATH中
        :return: (成功标志, 消息)
        """
        try:
            # 获取当前PATH
            current_path = self.get_path()
            if current_path is None:
                return False, "无法获取当前 PATH 环境变量"
            
            # 检查是否已包含%MYSQL_HOME%\bin
            mysql_bin_path = "%MYSQL_HOME%\\bin"
            path_list = current_path.split(';')
            
            # 检查是否已存在
            for path in path_list:
                if path.strip() == mysql_bin_path:
                    return True, f"PATH 中已包含 {mysql_bin_path}"
            
            # 添加到PATH末尾
            new_path = current_path + f";{mysql_bin_path}"
            
            # 更新PATH环境变量
            hkey = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, self.env_key_path, 0, reg.KEY_ALL_ACCESS)
            reg.SetValueEx(hkey, "Path", 0, reg.REG_EXPAND_SZ, new_path)
            reg.CloseKey(hkey)
            
            # 广播环境变量变更
            self.broadcast_env_change()
            
            return True, f"已将 {mysql_bin_path} 添加到系统 PATH"
        except Exception as e:
            self.logger.error(f"更新 PATH 环境变量失败: {e}")
            return False, f"更新 PATH 环境变量失败: {str(e)}"
    
    def set_version_specific_var(self, version, path):
        """
        设置版本特定的环境变量 MYSQL_HOME_V[大版本]_[小版本]
        :param version: MySQL版本号，如 "8.0.32"
        :param path: MySQL安装路径
        :return: (成功标志, 消息)
        """
        try:
            # 解析版本号
            major, minor = self.parse_version(version)
            if major is None or minor is None:
                return False, f"无效的版本号格式: {version}"
            
            # 生成环境变量名
            var_name = f"MYSQL_HOME_V{major}_{minor}"
            
            # 设置环境变量
            return self._set_environment_variable(var_name, path)
        except Exception as e:
            self.logger.error(f"设置版本特定环境变量失败: {e}")
            return False, f"设置版本特定环境变量失败: {str(e)}"
    
    def get_version_specific_var(self, version):
        """
        获取版本特定的环境变量值
        :param version: MySQL版本号，如 "8.0.32"
        :return: 环境变量值或None
        """
        try:
            # 解析版本号
            major, minor = self.parse_version(version)
            if major is None or minor is None:
                return None
            
            # 生成环境变量名
            var_name = f"MYSQL_HOME_V{major}_{minor}"
            
            # 获取环境变量值
            hkey = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, self.env_key_path, 0, reg.KEY_READ)
            value, _ = reg.QueryValueEx(hkey, var_name)
            reg.CloseKey(hkey)
            return value
        except Exception as e:
            self.logger.error(f"获取版本特定环境变量失败: {e}")
            return None
    
    def check_mysql_home_pointing(self, version):
        """
        检查MYSQL_HOME是否指向了正确的版本路径
        :param version: MySQL版本号，如 "8.0.32"
        :return: (是否正确指向, 当前值, 预期值)
        """
        try:
            # 获取当前MYSQL_HOME值
            current_mysql_home = self.get_current_mysql_home()
            if current_mysql_home is None:
                return False, None, None
            
            # 获取版本特定变量的实际值
            version_path = self.get_version_specific_var(version)
            if version_path is None:
                return False, current_mysql_home, None
            
            # 检查是否指向正确的实际路径
            is_correct = current_mysql_home.strip() == version_path.strip()
            
            return is_correct, current_mysql_home, version_path
        except Exception as e:
            self.logger.error(f"检查 MYSQL_HOME 指向失败: {e}")
            return False, None, None
    
    def parse_version(self, version):
        """
        解析版本号，提取大版本和小版本
        :param version: MySQL版本号，如 "8.0.32"
        :return: (major_version, minor_version) 或 (None, None)
        """
        try:
            # 使用正则表达式匹配版本号格式
            match = re.match(r"^(\d+)\.(\d+)\.\d+", version)
            if match:
                major = match.group(1)
                minor = match.group(2)
                return major, minor
            return None, None
        except Exception as e:
            self.logger.error(f"解析版本号失败: {e}")
            return None, None
    
    def extract_version_from_path(self, path):
        """
        从路径中提取MySQL版本号
        :param path: MySQL安装路径，如 "D:\\mysql-8.0.32-winx64"
        :return: 版本号字符串（如 "8.0.32"）或None
        """
        try:
            # 正则表达式从路径中匹配版本号
            # 格式如：mysql-8.0.32-winx64, MySQL-5.7.39, mysql5.6.47 等
            import os
            # 获取路径的最后一部分
            folder_name = os.path.basename(path)
            
            # 匹配版本号模式：数字.数字.数字
            match = re.search(r"(\d+)\.(\d+)\.(\d+)", folder_name)
            if match:
                return match.group(0)
            
            # 如果没有匹配到，尝试更宽松的匹配（可能没有小版本号）
            match = re.search(r"(\d+)\.(\d+)", folder_name)
            if match:
                return f"{match.group(0)}.0"  # 假设小版本号为0
            
            return None
        except Exception as e:
            self.logger.error(f"从路径提取版本号失败: {e}")
            return None
    
    def generate_service_name(self, version):
        """
        根据版本号生成服务名，规则为 MySQL[大版本][次版本]
        :param version: MySQL版本号，如 "8.0.32"
        :return: 服务名或None
        """
        try:
            major, minor = self.parse_version(version)
            if major is None or minor is None:
                return None
            
            return f"MySQL{major}{minor}"
        except Exception as e:
            self.logger.error(f"生成服务名失败: {e}")
            return None
    
    def find_service_by_path(self, mysql_path):
        """
        根据MySQL安装路径查找匹配的服务名
        :param mysql_path: MySQL安装路径，如 "D:\mysql-8.0.32-winx64"
        :return: 匹配的服务名或None
        """
        try:
            import os
            import winreg as reg
            
            # 构建期望的mysqld.exe路径
            expected_mysqld_path = os.path.normpath(os.path.join(mysql_path, "bin", "mysqld")).lower()
            
            # 打开服务注册表项
            services_key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services", 0, reg.KEY_READ)
            
            try:
                # 遍历所有服务
                index = 0
                while True:
                    try:
                        # 获取服务名
                        service_name = reg.EnumKey(services_key, index)
                        index += 1
                        
                        # 跳过非MySQL相关服务（可选，为了提高效率）
                        if not service_name.lower().startswith("mysql"):
                            continue
                        
                        # 打开服务的注册表项
                        service_key = reg.OpenKey(services_key, service_name, 0, reg.KEY_READ)
                        
                        try:
                            # 获取ImagePath值（服务可执行文件路径）
                            image_path, _ = reg.QueryValueEx(service_key, "ImagePath")
                            
                            # 清理路径（去除引号和可能的参数）
                            if image_path.startswith('"') and '"' in image_path[1:]:
                                image_path = image_path[1:image_path.index('"', 1)]
                            else:
                                # 没有引号，取第一个空格之前的部分
                                image_path = image_path.split()[0]
                            
                            # 标准化路径并转换为小写进行比较
                            normalized_path = os.path.normpath(image_path).lower()
                            
                            # 检查是否匹配期望的mysqld.exe路径
                            if normalized_path == expected_mysqld_path:
                                return service_name
                                
                        except Exception:
                            # 跳过无法读取ImagePath的服务
                            pass
                        finally:
                            reg.CloseKey(service_key)
                            
                    except OSError:
                        # 没有更多服务了
                        break
                        
            finally:
                reg.CloseKey(services_key)
                
            # 如果没有找到匹配的服务，返回None
            return None
            
        except Exception as e:
            self.logger.error(f"根据路径查找服务失败: {e}")
            return None
    
    def verify_admin_rights(self):
        """
        验证当前是否有管理员权限
        :return: 是否有管理员权限
        """
        try:
            # 尝试打开注册表项
            hkey = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, self.env_key_path, 0, reg.KEY_ALL_ACCESS)
            reg.CloseKey(hkey)
            return True
        except Exception as e:
            self.logger.error(f"没有管理员权限: {e}")
            return False