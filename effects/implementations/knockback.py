"""
Knockback effect implementation.
"""

from ..core import Effect
from ..physics import KnockbackEffect as BaseKnockbackEffect

# Re-export the physics implementation
KnockbackEffect = BaseKnockbackEffect
