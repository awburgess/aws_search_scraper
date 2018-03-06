"""
SQLAlchemy models for MWS results and jobs
"""
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base


BASE = declarative_base()


class Jobs(BASE):
    __tablename__ = 'jobs'
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer, primary_key=True)
    category = Column(String, nullable=False)
    terms = Column(String, nullable=False)
    run_date = Column(DateTime, default=datetime.now())


def get_engine(sqlite_path: Path):
    """
    Create SQLAlchemy engine for SQLite

    Args:
        sqlite_path: Path object representing location of db (creates if not present)

    Returns:
        SQLAlchemy engine for SQLite db
    """
    return create_engine('sqlite:///' + sqlite_path.as_posix())
