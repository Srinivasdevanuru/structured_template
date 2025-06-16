import cv2
import numpy as np
from typing import List, Dict, Any
import logging

class VideoProcessor:
    """Handles video processing operations including frame extraction"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_frames(self, video_path: str, interval_seconds: int = 5) -> List[Dict[str, Any]]:
        """
        Extract frames from video at specified intervals
        
        Args:
            video_path: Path to the video file
            interval_seconds: Extract frame every N seconds
            
        Returns:
            List of dictionaries containing frame data and metadata
        """
        try:
            # Open video capture
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                self.logger.error(f"Failed to open video: {video_path}")
                return []
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            self.logger.info(f"Video properties - FPS: {fps}, Total frames: {total_frames}, Duration: {duration:.2f}s")
            
            # Calculate frame interval
            frame_interval = int(fps * interval_seconds)
            
            frames_data = []
            frame_number = 0
            
            while True:
                # Set position to next frame of interest
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Calculate timestamp
                timestamp = frame_number / fps
                
                # Store frame data
                frames_data.append({
                    'frame': frame,
                    'frame_index': frame_number,
                    'timestamp': timestamp
                })
                
                # Move to next frame of interest
                frame_number += frame_interval
                
                # Check if we've reached the end
                if frame_number >= total_frames:
                    break
            
            cap.release()
            
            self.logger.info(f"Extracted {len(frames_data)} frames from video")
            return frames_data
            
        except Exception as e:
            self.logger.error(f"Error extracting frames: {str(e)}")
            return []
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get basic information about a video file
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing video metadata
        """
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return {}
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0
            
            cap.release()
            
            return {
                'fps': fps,
                'total_frames': total_frames,
                'width': width,
                'height': height,
                'duration': duration
            }
            
        except Exception as e:
            self.logger.error(f"Error getting video info: {str(e)}")
            return {}
    
    def resize_frame(self, frame: np.ndarray, max_width: int = 1024, max_height: int = 768) -> np.ndarray:
        """
        Resize frame while maintaining aspect ratio
        
        Args:
            frame: Input frame
            max_width: Maximum width
            max_height: Maximum height
            
        Returns:
            Resized frame
        """
        height, width = frame.shape[:2]
        
        # Calculate scaling factor
        scale_w = max_width / width
        scale_h = max_height / height
        scale = min(scale_w, scale_h, 1.0)  # Don't upscale
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return frame
    
    def save_frame(self, frame: np.ndarray, output_path: str) -> bool:
        """
        Save frame to file
        
        Args:
            frame: Frame to save
            output_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return cv2.imwrite(output_path, frame)
        except Exception as e:
            self.logger.error(f"Error saving frame: {str(e)}")
            return False
