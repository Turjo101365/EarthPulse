"""
Database package for EarthPulse.
Provides PostgreSQL + pgvector storage and session-based chat persistence.
"""
from .postgres import db_manager

__all__ = ["db_manager"]
