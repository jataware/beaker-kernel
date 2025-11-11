"""
Hypothesis generation module for beaker-kernel.

Integrates AI-CoScientist for scientific hypothesis generation.
"""

from .generator import HypothesisGenerator
from .actions import HypothesisGenerationMixin

__all__ = ["HypothesisGenerator", "HypothesisGenerationMixin"]
