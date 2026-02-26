import win32serviceutil
import win32service
import win32api
import win32con
import logging
from .env_handler import EnvironmentHandler

class MVSwitchServiceManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.env_handler = EnvironmentHandler()
    
    def get_service_status(self, service_name):
        """
        获取MySQL服务状态
        :param service_name: 服务名称
        :return: 服务状态字符串 (running, stopped, paused, unknown)
        """
        try:
            status = win32serviceutil.QueryServiceStatus(service_name)
            service_state = status[1]
            
            if service_state == win32service.SERVICE_RUNNING:
                return "running"
            elif service_state == win32service.SERVICE_STOPPED:
                return "stopped"
            elif service_state == win32service.SERVICE_PAUSED:
                return "paused"
            else:
                return "unknown"
        except Exception as e:
            self.logger.error(f"获取服务状态失败: {e}")
            return "unknown"
    
    def _setup_environment(self, version):
        """
        检查并设置环境变量（MYSQL_HOME和PATH）
        :param version: MySQL版本号
        :return: (成功标志, 消息)
        """
        try:
            # 检查并设置MYSQL_HOME指向正确的版本变量
            is_correct, current_value, expected_value = self.env_handler.check_mysql_home_pointing(version)
            
            if not is_correct:
                # 设置MYSQL_HOME指向正确的版本变量
                result, msg = self.env_handler.set_mysql_home(expected_value)
                if not result:
                    return False, f"设置 MYSQL_HOME失败: {msg}"
            
            # 检查PATH环境变量是否包含%MYSQL_HOME%\bin
            result, msg = self.env_handler.check_and_update_path()
            if not result:
                self.logger.warning(f"PATH环境变量检查/更新失败: {msg}")
            
            return True, "环境变量设置完成"
        except Exception as e:
            self.logger.error(f"环境变量设置失败: {e}")
            return False, f"环境变量设置失败: {str(e)}"
    
    def _find_running_service(self, service_names):
        """
        查找正在运行的服务
        :param service_names: 服务名称列表
        :return: 正在运行的服务名称/None
        """
        for service_name in service_names:
            status = self.get_service_status(service_name)
            if status == "running":
                return service_name
        return None

    def start_service(self, service_name, version, timeout=10000, start_services=None):
        """
        启动MySQL服务
        :param service_name: 服务名称
        :param version: MySQL版本号，如 "8.0.32"
        :param timeout: 等待服务启动的超时时间(毫秒)
        :param start_services: 服务名称列表
        :return: (成功标志, 消息)
        """
        try:
            # 验证管理员权限
            if not self.env_handler.verify_admin_rights():
                return False, "需要管理员权限才能执行此操作"
            
            # 检查是否有其他服务正在运行，并停止
            running_service = self._find_running_service(start_services)
            if running_service != None and running_service != service_name:
                try:
                    win32serviceutil.StopService(running_service)
                    # 等待服务停止
                    win32serviceutil.WaitForServiceStatus(running_service, win32service.SERVICE_STOPPED, timeout)
                    self.logger.info(f"服务 {running_service} 停止成功，正在启动 {service_name}...")
                except Exception as e:
                    self.logger.error(f"停止服务 {running_service} 失败，未能启动服务 {service_name}: {e}")
                    return False, f"停止服务 {running_service} 失败，未能启动服务 {service_name}: {str(e)}"
            
            
            # 设置环境变量
            result, msg = self._setup_environment(version)
            if not result:
                return False, msg
            
            # 检查服务状态
            status = self.get_service_status(service_name)
            if status == "running":
                return True, f"服务 {service_name} 已经在运行中"
            
            # 启动服务
            win32serviceutil.StartService(service_name)
            # 等待服务启动
            win32serviceutil.WaitForServiceStatus(service_name, win32service.SERVICE_RUNNING, timeout)
            return True, f"服务 {service_name} 启动成功"
        except Exception as e:
            self.logger.error(f"启动服务失败: {e}")
            return False, f"服务 {service_name} 启动失败: {str(e)}"
    
    def stop_service(self, service_name, version=None, timeout=10000, start_services=None):
        """
        停止MySQL服务
        :param service_name: 服务名称
        :param version: MySQL版本号
        :param timeout: 等待服务停止的超时时间(毫秒)
        :param start_services: 服务名称列表
        :return: (成功标志, 消息)
        """
        try:
            # 先检查服务状态
            status = self.get_service_status(service_name)
            if status == "stopped":
                return True, f"服务 {service_name} 已经停止"
            
            win32serviceutil.StopService(service_name)
            # 等待服务停止
            win32serviceutil.WaitForServiceStatus(service_name, win32service.SERVICE_STOPPED, timeout)
            return True, f"服务 {service_name} 停止成功"
        except Exception as e:
            self.logger.error(f"停止服务失败: {e}")
            return False, f"服务 {service_name} 停止失败: {str(e)}"
    
    def restart_service(self, service_name, version=None, timeout=10000, start_services=None):
        """
        重启MySQL服务
        :param service_name: 服务名称
        :param version: MySQL版本号（兼容参数，实际重启服务不需要）
        :param timeout: 等待服务重启的超时时间(毫秒)
        :param start_services: 服务名称列表
        :return: (成功标志, 消息)
        """
        try:
            # 验证管理员权限
            if not self.env_handler.verify_admin_rights():
                return False, "需要管理员权限才能执行此操作"
            
            
            # 检查服务状态
            status = self.get_service_status(service_name)
            if status == "stopped":
                return True, f"服务 {service_name} 已经停止，无需重启"
            else:
                # 否则重启服务
                # 设置环境变量
                if version:
                    result, msg = self._setup_environment(version)
                    if not result:
                        return False, msg
                win32serviceutil.RestartService(service_name)
            
            # 等待服务启动
            win32serviceutil.WaitForServiceStatus(service_name, win32service.SERVICE_RUNNING, timeout)
            return True, f"服务 {service_name} 重启成功"
        except Exception as e:
            self.logger.error(f"重启服务失败: {e}")
            return False, f"服务 {service_name} 重启失败: {str(e)}"