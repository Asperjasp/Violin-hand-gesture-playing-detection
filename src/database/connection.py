"""
Database connection management.
"""

from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLSession

from src.database.models import Base


class DatabaseConnection:
    """
    Manages database connections and sessions.
    
    Provides a context manager for safe session handling
    and utilities for database operations.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_directory()
        
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False}
        )
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Session factory
        self.SessionFactory = sessionmaker(bind=self.engine)
    
    def _ensure_directory(self) -> None:
        """Ensure the database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def session(self):
        """
        Context manager for database sessions.
        
        Automatically commits on success, rolls back on error.
        
        Usage:
            with db.session() as session:
                session.add(my_object)
        """
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_session(self) -> SQLSession:
        """
        Get a new session instance.
        
        Note: Caller is responsible for closing the session.
        
        Returns:
            SQLAlchemy Session instance
        """
        return self.SessionFactory()
    
    def close(self) -> None:
        """Close the database connection."""
        self.engine.dispose()


# Global connection instance
_connection: Optional[DatabaseConnection] = None


def get_connection(db_path: str = None) -> DatabaseConnection:
    """
    Get or create the global database connection.
    
    Args:
        db_path: Database file path (required on first call)
        
    Returns:
        DatabaseConnection instance
    """
    global _connection
    
    if _connection is None:
        if db_path is None:
            raise ValueError("db_path required for initial connection")
        _connection = DatabaseConnection(db_path)
    
    return _connection


def close_connection() -> None:
    """Close the global database connection."""
    global _connection
    
    if _connection is not None:
        _connection.close()
        _connection = None
