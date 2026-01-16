"""
시스템 리소스 모니터링 모듈
CPU, GPU, 메모리, 디스크, 네트워크 등 시스템 리소스를 수집합니다.
"""

import psutil
import platform
import time
from datetime import datetime

# GPU 모니터링 (NVIDIA GPU용)
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

# Windows WMI (온도 측정용)
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False


class SystemMonitor:
    def __init__(self):
        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_time = time.time()
        
    def get_cpu_info(self):
        """CPU 정보 수집"""
        cpu_percent = psutil.cpu_percent(interval=0)
        cpu_percent_per_core = psutil.cpu_percent(interval=0, percpu=True)
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)
        
        # CPU 온도 (Windows에서는 제한적)
        cpu_temp = self._get_cpu_temperature()
        
        return {
            'percent': cpu_percent,
            'percent_per_core': cpu_percent_per_core,
            'frequency_current': cpu_freq.current if cpu_freq else 0,
            'frequency_max': cpu_freq.max if cpu_freq else 0,
            'cores_physical': cpu_count,
            'cores_logical': cpu_count_logical,
            'temperature': cpu_temp
        }
    
    def _get_cpu_temperature(self):
        """CPU 온도 측정 (Windows)"""
        try:
            if WMI_AVAILABLE:
                w = wmi.WMI(namespace="root\\wmi")
                temperature_info = w.MSAcpi_ThermalZoneTemperature()
                if temperature_info:
                    # 켈빈에서 섭씨로 변환
                    temp_kelvin = temperature_info[0].CurrentTemperature
                    temp_celsius = (temp_kelvin / 10.0) - 273.15
                    return round(temp_celsius, 1)
        except Exception:
            pass
        
        # psutil로 시도 (Linux에서 주로 작동)
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        return entries[0].current
        except Exception:
            pass
        
        return None
    
    def get_gpu_info(self):
        """GPU 정보 수집 (NVIDIA GPU)"""
        if not GPU_AVAILABLE:
            return {
                'available': False,
                'gpus': []
            }
        
        try:
            gpus = GPUtil.getGPUs()
            gpu_list = []
            
            for gpu in gpus:
                gpu_list.append({
                    'id': gpu.id,
                    'name': gpu.name,
                    'load': round(gpu.load * 100, 1),
                    'memory_total': gpu.memoryTotal,
                    'memory_used': gpu.memoryUsed,
                    'memory_free': gpu.memoryFree,
                    'memory_percent': round((gpu.memoryUsed / gpu.memoryTotal) * 100, 1) if gpu.memoryTotal > 0 else 0,
                    'temperature': gpu.temperature
                })
            
            return {
                'available': True,
                'gpus': gpu_list
            }
        except Exception:
            return {
                'available': False,
                'gpus': []
            }
    
    def get_memory_info(self):
        """메모리 정보 수집"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent,
            'total_gb': round(memory.total / (1024**3), 2),
            'used_gb': round(memory.used / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_percent': swap.percent
        }
    
    def get_disk_info(self):
        """디스크 정보 수집"""
        partitions = []
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent,
                    'total_gb': round(usage.total / (1024**3), 2),
                    'used_gb': round(usage.used / (1024**3), 2),
                    'free_gb': round(usage.free / (1024**3), 2)
                })
            except PermissionError:
                continue
        
        # 디스크 I/O
        current_time = time.time()
        current_disk_io = psutil.disk_io_counters()
        time_diff = current_time - self.last_time
        
        if time_diff > 0:
            read_speed = (current_disk_io.read_bytes - self.last_disk_io.read_bytes) / time_diff
            write_speed = (current_disk_io.write_bytes - self.last_disk_io.write_bytes) / time_diff
        else:
            read_speed = 0
            write_speed = 0
        
        self.last_disk_io = current_disk_io
        
        return {
            'partitions': partitions,
            'io': {
                'read_bytes': current_disk_io.read_bytes,
                'write_bytes': current_disk_io.write_bytes,
                'read_speed': round(read_speed / (1024**2), 2),  # MB/s
                'write_speed': round(write_speed / (1024**2), 2)  # MB/s
            }
        }
    
    def get_network_info(self):
        """네트워크 정보 수집"""
        current_time = time.time()
        current_net_io = psutil.net_io_counters()
        time_diff = current_time - self.last_time
        
        if time_diff > 0:
            bytes_sent_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_diff
            bytes_recv_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_diff
        else:
            bytes_sent_speed = 0
            bytes_recv_speed = 0
        
        self.last_net_io = current_net_io
        self.last_time = current_time
        
        # 네트워크 인터페이스별 정보
        interfaces = []
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()
        
        for interface, addrs in net_if_addrs.items():
            stats = net_if_stats.get(interface)
            if stats and stats.isup:
                ip_address = None
                for addr in addrs:
                    if addr.family.name == 'AF_INET':
                        ip_address = addr.address
                        break
                
                interfaces.append({
                    'name': interface,
                    'ip': ip_address,
                    'speed': stats.speed,
                    'is_up': stats.isup
                })
        
        return {
            'bytes_sent': current_net_io.bytes_sent,
            'bytes_recv': current_net_io.bytes_recv,
            'packets_sent': current_net_io.packets_sent,
            'packets_recv': current_net_io.packets_recv,
            'bytes_sent_speed': round(bytes_sent_speed / 1024, 2),  # KB/s
            'bytes_recv_speed': round(bytes_recv_speed / 1024, 2),  # KB/s
            'bytes_sent_speed_mb': round(bytes_sent_speed / (1024**2), 2),  # MB/s
            'bytes_recv_speed_mb': round(bytes_recv_speed / (1024**2), 2),  # MB/s
            'interfaces': interfaces
        }
    
    def get_system_info(self):
        """시스템 기본 정보"""
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        return {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'hostname': platform.node(),
            'processor': platform.processor(),
            'boot_time': boot_time.strftime('%Y-%m-%d %H:%M:%S'),
            'uptime_seconds': int(uptime.total_seconds()),
            'uptime_formatted': str(uptime).split('.')[0]
        }
    
    def get_all_resources(self):
        """모든 리소스 정보 수집"""
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp_ms': int(time.time() * 1000),
            'system': self.get_system_info(),
            'cpu': self.get_cpu_info(),
            'gpu': self.get_gpu_info(),
            'memory': self.get_memory_info(),
            'disk': self.get_disk_info(),
            'network': self.get_network_info()
        }


# 테스트용
if __name__ == '__main__':
    import json
    monitor = SystemMonitor()
    data = monitor.get_all_resources()
    print(json.dumps(data, indent=2, ensure_ascii=False))
