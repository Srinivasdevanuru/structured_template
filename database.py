import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import JSON

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class VideoAnalysis(Base):
    __tablename__ = "video_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_size_mb = Column(Float, nullable=False)
    frame_interval = Column(Integer, nullable=False)
    total_frames = Column(Integer, nullable=False)
    total_detections = Column(Integer, nullable=False)
    avg_per_frame = Column(Float, nullable=False)
    max_in_frame = Column(Integer, nullable=False)
    min_in_frame = Column(Integer, nullable=False)
    analysis_results = Column(JSON, nullable=False)  # Store frame-by-frame results
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_time_seconds = Column(Float, nullable=True, default=0.0)

class FrameDetection(Base):
    __tablename__ = "frame_detections"
    
    id = Column(Integer, primary_key=True, index=True)
    video_analysis_id = Column(Integer, nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp_seconds = Column(Float, nullable=False)
    medibox_count = Column(Integer, nullable=False)
    confidence_scores = Column(JSON, nullable=False)  # Array of confidence scores
    bounding_boxes = Column(JSON, nullable=False)  # Array of bounding box coordinates
    created_at = Column(DateTime, default=datetime.utcnow)

def create_tables():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass

def save_analysis_results(
    filename: str,
    file_size_mb: float,
    frame_interval: int,
    results: List[Dict[str, Any]],
    processing_time: Optional[float] = None
) -> int:
    """
    Save video analysis results to database
    
    Returns:
        Analysis ID
    """
    db = get_db()
    try:
        # Calculate summary statistics
        total_frames = len(results)
        total_detections = sum(r['medibox_count'] for r in results)
        avg_per_frame = total_detections / total_frames if total_frames > 0 else 0
        max_in_frame = max(r['medibox_count'] for r in results) if results else 0
        min_in_frame = min(r['medibox_count'] for r in results) if results else 0
        
        # Create video analysis record
        video_analysis = VideoAnalysis(
            filename=filename,
            file_size_mb=file_size_mb,
            frame_interval=frame_interval,
            total_frames=total_frames,
            total_detections=total_detections,
            avg_per_frame=avg_per_frame,
            max_in_frame=max_in_frame,
            min_in_frame=min_in_frame,
            analysis_results=results,
            processing_time_seconds=processing_time or 0.0
        )
        
        db.add(video_analysis)
        db.commit()
        db.refresh(video_analysis)
        
        # Save individual frame detections
        for result in results:
            frame_detection = FrameDetection(
                video_analysis_id=video_analysis.id,
                frame_number=result['frame_number'],
                timestamp_seconds=result['timestamp'],
                medibox_count=result['medibox_count'],
                confidence_scores=[d.get('score', 0) for d in result.get('detections', [])],
                bounding_boxes=[d.get('bbox', []) for d in result.get('detections', [])]
            )
            db.add(frame_detection)
        
        db.commit()
        return video_analysis.id
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_analysis_history(limit: int = 10) -> List[VideoAnalysis]:
    """Get recent analysis history"""
    db = get_db()
    try:
        return db.query(VideoAnalysis).order_by(VideoAnalysis.created_at.desc()).limit(limit).all()
    finally:
        db.close()

def get_analysis_by_id(analysis_id: int) -> Optional[VideoAnalysis]:
    """Get specific analysis by ID"""
    db = get_db()
    try:
        return db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
    finally:
        db.close()

def get_frame_detections(analysis_id: int) -> List[FrameDetection]:
    """Get frame detections for a specific analysis"""
    db = get_db()
    try:
        return db.query(FrameDetection).filter(
            FrameDetection.video_analysis_id == analysis_id
        ).order_by(FrameDetection.frame_number).all()
    finally:
        db.close()

def delete_analysis(analysis_id: int) -> bool:
    """Delete an analysis and its frame detections"""
    db = get_db()
    try:
        # Delete frame detections first
        db.query(FrameDetection).filter(FrameDetection.video_analysis_id == analysis_id).delete()
        
        # Delete analysis
        analysis = db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
        if analysis:
            db.delete(analysis)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()