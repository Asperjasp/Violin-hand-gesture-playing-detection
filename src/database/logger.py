"""
Performance logging utilities.
"""

from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import json

from src.utils.config import Config
from src.database.connection import DatabaseConnection
from src.database.models import Session, Note, Metric


class PerformanceLogger:
    """
    Logs performance data to the database.
    
    Tracks notes played, timing, and calculates
    various performance metrics for analysis.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the performance logger.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.db = DatabaseConnection(config.database.path)
        
        # Current session
        self.current_session: Optional[Session] = None
        self.session_db = None
        
        # Note tracking
        self.note_start_time: Optional[datetime] = None
        self.last_note: Optional[int] = None
        self.note_counts: Dict[int, int] = defaultdict(int)
        self.note_durations: List[int] = []
        
        # Logging interval
        self.log_interval_ms = config.database.log_interval_ms
        self.last_log_time: Optional[datetime] = None
    
    def start_session(self) -> Session:
        """
        Start a new practice session.
        
        Returns:
            Created Session object
        """
        self.session_db = self.db.get_session()
        
        self.current_session = Session(
            start_time=datetime.utcnow(),
            total_notes=0,
            unique_notes=0
        )
        
        self.session_db.add(self.current_session)
        self.session_db.commit()
        
        # Reset tracking
        self.note_counts.clear()
        self.note_durations.clear()
        self.note_start_time = None
        self.last_note = None
        
        print(f"Session started: {self.current_session.id}")
        return self.current_session
    
    def end_session(self) -> Optional[Session]:
        """
        End the current session and calculate final metrics.
        
        Returns:
            Updated Session object
        """
        if not self.current_session:
            return None
        
        # Update session end time
        self.current_session.end_time = datetime.utcnow()
        self.current_session.unique_notes = len(self.note_counts)
        
        # Calculate average duration
        if self.note_durations:
            self.current_session.avg_note_duration_ms = (
                sum(self.note_durations) / len(self.note_durations)
            )
        
        # Calculate notes per minute
        duration = self.current_session.duration_minutes
        if duration and duration > 0:
            self.current_session.notes_per_minute = (
                self.current_session.total_notes / duration
            )
        
        # Save final metrics
        self._save_session_metrics()
        
        self.session_db.commit()
        
        print(f"Session ended: {self.current_session.total_notes} notes in {duration:.1f} min")
        
        session = self.current_session
        self.session_db.close()
        self.current_session = None
        
        return session
    
    def log_note(self, midi_note: int, gestures: Dict) -> None:
        """
        Log a note event.
        
        Args:
            midi_note: MIDI note number
            gestures: Gesture information dictionary
        """
        if not self.current_session:
            return
        
        now = datetime.utcnow()
        
        # Check logging interval
        if self.last_log_time:
            delta_ms = (now - self.last_log_time).total_seconds() * 1000
            if delta_ms < self.log_interval_ms:
                return
        
        # Calculate duration of previous note
        duration_ms = None
        if self.note_start_time and self.last_note is not None:
            delta = (now - self.note_start_time).total_seconds() * 1000
            duration_ms = int(delta)
            self.note_durations.append(duration_ms)
        
        # Create note record
        note = Note(
            session_id=self.current_session.id,
            timestamp=now,
            midi_note=midi_note,
            note_name=self._midi_to_name(midi_note),
            string_played=self._get_string_name(gestures.get('string')),
            position=gestures.get('position'),
            finger_count=gestures.get('finger_count'),
            pitch_offset=gestures.get('pitch_offset', 0),
            velocity=self.config.midi.velocity
        )
        
        self.session_db.add(note)
        
        # Update counters
        self.current_session.total_notes += 1
        self.note_counts[midi_note] += 1
        
        # Update tracking
        self.note_start_time = now
        self.last_note = midi_note
        self.last_log_time = now
        
        # Commit periodically
        if self.current_session.total_notes % 10 == 0:
            self.session_db.commit()
    
    def log_metric(self, metric_type: str, value: float, metadata: Dict = None) -> None:
        """
        Log a performance metric.
        
        Args:
            metric_type: Type of metric (e.g., "accuracy", "tempo")
            value: Metric value
            metadata: Optional additional data
        """
        if not self.current_session:
            return
        
        metric = Metric(
            session_id=self.current_session.id,
            metric_type=metric_type,
            value=value,
            recorded_at=datetime.utcnow(),
            metadata=json.dumps(metadata) if metadata else None
        )
        
        self.session_db.add(metric)
    
    def _save_session_metrics(self) -> None:
        """Save final session metrics."""
        if not self.current_session:
            return
        
        # Note distribution by string
        string_counts = defaultdict(int)
        for note in self.session_db.query(Note).filter_by(
            session_id=self.current_session.id
        ):
            if note.string_played:
                string_counts[note.string_played] += 1
        
        self.log_metric(
            "string_distribution",
            len(string_counts),
            dict(string_counts)
        )
        
        # Position usage
        position_counts = defaultdict(int)
        for note in self.session_db.query(Note).filter_by(
            session_id=self.current_session.id
        ):
            if note.position:
                position_counts[note.position] += 1
        
        self.log_metric(
            "position_usage",
            len(position_counts),
            {str(k): v for k, v in position_counts.items()}
        )
    
    def _midi_to_name(self, midi_note: int) -> str:
        """Convert MIDI note to name."""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1
        note_index = midi_note % 12
        return f"{notes[note_index]}{octave}"
    
    def _get_string_name(self, string_num: Optional[int]) -> Optional[str]:
        """Convert string number to name."""
        if string_num is None:
            return None
        return {1: 'E', 2: 'A', 3: 'D', 4: 'G'}.get(string_num)
    
    def get_session_stats(self, session_id: int = None) -> Dict:
        """
        Get statistics for a session.
        
        Args:
            session_id: Session ID (uses current if not specified)
            
        Returns:
            Dictionary of statistics
        """
        sid = session_id or (self.current_session.id if self.current_session else None)
        if not sid:
            return {}
        
        with self.db.session() as session:
            sess = session.query(Session).get(sid)
            if not sess:
                return {}
            
            notes = session.query(Note).filter_by(session_id=sid).all()
            
            return {
                "session_id": sid,
                "start_time": sess.start_time.isoformat(),
                "end_time": sess.end_time.isoformat() if sess.end_time else None,
                "duration_minutes": sess.duration_minutes,
                "total_notes": sess.total_notes,
                "unique_notes": sess.unique_notes,
                "notes_per_minute": sess.notes_per_minute,
                "avg_duration_ms": sess.avg_note_duration_ms,
                "most_played_note": max(
                    set(n.midi_note for n in notes),
                    key=lambda x: sum(1 for n in notes if n.midi_note == x),
                    default=None
                ) if notes else None
            }
