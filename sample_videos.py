import streamlit as st
import requests
import os
from typing import List, Dict

# Sample video configurations using actual provided files
SAMPLE_VIDEOS = [
    {
        "name": "Sample Video 1",
        "description": "Medibox detection sample video",
        "duration": "Variable",
        "expected_objects": "To be detected",
        "file_key": "video_2025-05-28_11-57-01",
        "file_path": "attached_assets/video_2025-05-28_11-57-01.mp4"
    },
    {
        "name": "Sample Video 2", 
        "description": "Medibox detection sample video",
        "duration": "Variable",
        "expected_objects": "To be detected",
        "file_key": "video_2025-05-28_11-58-01",
        "file_path": "attached_assets/video_2025-05-28_11-58-01.mp4"
    },
    {
        "name": "Sample Video 3",
        "description": "Medibox detection sample video", 
        "duration": "Variable",
        "expected_objects": "To be detected",
        "file_key": "video_2025-05-28_11-59-01",
        "file_path": "attached_assets/video_2025-05-28_11-59-01.mp4"
    },
    {
        "name": "Sample Video 4",
        "description": "Medibox detection sample video",
        "duration": "Variable", 
        "expected_objects": "To be detected",
        "file_key": "video_2025-05-28_12-00-01",
        "file_path": "attached_assets/video_2025-05-28_12-00-01.mp4"
    },
    {
        "name": "Sample Video 5",
        "description": "Medibox detection sample video",
        "duration": "Variable",
        "expected_objects": "To be detected", 
        "file_key": "video_2025-05-28_12-01-01",
        "file_path": "attached_assets/video_2025-05-28_12-01-01.mp4"
    },
    {
        "name": "Sample Video 6",
        "description": "Medibox detection sample video",
        "duration": "Variable",
        "expected_objects": "To be detected",
        "file_key": "video_2025-05-28_12-02-01", 
        "file_path": "attached_assets/video_2025-05-28_12-02-01.mp4"
    }
]

def display_sample_videos() -> str:
    """
    Display sample video options and return selected video key
    Returns None if no video is selected
    """
    st.markdown("### 🎬 Sample Videos")
    st.markdown("Choose from our curated collection of medibox detection test videos:")
    
    # Create a grid layout for sample videos
    cols = st.columns(2)
    
    selected_video = None
    
    for i, video in enumerate(SAMPLE_VIDEOS):
        col = cols[i % 2]
        
        with col:
            with st.expander(f"📹 {video['name']}", expanded=False):
                st.write(f"**Description:** {video['description']}")
                st.write(f"**Duration:** {video['duration']}")
                st.write(f"**Expected Objects:** {video['expected_objects']}")
                
                if st.button(f"Use This Video", key=f"select_{video['file_key']}", type="secondary", use_container_width=True):
                    selected_video = video['file_key']
                    st.success(f"Selected: {video['name']}")
    
    return selected_video

def get_sample_video_info(video_key: str) -> Dict:
    """Get information about a sample video"""
    for video in SAMPLE_VIDEOS:
        if video['file_key'] == video_key:
            return video
    return None

def get_sample_video_path(video_key: str) -> str:
    """
    Get the file path for a sample video
    
    Args:
        video_key: The key identifying the sample video
        
    Returns:
        File path to the sample video, or None if not found
    """
    video_info = get_sample_video_info(video_key)
    if not video_info or 'file_path' not in video_info:
        return None
    
    file_path = video_info['file_path']
    
    # Check if file exists
    if os.path.exists(file_path):
        return file_path
    else:
        return None

def get_sample_videos_list() -> List[Dict]:
    """Return the list of available sample videos"""
    return SAMPLE_VIDEOS