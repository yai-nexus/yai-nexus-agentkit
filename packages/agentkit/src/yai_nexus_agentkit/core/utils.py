"""
通用工具函数模块

提供项目通用的工具函数，包括：
- 项目根目录查找
- 目录创建和管理
- 文件操作辅助函数
"""

import os
from pathlib import Path
from typing import Optional, List


# 标准项目标记文件列表
DEFAULT_PROJECT_MARKERS = [
    "pnpm-workspace.yaml",  # monorepo 标记
    "package.json",         # Node.js 项目
    "pyproject.toml",       # Python 项目
    "Cargo.toml",          # Rust 项目
    ".git",                # Git 仓库
    "composer.json",       # PHP 项目
]


def find_project_root(marker_files: Optional[List[str]] = None) -> Path:
    """
    查找项目根目录
    
    从当前目录向上查找，直到找到包含标记文件的目录
    
    Args:
        marker_files: 标记文件列表，默认使用 DEFAULT_PROJECT_MARKERS
    
    Returns:
        Path: 项目根目录路径
    """
    if marker_files is None:
        marker_files = DEFAULT_PROJECT_MARKERS
    
    current = Path.cwd()
    
    # 从当前目录向上查找
    for parent in [current] + list(current.parents):
        for marker in marker_files:
            if (parent / marker).exists():
                return parent
    
    # 如果找不到，返回当前目录
    return current


def ensure_directory(path: Path) -> bool:
    """
    确保目录存在
    
    Args:
        path: 目录路径
    
    Returns:
        bool: 创建成功或已存在返回 True，失败返回 False
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False


def get_safe_filename(filename: str, max_length: int = 255) -> str:
    """
    获取安全的文件名（去除非法字符）
    
    Args:
        filename: 原始文件名
        max_length: 最大长度限制
    
    Returns:
        str: 安全的文件名
    """
    # 替换非法字符
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    safe_filename = "".join(c if c in safe_chars else "_" for c in filename)
    
    # 限制长度
    if len(safe_filename) > max_length:
        name, ext = os.path.splitext(safe_filename)
        max_name_length = max_length - len(ext)
        safe_filename = name[:max_name_length] + ext
    
    return safe_filename


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小为人类可读格式
    
    Args:
        size_bytes: 文件大小（字节）
    
    Returns:
        str: 格式化后的大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def is_writable_directory(path: Path) -> bool:
    """
    检查目录是否可写
    
    Args:
        path: 目录路径
    
    Returns:
        bool: 可写返回 True，否则返回 False
    """
    try:
        if not path.exists():
            return False
        
        if not path.is_dir():
            return False
        
        # 尝试创建一个临时文件来测试写权限
        test_file = path / ".write_test"
        test_file.touch()
        test_file.unlink()
        return True
    except (OSError, PermissionError):
        return False


__all__ = [
    "DEFAULT_PROJECT_MARKERS",
    "find_project_root",
    "ensure_directory", 
    "get_safe_filename",
    "format_file_size",
    "is_writable_directory"
]