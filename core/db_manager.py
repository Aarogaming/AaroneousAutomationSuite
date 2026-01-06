"""
Database layer for AAS using SQLite with SQLAlchemy ORM.

This module provides a type-safe database abstraction layer with
Pydantic model integration, connection pooling, and migration support.
"""

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional
from loguru import logger

# Base class for all database models
Base = declarative_base()


class DatabaseManager:
    """
    Manages database connections, sessions, and lifecycle.
    
    Uses SQLite for simplicity and zero-configuration deployment.
    Can be extended to PostgreSQL for production scalability.
    """
    
    def __init__(
        self,
        db_path: str = "artifacts/aas.db",
        echo: bool = False,
        enable_foreign_keys: bool = True
    ):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
            echo: Whether to log SQL statements (debug mode)
            enable_foreign_keys: Enable foreign key constraints
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create SQLite engine with connection pooling
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=echo,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool  # StaticPool for SQLite
        )
        
        # Enable foreign key constraints and load extensions
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            if enable_foreign_keys:
                cursor.execute("PRAGMA foreign_keys=ON")
            
            # Load sqlite-vec extension if available
            try:
                import sqlite_vec
                dbapi_conn.enable_load_extension(True)
                sqlite_vec.load(dbapi_conn)
                logger.debug("Loaded sqlite-vec extension")
            except ImportError:
                logger.warning("sqlite-vec not found, vector search will be disabled")
            except Exception as e:
                logger.error(f"Failed to load sqlite-vec extension: {e}")
            
            cursor.close()
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=self.engine
        )
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def create_tables(self) -> None:
        """Create all tables defined by SQLAlchemy models."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self) -> None:
        """Drop all tables (use with caution)."""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session with automatic cleanup.
        
        Usage:
            with db_manager.get_session() as session:
                task = session.query(Task).filter_by(id=1).first()
        
        Yields:
            SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """
        Get a database session without context manager.
        
        Note: Caller is responsible for closing the session.
        
        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()
    
    def execute_raw_sql(self, sql: str) -> None:
        """
        Execute raw SQL statement (use sparingly).
        
        Args:
            sql: SQL statement to execute
        """
        from sqlalchemy import text
        with self.engine.connect() as connection:
            connection.execute(text(sql))
            connection.commit()
        logger.debug(f"Executed raw SQL: {sql[:50]}...")
    
    def backup_database(self, backup_path: str) -> None:
        """
        Create a backup of the SQLite database.
        
        Args:
            backup_path: Path for backup file
        """
        import shutil
        backup_path_obj = Path(backup_path)
        backup_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(self.db_path, backup_path_obj)
        logger.info(f"Database backed up to {backup_path_obj}")
    
    def get_table_stats(self) -> dict:
        """
        Get statistics about database tables.
        
        Returns:
            Dictionary with table names and row counts
        """
        from sqlalchemy import text
        stats = {}
        with self.engine.connect() as connection:
            for table in Base.metadata.tables.keys():
                try:
                    result = connection.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    )
                    count = result.scalar()
                    stats[table] = count
                except Exception as e:
                    logger.warning(f"Failed to get stats for table {table}: {e}")
                    stats[table] = -1
        return stats


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(
    db_path: str = "artifacts/aas.db",
    echo: bool = False
) -> DatabaseManager:
    """
    Get or create the global database manager instance.
    
    Args:
        db_path: Path to SQLite database file
        echo: Whether to log SQL statements
    
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path=db_path, echo=echo)
        _db_manager.create_tables()
    return _db_manager


def init_database(db_path: str = "artifacts/aas.db", echo: bool = False) -> None:
    """
    Initialize the database (create tables, set up connections).
    
    Args:
        db_path: Path to SQLite database file
        echo: Whether to log SQL statements
    """
    db_manager = get_db_manager(db_path=db_path, echo=echo)
    logger.info("Database initialized successfully")
