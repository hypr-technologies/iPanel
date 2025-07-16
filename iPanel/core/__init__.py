#!/usr/bin/env python
# coding: utf-8
"""
iPanel Core Module System
Provides core functionality for iPanel v8.0.0
"""

from .auth import AuthManager
from .database import DatabaseManager
from .config import ConfigManager
from .logging import LogManager
from .cache import CacheManager
from .exceptions import (
    iPanelError,
    AuthenticationError,
    DatabaseError,
    ConfigurationError,
    ValidationError
)

__version__ = "8.0.0"
__author__ = "Hypr Technologies"

# Core module instances
auth_manager = AuthManager()
database_manager = DatabaseManager()
config_manager = ConfigManager()
log_manager = LogManager()
cache_manager = CacheManager()

# Export all core components
__all__ = [
    'auth_manager',
    'database_manager', 
    'config_manager',
    'log_manager',
    'cache_manager',
    'AuthManager',
    'DatabaseManager',
    'ConfigManager',
    'LogManager',
    'CacheManager',
    'iPanelError',
    'AuthenticationError',
    'DatabaseError',
    'ConfigurationError',
    'ValidationError'
]
