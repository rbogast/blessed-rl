"""
Map templates for procedural generation.
"""

from .base import MapTemplate, ParameterDef
from .registry import get_template, register_template, list_templates

__all__ = ['MapTemplate', 'ParameterDef', 'get_template', 'register_template', 'list_templates']
