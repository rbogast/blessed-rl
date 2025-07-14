"""
Shockwave effect implementation.
"""

from ..core import Effect
from ..physics import ShockwaveEffect as BaseShockwaveEffect

# Re-export the physics implementation
ShockwaveEffect = BaseShockwaveEffect
