"""
SQLAlchemy database models for performance tracking.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class Session(Base):
    """Practice session model."""
    
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_notes = Column(Integer, default=0)
    unique_notes = Column(Integer, default=0)
    avg_note_duration_ms = Column(Float, nullable=True)
    notes_per_minute = Column(Float, nullable=True)
    
    # Relationships
    notes = relationship("Note", back_populates="session", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, start={self.start_time}, notes={self.total_notes})>"
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Get session duration in minutes."""
        if self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 60
        return None


class Note(Base):
    """Individual note event model."""
    
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    midi_note = Column(Integer, nullable=False)
    note_name = Column(String(10), nullable=True)
    string_played = Column(String(1), nullable=True)  # G, D, A, E
    position = Column(Integer, nullable=True)
    finger_count = Column(Integer, nullable=True)
    pitch_offset = Column(Integer, default=0)
    duration_ms = Column(Integer, nullable=True)
    velocity = Column(Integer, default=100)
    
    # Relationship
    session = relationship("Session", back_populates="notes")
    
    def __repr__(self) -> str:
        return f"<Note(midi={self.midi_note}, string={self.string_played}, finger={self.finger_count})>"


class Metric(Base):
    """Performance metric model."""
    
    __tablename__ = 'metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    metric_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    extra_data = Column(String(500), nullable=True)  # JSON string for extra data
    
    # Relationship
    session = relationship("Session", back_populates="metrics")
    
    def __repr__(self) -> str:
        return f"<Metric(type={self.metric_type}, value={self.value})>"


class CalibrationProfile(Base):
    """Saved calibration profile model."""
    
    __tablename__ = 'calibration_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, default=False)
    
    # Position zones (stored as normalized Y coordinates)
    first_pos_min = Column(Float, default=0.0)
    first_pos_max = Column(Float, default=0.33)
    second_pos_min = Column(Float, default=0.33)
    second_pos_max = Column(Float, default=0.66)
    third_pos_min = Column(Float, default=0.66)
    third_pos_max = Column(Float, default=1.0)
    
    # Thresholds
    pinch_threshold = Column(Float, default=0.05)
    
    def __repr__(self) -> str:
        return f"<CalibrationProfile(name={self.name}, active={self.is_active})>"


def init_database(db_path: str) -> sessionmaker:
    """
    Initialize the database and return a session factory.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        SQLAlchemy sessionmaker instance
    """
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
