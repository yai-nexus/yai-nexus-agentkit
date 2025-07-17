"""
日志策略实现模块

提供不同的日志存储策略，包括：
- HourlyDirectoryStrategy: 按小时分目录存储日志
- SimpleFileStrategy: 简单文件存储策略
- DailyDirectoryStrategy: 按天分目录存储日志

这些策略实现了 LogPathStrategy 接口，可以与统一日志配置系统配合使用。
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

try:
    from yai_nexus_agentkit.core.logger_config import LogPathStrategy
    from yai_nexus_agentkit.core.utils import find_project_root, ensure_directory
except ImportError:
    # 如果 agentkit 不可用，提供基础实现
    from abc import ABC, abstractmethod
    
    class LogPathStrategy(ABC):
        """日志路径策略接口"""
        
        @abstractmethod
        def get_log_path(self, service_name: str) -> str:
            """生成日志文件路径"""
            pass
        
        @abstractmethod
        def get_metadata(self) -> Dict[str, Any]:
            """获取策略元数据"""
            pass
    
    def find_project_root() -> Path:
        """查找项目根目录"""
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / "package.json").exists() or (parent / "pyproject.toml").exists():
                return parent
        return current
    
    def ensure_directory(path: Path) -> bool:
        """确保目录存在"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False


class HourlyDirectoryStrategy(LogPathStrategy):
    """按小时分目录的日志策略"""
    
    def __init__(self, 
                 base_dir: str = "logs",
                 timezone: str = None,
                 create_symlink: bool = True,
                 create_readme: bool = True):
        self.base_dir = base_dir
        self.timezone = timezone or os.getenv('LOG_TIMEZONE', 'Asia/Shanghai')
        self.create_symlink = create_symlink
        self.create_readme = create_readme
        self._current_hour = None
        self._current_dir = None
    
    def get_log_path(self, service_name: str) -> str:
        """生成按小时分目录的日志路径"""
        now = datetime.now()
        hour_dir = now.strftime("%Y%m%d-%H")
        
        # 缓存优化：如果还是同一小时，直接返回缓存的路径
        if self._current_hour == hour_dir and self._current_dir:
            return str(self._current_dir / f"{service_name}.log")
        
        root_dir = find_project_root()
        log_dir = root_dir / self.base_dir / hour_dir
        
        # 确保目录存在
        if ensure_directory(log_dir):
            self._current_hour = hour_dir
            self._current_dir = log_dir
            
            # 创建/更新软链接
            if self.create_symlink:
                self._create_current_symlink(root_dir, hour_dir)
            
            # 创建 README
            if self.create_readme:
                self._create_hour_readme(log_dir, hour_dir)
        
        return str(log_dir / f"{service_name}.log")
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取策略元数据"""
        return {
            "strategy_name": "hourly_directory",
            "base_dir": self.base_dir,
            "timezone": self.timezone,
            "create_symlink": self.create_symlink,
            "create_readme": self.create_readme,
            "current_hour": self._current_hour
        }
    
    def _create_current_symlink(self, root_dir: Path, hour_dir: str) -> None:
        """创建或更新 current 软链接"""
        try:
            current_link = root_dir / self.base_dir / "current"
            
            # 如果软链接已存在，先删除
            if current_link.exists() or current_link.is_symlink():
                current_link.unlink()
            
            # 创建新的软链接
            if os.name != 'nt':  # Unix/Linux/macOS
                current_link.symlink_to(hour_dir)
            else:  # Windows - 创建 junction 或记录文件
                self._create_windows_link(current_link, hour_dir)
                
        except Exception:
            # 软链接失败不应该影响日志功能
            pass
    
    def _create_windows_link(self, link_path: Path, target: str) -> None:
        """Windows 系统的链接创建"""
        # 方案1: 尝试创建 junction (需要管理员权限)
        try:
            subprocess.run([
                'mklink', '/J', str(link_path), target
            ], check=True, shell=True, capture_output=True)
        except:
            # 方案2: 创建指向文件记录目标路径
            try:
                with open(f"{link_path}.txt", 'w') as f:
                    f.write(target)
            except:
                pass  # 即使备选方案失败也不影响日志功能
    
    def _create_hour_readme(self, log_dir: Path, hour_dir: str) -> None:
        """为每小时目录创建 README.md"""
        readme_path = log_dir / "README.md"
        if not readme_path.exists():
            content = f"""# 日志目录: {hour_dir}

创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
时区: {self.timezone}

## 包含的日志文件

- `python-backend.log`: Python 后端服务日志
- `nextjs-app.log`: Next.js 前端应用日志 (如果存在)

## 日志格式

所有日志文件都采用 JSON 格式，便于程序化处理和分析。

## 保留策略

日志文件会保留 7 天，之后自动清理。

## 访问当前日志

可以通过 `logs/current` 软链接访问当前小时的日志目录。
"""
            try:
                readme_path.write_text(content, encoding='utf-8')
            except Exception:
                pass  # README 创建失败不应该影响日志功能


class DailyDirectoryStrategy(LogPathStrategy):
    """按天分目录的日志策略"""
    
    def __init__(self, base_dir: str = "logs", create_symlink: bool = True):
        self.base_dir = base_dir
        self.create_symlink = create_symlink
        self._current_day = None
        self._current_dir = None
    
    def get_log_path(self, service_name: str) -> str:
        """生成按天分目录的日志路径"""
        now = datetime.now()
        day_dir = now.strftime("%Y%m%d")
        
        # 缓存优化
        if self._current_day == day_dir and self._current_dir:
            return str(self._current_dir / f"{service_name}.log")
        
        root_dir = find_project_root()
        log_dir = root_dir / self.base_dir / day_dir
        
        if ensure_directory(log_dir):
            self._current_day = day_dir
            self._current_dir = log_dir
            
            if self.create_symlink:
                self._create_current_symlink(root_dir, day_dir)
        
        return str(log_dir / f"{service_name}.log")
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "strategy_name": "daily_directory",
            "base_dir": self.base_dir,
            "create_symlink": self.create_symlink,
            "current_day": self._current_day
        }
    
    def _create_current_symlink(self, root_dir: Path, day_dir: str) -> None:
        """创建当天的软链接"""
        try:
            current_link = root_dir / self.base_dir / "current"
            
            if current_link.exists() or current_link.is_symlink():
                current_link.unlink()
            
            if os.name != 'nt':
                current_link.symlink_to(day_dir)
            else:
                with open(f"{current_link}.txt", 'w') as f:
                    f.write(day_dir)
        except Exception:
            pass


class SimpleFileStrategy(LogPathStrategy):
    """简单文件策略 - 用于对比和备选方案"""
    
    def __init__(self, log_dir: str = "logs", filename_template: str = "{service_name}.log"):
        self.log_dir = log_dir
        self.filename_template = filename_template
    
    def get_log_path(self, service_name: str) -> str:
        root_dir = find_project_root()
        log_dir = root_dir / self.log_dir
        ensure_directory(log_dir)
        
        filename = self.filename_template.format(service_name=service_name)
        return str(log_dir / filename)
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "strategy_name": "simple_file",
            "log_dir": self.log_dir,
            "filename_template": self.filename_template
        }


__all__ = [
    "HourlyDirectoryStrategy",
    "SimpleFileStrategy", 
    "DailyDirectoryStrategy"
]