#!/usr/bin/env python
# coding: utf-8
"""
iPanel Core Exception Classes
Custom exceptions for better error handling
"""

class iPanelError(Exception):
    """Base exception for all iPanel errors"""
    def __init__(self, message, code=None, details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        
    def to_dict(self):
        """Convert exception to dictionary for JSON responses"""
        return {
            'error': True,
            'message': self.message,
            'code': self.code,
            'details': self.details
        }

class AuthenticationError(iPanelError):
    """Authentication related errors"""
    pass

class AuthorizationError(iPanelError):
    """Authorization related errors"""
    pass

class DatabaseError(iPanelError):
    """Database operation errors"""
    pass

class ConfigurationError(iPanelError):
    """Configuration errors"""
    pass

class ValidationError(iPanelError):
    """Data validation errors"""
    pass

class NetworkError(iPanelError):
    """Network operation errors"""
    pass

class FileSystemError(iPanelError):
    """File system operation errors"""
    pass

class ServiceError(iPanelError):
    """Service operation errors"""
    pass

class PluginError(iPanelError):
    """Plugin system errors"""
    pass

class APIError(iPanelError):
    """API operation errors"""
    pass
