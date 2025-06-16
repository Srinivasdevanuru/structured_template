import cv2
import numpy as np
from typing import List, Dict, Any
import streamlit as st
from datetime import timedelta

def validate_file(uploaded_file) -> bool:
    """
    Validate uploaded video file
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        True if file is valid, False otherwise
    """
    # Check file size (100MB limit)
    max_size = 100 * 1024 * 1024  # 100MB in bytes
    if uploaded_file.size > max_size:
        return False
    
    # Check file extension
    allowed_extensions = ['mp4', 'webm', 'ogg']
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension not in allowed_extensions:
        return False
    
    return True

def format_timestamp(seconds: float) -> str:
    """
    Format timestamp from seconds to human-readable format
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string (MM:SS or HH:MM:SS)
    """
    td = timedelta(seconds=int(seconds))
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def draw_bounding_boxes(image: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
    """
    Draw bounding boxes on image for detected objects
    
    Args:
        image: Input image (BGR format)
        detections: List of detection results from API
        
    Returns:
        Image with bounding boxes drawn
    """
    if not detections:
        return image
    
    # Make a copy to avoid modifying original
    result_image = image.copy()
    
    # Define vibrant colors for bounding boxes (BGR format)
    colors = [
        (0, 255, 0),      # Bright Green
        (255, 100, 0),    # Orange Blue
        (0, 100, 255),    # Orange Red  
        (255, 255, 0),    # Cyan
        (255, 0, 255),    # Magenta
        (0, 255, 255),    # Yellow
        (128, 0, 255),    # Purple
        (0, 255, 128),    # Light Green
    ]
    
    for i, detection in enumerate(detections):
        # Get bounding box coordinates
        bbox = detection.get('bounding_box', [])
        if len(bbox) != 4:
            continue
        
        # Ensure coordinates are integers
        x1, y1, x2, y2 = [int(coord) for coord in bbox]
        
        # Select color
        color = colors[i % len(colors)]
        
        # Draw thicker, more visible bounding box
        cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 3)
        
        # Prepare enhanced label text
        label = detection.get('label', 'Medibox')
        score = detection.get('score', 0)
        object_num = f"#{i + 1}"
        text = f"{object_num} ({score:.2f})"
        
        # Calculate text size and position
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        # Draw larger text background with padding
        padding = 8
        cv2.rectangle(
            result_image,
            (x1, y1 - text_height - baseline - padding),
            (x1 + text_width + padding, y1),
            color,
            -1
        )
        
        # Draw white text with shadow effect
        cv2.putText(
            result_image,
            text,
            (x1 + 4, y1 - baseline - 4),
            font,
            font_scale,
            (255, 255, 255),  # White text
            thickness
        )
        
        # Add corner markers for better visibility
        corner_size = 15
        corner_thickness = 4
        
        # Top-left corner
        cv2.line(result_image, (x1, y1), (x1 + corner_size, y1), color, corner_thickness)
        cv2.line(result_image, (x1, y1), (x1, y1 + corner_size), color, corner_thickness)
        
        # Top-right corner
        cv2.line(result_image, (x2, y1), (x2 - corner_size, y1), color, corner_thickness)
        cv2.line(result_image, (x2, y1), (x2, y1 + corner_size), color, corner_thickness)
        
        # Bottom-left corner
        cv2.line(result_image, (x1, y2), (x1 + corner_size, y2), color, corner_thickness)
        cv2.line(result_image, (x1, y2), (x1, y2 - corner_size), color, corner_thickness)
        
        # Bottom-right corner
        cv2.line(result_image, (x2, y2), (x2 - corner_size, y2), color, corner_thickness)
        cv2.line(result_image, (x2, y2), (x2, y2 - corner_size), color, corner_thickness)
    
    return result_image

def calculate_object_area(bbox: List[int]) -> int:
    """
    Calculate the area of a bounding box
    
    Args:
        bbox: Bounding box coordinates [x1, y1, x2, y2]
        
    Returns:
        Area in pixels
    """
    if len(bbox) != 4:
        return 0
    
    x1, y1, x2, y2 = bbox
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    return width * height

def filter_detections_by_confidence(detections: List[Dict[str, Any]], min_confidence: float = 0.5) -> List[Dict[str, Any]]:
    """
    Filter detections by minimum confidence score
    
    Args:
        detections: List of detection results
        min_confidence: Minimum confidence threshold
        
    Returns:
        Filtered list of detections
    """
    return [d for d in detections if d.get('score', 0) >= min_confidence]

def get_detection_stats(detections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics for a list of detections
    
    Args:
        detections: List of detection results
        
    Returns:
        Dictionary with statistics
    """
    if not detections:
        return {
            'count': 0,
            'avg_confidence': 0,
            'min_confidence': 0,
            'max_confidence': 0,
            'total_area': 0,
            'avg_area': 0
        }
    
    scores = [d.get('score', 0) for d in detections]
    areas = [calculate_object_area(d.get('bounding_box', [])) for d in detections]
    
    return {
        'count': len(detections),
        'avg_confidence': np.mean(scores),
        'min_confidence': min(scores),
        'max_confidence': max(scores),
        'total_area': sum(areas),
        'avg_area': np.mean(areas) if areas else 0
    }

def export_results_to_csv(results: List[Dict[str, Any]]) -> str:
    """
    Export analysis results to CSV format
    
    Args:
        results: List of frame analysis results
        
    Returns:
        CSV content as string
    """
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Frame_Index',
        'Timestamp_Seconds',
        'Timestamp_Formatted',
        'Playdough_Count',
        'Detection_Details'
    ])
    
    # Write data
    for result in results:
        detection_details = []
        for i, det in enumerate(result.get('detections', [])):
            bbox = det.get('bounding_box', [])
            score = det.get('score', 0)
            detection_details.append(f"Object_{i+1}:({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}):conf_{score:.3f}")
        
        writer.writerow([
            result['frame_index'],
            result['timestamp'],
            format_timestamp(result['timestamp']),
            result['playdough_count'],
            ';'.join(detection_details)
        ])
    
    return output.getvalue()
