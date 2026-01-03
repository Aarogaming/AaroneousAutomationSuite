"""
Batch API Integration for AAS

Provides cost-effective async processing using OpenAI's Batch API (50% cost reduction).
"""

from .manager import BatchManager
from .processor import BatchProcessor

__all__ = ['BatchManager', 'BatchProcessor']
