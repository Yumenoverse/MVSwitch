import win32serviceutil
import win32service
import win32api
import win32con
import logging

class MySQLServiceManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
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
    
    def start_service(self, service_name):
        """
        启动MySQL服务
        :param service_name: 服务名称
        :return: (成功标志, 消息)
        """
        try:
            win32serviceutil.StartService(service_name)
            # 等待服务启动
            win32serviceutil.WaitForServiceStatus(service_name, win32service.SERVICE_RUNNING, 10000)
            return True, f"服务 {service_name} 启动成功"
        except Exception as e:
            self.logger.error(f"启动服务失败: {e}")
            return False, f"服务 {service_name} 启动失败: {str(e)}"
    
    def stop_service(self, service_name):
        """
        停止MySQL服务
        :param service_name: 服务名称
        :return: (成功标志, 消息)
        """
        try:
            win32serviceutil.StopService(service_name)
            # 等待服务停止
            win32serviceutil.WaitForServiceStatus(service_name, win32service.SERVICE_STOPPED, 10000)
            return True, f"服务 {service_name} 停止成功"
        except Exception as e:
            self.logger.error(f"停止服务失败: {e}")
            return False, f"服务 {service_name} 停止失败: {str(e)}"
    
    def restart_service(self, service_name):
        """
        重启MySQL服务
        :param service_name: 服务名称
        :return: (成功标志, 消息)
        """
        try:
            win32serviceutil.RestartService(service_name)
            # 等待服务启动
            win32serviceutil.WaitForServiceStatus(service_name, win32service.SERVICE_RUNNING, 10000)
            return True, f"服务 {service_name} 重启成功"
        except Exception as e:
            self.logger.error(f"重启服务失败: {e}")
            return False, f"服务 {service_name} 重启失败: {str(e)}"