"""
Platform detection utilities for cross-platform compatibility.
"""

import platform
import sys
import locale
import os
from typing import Optional


class PlatformDetector:
    """Detects platform capabilities and recommends appropriate character sets."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.encoding = self._detect_encoding()
        self.supports_unicode = self._test_unicode_support()
    
    def _detect_encoding(self) -> str:
        """Detect the system's preferred encoding."""
        # Try multiple methods to detect encoding
        encodings_to_try = [
            sys.stdout.encoding,
            locale.getpreferredencoding(),
            sys.getdefaultencoding(),
        ]
        
        # Add environment variable encodings
        if 'PYTHONIOENCODING' in os.environ:
            encodings_to_try.insert(0, os.environ['PYTHONIOENCODING'])
        
        for encoding in encodings_to_try:
            if encoding:
                return encoding.lower()
        
        return 'utf-8'  # Fallback
    
    def _test_unicode_support(self) -> bool:
        """Test if the terminal supports Unicode characters."""
        try:
            # Test if we can encode/decode Unicode characters
            test_chars = ['·', '▒', '↑', '♣']
            for char in test_chars:
                char.encode(self.encoding)
            return True
        except (UnicodeEncodeError, UnicodeDecodeError, LookupError):
            return False
    
    def get_recommended_character_set(self) -> str:
        """Get the recommended character set for this platform."""
        # Check for explicit environment variable override
        if 'BLESSED_RL_CHARSET' in os.environ:
            charset = os.environ['BLESSED_RL_CHARSET'].lower()
            if charset in ['unicode', 'ascii', 'cp437']:
                return charset
        
        # Platform-specific logic
        if self.system == 'windows':
            # Windows-specific detection
            if self._is_windows_terminal() or self._is_wt():
                # Modern Windows Terminal supports Unicode well
                return 'unicode' if self.supports_unicode else 'cp437'
            elif self._is_cmd_or_powershell():
                # Traditional cmd.exe or PowerShell - use CP437 if available
                return 'cp437' if self._test_cp437_support() else 'ascii'
            else:
                # Unknown Windows terminal - be conservative
                return 'ascii'
        
        elif self.system in ['linux', 'darwin']:
            # Linux and macOS usually have good Unicode support
            return 'unicode' if self.supports_unicode else 'ascii'
        
        else:
            # Unknown platform - be conservative
            return 'ascii'
    
    def _is_windows_terminal(self) -> bool:
        """Check if running in Windows Terminal."""
        return 'WT_SESSION' in os.environ
    
    def _is_wt(self) -> bool:
        """Check if running in Windows Terminal (alternative method)."""
        return os.environ.get('TERM_PROGRAM') == 'vscode' or 'WT_PROFILE_ID' in os.environ
    
    def _is_cmd_or_powershell(self) -> bool:
        """Check if running in cmd.exe or PowerShell."""
        # This is a heuristic - not perfect but reasonable
        return (
            os.environ.get('COMSPEC', '').lower().endswith('cmd.exe') or
            'POWERSHELL' in os.environ.get('PSModulePath', '') or
            os.environ.get('TERM') is None
        )
    
    def _test_cp437_support(self) -> bool:
        """Test if the system supports CP437 encoding."""
        try:
            test_chars = ['▒', '↑', '♣']
            for char in test_chars:
                char.encode('cp437')
            return True
        except (UnicodeEncodeError, LookupError):
            return False
    
    def get_platform_info(self) -> dict:
        """Get detailed platform information for debugging."""
        return {
            'system': self.system,
            'platform': platform.platform(),
            'encoding': self.encoding,
            'stdout_encoding': sys.stdout.encoding,
            'locale_encoding': locale.getpreferredencoding(),
            'supports_unicode': self.supports_unicode,
            'supports_cp437': self._test_cp437_support(),
            'recommended_charset': self.get_recommended_character_set(),
            'environment': {
                'TERM': os.environ.get('TERM'),
                'TERM_PROGRAM': os.environ.get('TERM_PROGRAM'),
                'WT_SESSION': os.environ.get('WT_SESSION'),
                'COMSPEC': os.environ.get('COMSPEC'),
                'BLESSED_RL_CHARSET': os.environ.get('BLESSED_RL_CHARSET'),
            }
        }
