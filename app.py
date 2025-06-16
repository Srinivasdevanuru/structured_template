import streamlit as st
import cv2
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import tempfile
import os
import time
from datetime import datetime, timedelta
import json

from video_processor import VideoProcessor
from api_client import LandingAIClient
from utils import validate_file, format_timestamp, draw_bounding_boxes, export_results_to_csv
from database import create_tables, save_analysis_results, get_analysis_history, get_analysis_by_id, delete_analysis
from sample_videos import display_sample_videos, get_sample_video_info, get_sample_video_path
from auth import (
    create_auth_tables, create_default_admin, login_form, register_form, 
    auth_sidebar, check_permission, user_management_tab
)

# Page configuration
st.set_page_config(
    page_title="Medibox Detection System",
    page_icon="📦",
    layout="wide"
)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'current_frame_index' not in st.session_state:
    st.session_state.current_frame_index = 0
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

# Initialize database and authentication
try:
    create_tables()
    create_auth_tables()
    create_default_admin()
except Exception as e:
    st.error(f"Database initialization error: {str(e)}")

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'show_register' not in st.session_state:
    st.session_state.show_register = False

def main():
    # Check authentication first
    if not st.session_state.authenticated:
        if st.session_state.show_register:
            register_form()
        else:
            login_form()
        return
    
    st.title("📦 Medibox Detection System")
    st.markdown("Upload a video to analyze and count medibox objects using AI-powered computer vision.")
    
    # Authentication sidebar
    auth_sidebar()
    
    # Sidebar for configuration and testing
    with st.sidebar:
        st.header("⚙️ Analysis Settings")
        
        # API Key (pre-configured)
        api_key = "land_sk_aMAuV8fgT2SL7SdlDQhx24a1tWjebdgFO0iIJv2B1mST72BNSf"
        detection_prompt = "medibox in the picture"
        
        # Frame extraction interval with improved UI
        st.subheader("📊 Frame Analysis")
        frame_interval = st.slider(
            "Frame Extraction Interval",
            min_value=1,
            max_value=30,
            value=5,
            help="Extract and analyze frames every N seconds"
        )
        st.caption(f"Will analyze every {frame_interval} second{'s' if frame_interval != 1 else ''}")
        
        st.divider()
        
        # Enhanced Single Image Testing
        st.subheader("🔍 Quick Test")
        st.write("Test detection on a single image before video analysis")
        
        test_image = st.file_uploader(
            "Upload test image",
            type=['png', 'jpg', 'jpeg'],
            key="test_image",
            help="Upload an image to test medibox detection"
        )
        
        if st.button("🚀 Test Detection", type="primary", use_container_width=True) and test_image and api_key:
            test_single_image(test_image, api_key, detection_prompt)
        
        st.divider()
        
        # Information panel
        with st.expander("ℹ️ About This System"):
            st.write("""
            **Medibox Detection System**
            
            - Analyzes video files for medibox inventory
            - Provides min/max count tracking
            - Shows detection trends over time
            - Supports MP4, WebM, and Ogg formats
            - Maximum file size: 100MB
            """)
            
        st.caption("Powered by LandingAI Computer Vision")
    
    # Role-based tab access
    user_role = st.session_state.user_info.get('role', 'viewer')
    
    if user_role == 'admin':
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📹 Video Analysis", "📊 Results Visualization", "🔍 Frame Inspector", "📚 Analysis History", "👥 User Management"])
        
        with tab1:
            video_analysis_tab(api_key, detection_prompt, frame_interval)
        
        with tab2:
            results_visualization_tab()
        
        with tab3:
            frame_inspector_tab()
        
        with tab4:
            analysis_history_tab()
        
        
        with tab5:
            user_management_tab()
    
    elif user_role == 'analyst':
        tab1, tab2, tab3, tab4 = st.tabs(["📹 Video Analysis", "📊 Results Visualization", "🔍 Frame Inspector", "📚 Analysis History"])
        
        with tab1:
            video_analysis_tab(api_key, detection_prompt, frame_interval)
        
        with tab2:
            results_visualization_tab()
        
        with tab3:
            frame_inspector_tab()
        
        with tab4:
            analysis_history_tab()
    
    else:  # viewer role
        tab1, tab2, tab3 = st.tabs(["📊 Results Visualization", "🔍 Frame Inspector", "📚 Analysis History"])
        
        with tab1:
            results_visualization_tab()
        
        with tab2:
            frame_inspector_tab()
        
        with tab3:
            analysis_history_tab()

def video_analysis_tab(api_key, detection_prompt, frame_interval):
    st.header("📹 Video Upload and Analysis")
    
    # Video source selection
    video_source = st.radio(
        "Choose Video Source:",
        ["Upload Your Own Video", "Use Sample Videos"],
        horizontal=True
    )
    
    uploaded_file = None
    selected_video_info = None
    
    if video_source == "Upload Your Own Video":
        # Create a more polished upload area
        upload_container = st.container()
        with upload_container:
            st.markdown("### Upload Your Video")
            st.markdown("Choose a video file to analyze medibox inventory over time")
            
            # File uploader with enhanced styling
            uploaded_file = st.file_uploader(
                "Drag and drop or browse for video file",
                type=['mp4', 'webm', 'ogg'],
                help="Supported formats: MP4, WebM, Ogg (maximum size: 100MB)",
                label_visibility="collapsed"
            )
    
    else:  # Use Sample Videos
        # Initialize session state for sample video selection
        if 'selected_sample_video' not in st.session_state:
            st.session_state.selected_sample_video = None
        
        selected_video_key = display_sample_videos()
        if selected_video_key:
            st.session_state.selected_sample_video = selected_video_key
            st.rerun()
        
        if st.session_state.selected_sample_video:
            selected_video_info = get_sample_video_info(st.session_state.selected_sample_video)
            st.info(f"Selected: {selected_video_info['name']}")
            
            # Clear selection button
            if st.button("Clear Selection"):
                st.session_state.selected_sample_video = None
                st.rerun()
            
            # Create a mock uploaded file object for sample videos
            class MockUploadedFile:
                def __init__(self, name, size=1024*1024*5):  # 5MB mock size
                    self.name = name
                    self.size = size
            uploaded_file = MockUploadedFile(selected_video_info['name'])
    
    if uploaded_file is not None:
        # Validate file (skip validation for sample videos)
        if video_source == "Upload Your Own Video" and not validate_file(uploaded_file):
            st.error("❌ File size exceeds 100MB limit or unsupported format.")
            return
        
        st.success("✅ Video file uploaded successfully!")
        
        # Enhanced video info display  
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            if video_source == "Use Sample Videos" and selected_video_info:
                # Get actual file size for sample videos
                sample_path = get_sample_video_path(selected_video_info['file_key'])
                if sample_path and os.path.exists(sample_path):
                    actual_size = os.path.getsize(sample_path) / (1024*1024)
                    st.metric("File Size", f"{actual_size:.1f} MB")
                else:
                    st.metric("File Size", "Unknown")
            else:
                st.metric("File Size", f"{uploaded_file.size / (1024*1024):.1f} MB")
        with col3:
            st.metric("Analysis Interval", f"Every {frame_interval}s")
        
        # Video preview (only for real uploaded files)
        if video_source == "Upload Your Own Video":
            st.markdown("### Video Preview")
            st.video(uploaded_file)
        else:
            st.markdown("### Sample Video Information")
            if selected_video_info:
                st.info(f"**Description:** {selected_video_info['description']}")
                st.info(f"**Expected Objects:** {selected_video_info['expected_objects']}")
                st.info(f"**Duration:** {selected_video_info['duration']}")
        
        # Enhanced analysis section
        st.markdown("### Start Analysis")
        analysis_col1, analysis_col2 = st.columns([3, 1])
        
        with analysis_col1:
            st.info("📊 The system will extract frames and detect medibox objects to provide comprehensive inventory analysis including trends, min/max counts, and detection rates.")
        
        with analysis_col2:
            if st.button("🚀 Analyze Video", type="primary", use_container_width=True):
                if not api_key:
                    st.error("API key is not configured.")
                    return
                
                if video_source == "Use Sample Videos" and selected_video_info:
                    # For sample videos, get the actual file path
                    sample_path = get_sample_video_path(selected_video_info['file_key'])
                    
                    if sample_path and os.path.exists(sample_path):
                        st.info(f"Starting analysis of {selected_video_info['name']}...")
                        analyze_sample_video(sample_path, selected_video_info['name'], api_key, detection_prompt, frame_interval)
                    else:
                        st.error(f"Sample video file not found: {selected_video_info['name']}")
                else:
                    analyze_video(uploaded_file, api_key, detection_prompt, frame_interval)
    else:
        # Show helpful information when no file is uploaded
        st.info("👆 Upload a video file above to begin medibox detection analysis")
        
        # Feature highlights
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            **📊 Inventory Tracking**
            - Real-time object counting
            - Min/max inventory levels
            - Detection confidence scores
            """)
        with col2:
            st.markdown("""
            **📈 Trend Analysis**
            - Time-based count visualization
            - Frame-by-frame inspection
            - Statistical summaries
            """)
        with col3:
            st.markdown("""
            **🔍 Visual Recognition**
            - Bounding box annotations
            - Object identification
            - Enhanced detection display
            """)

def analyze_video(uploaded_file, api_key, detection_prompt, frame_interval):
    """Process video and analyze frames for medibox detection"""
    
    # Initialize clients
    processor = VideoProcessor()
    ai_client = LandingAIClient(api_key)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name
    
    try:
        # Extract frames
        st.info("📽️ Extracting frames from video...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        frames_data = processor.extract_frames(tmp_path, frame_interval)
        
        if not frames_data:
            st.error("Failed to extract frames from video.")
            return
        
        total_frames = len(frames_data)
        st.success(f"✅ Extracted {total_frames} frames")
        
        # Analyze frames
        st.info("🤖 Analyzing frames with AI...")
        results = []
        
        for i, frame_data in enumerate(frames_data):
            status_text.text(f"Processing frame {i+1}/{total_frames} (timestamp: {format_timestamp(frame_data['timestamp'])})")
            progress_bar.progress((i + 1) / total_frames)
            
            # Convert frame to PIL Image
            frame_rgb = cv2.cvtColor(frame_data['frame'], cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # Analyze with AI
            try:
                detections = ai_client.detect_objects(pil_image, detection_prompt)
                medibox_count = len(detections) if detections else 0
                
                results.append({
                    'frame_index': i,
                    'timestamp': frame_data['timestamp'],
                    'frame': frame_data['frame'],
                    'detections': detections,
                    'medibox_count': medibox_count
                })
                
            except Exception as e:
                st.warning(f"Failed to analyze frame {i+1}: {str(e)}")
                results.append({
                    'frame_index': i,
                    'timestamp': frame_data['timestamp'],
                    'frame': frame_data['frame'],
                    'detections': [],
                    'medibox_count': 0
                })
            
            # Small delay to prevent API rate limiting
            time.sleep(0.1)
        
        # Store results in session state
        st.session_state.analysis_results = results
        st.session_state.processing_complete = True
        st.session_state.current_frame_index = 0
        
        # Calculate summary statistics
        total_detections = sum(r['medibox_count'] for r in results)
        avg_per_frame = total_detections / len(results) if results else 0
        max_in_frame = max(r['medibox_count'] for r in results) if results else 0
        
        st.success("🎉 Analysis Complete!")
        
        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        with summary_col1:
            st.metric("Total Frames Analyzed", len(results), help="Number of frames extracted and processed")
        with summary_col2:
            st.metric("Total Objects Detected", total_detections, help="Sum of all medibox detections")
        with summary_col3:
            st.metric("Average per Frame", f"{avg_per_frame:.1f}", help="Mean number of objects detected per frame")
        with summary_col4:
            st.metric("Peak Count", max_in_frame, help="Maximum objects detected in a single frame")
        
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def analyze_sample_video(video_path: str, video_name: str, api_key: str, detection_prompt: str, frame_interval: int):
    """Process sample video file for medibox detection"""
    
    start_time = time.time()
    
    try:
        processor = VideoProcessor()
        client = LandingAIClient(api_key)
        
        # Initialize progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []
        
        status_text.text("Extracting frames from sample video...")
        
        # Extract frames from video
        frames_data = processor.extract_frames(video_path, frame_interval)
        
        if not frames_data:
            st.error("Could not extract frames from sample video.")
            return
        
        st.info(f"Extracted {len(frames_data)} frames for analysis")
        
        # Process each frame
        for i, frame_data in enumerate(frames_data):
            progress = (i + 1) / len(frames_data)
            progress_bar.progress(progress)
            status_text.text(f"Analyzing frame {i+1}/{len(frames_data)}...")
            
            # Convert frame to PIL Image
            frame_rgb = cv2.cvtColor(frame_data['frame'], cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # Detect objects in frame
            detections = client.detect_objects(pil_image, detection_prompt)
            
            # Store results
            result = {
                'frame_index': i,
                'timestamp': frame_data['timestamp'],
                'medibox_count': len(detections),
                'detections': detections,
                'frame': frame_data['frame']
            }
            results.append(result)
            
            # Small delay to prevent API rate limiting
            time.sleep(0.1)
        
        # Store results in session state
        st.session_state.analysis_results = results
        st.session_state.processing_complete = True
        st.session_state.current_frame_index = 0
        
        # Save results to database (exclude frame data)
        try:
            processing_time = time.time() - start_time
            # Get file size (estimate for sample videos)
            file_size_mb = os.path.getsize(video_path) / (1024*1024) if os.path.exists(video_path) else 5.0
            
            # Create database-safe results (remove numpy arrays)
            db_results = []
            for result in results:
                db_result = {
                    'frame_index': result['frame_index'],
                    'timestamp': result['timestamp'],
                    'medibox_count': result['medibox_count'],
                    'detections': result['detections']
                    # Exclude 'frame' data as it contains numpy arrays
                }
                db_results.append(db_result)
            
            analysis_id = save_analysis_results(
                filename=video_name,
                file_size_mb=file_size_mb,
                frame_interval=frame_interval,
                results=db_results,
                processing_time=processing_time
            )
            st.success(f"Analysis saved to database with ID: {analysis_id}")
        except Exception as e:
            st.warning(f"Could not save to database: {str(e)}")
        
        # Calculate summary statistics
        total_detections = sum(r['medibox_count'] for r in results)
        avg_per_frame = total_detections / len(results) if results else 0
        max_in_frame = max(r['medibox_count'] for r in results) if results else 0
        
        st.success("Analysis Complete!")
        
        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        with summary_col1:
            st.metric("Total Frames Analyzed", len(results), help="Number of frames extracted and processed")
        with summary_col2:
            st.metric("Total Objects Detected", total_detections, help="Sum of all medibox detections")
        with summary_col3:
            st.metric("Average per Frame", f"{avg_per_frame:.1f}", help="Mean number of objects detected per frame")
        with summary_col4:
            st.metric("Peak Count", max_in_frame, help="Maximum objects detected in a single frame")
        
    except Exception as e:
        st.error(f"Error during sample video analysis: {str(e)}")
        st.session_state.processing_complete = False

def results_visualization_tab():
    st.header("Analysis Results")
    
    if not st.session_state.processing_complete or not st.session_state.analysis_results:
        st.info("🔄 No analysis results available. Please upload and analyze a video first.")
        return
    
    results = st.session_state.analysis_results
    
    # Create DataFrame for visualization
    df = pd.DataFrame([
        {
            'Frame': r['frame_index'],
            'Timestamp': format_timestamp(r['timestamp']),
            'Medibox Count': r['medibox_count'],
            'Timestamp_seconds': r['timestamp']
        }
        for r in results
    ])
    
    # Enhanced visualization with inventory tracking
    st.subheader("📈 Inventory Count Over Time")
    
    # Create enhanced line chart with min/max annotations
    fig = px.line(
        df, 
        x='Timestamp_seconds', 
        y='Medibox Count',
        title='Medibox Inventory Tracking',
        labels={'Timestamp_seconds': 'Time (seconds)', 'Medibox Count': 'Number of Objects'}
    )
    
    # Add markers and improve styling
    fig.update_traces(
        mode='lines+markers',
        line=dict(width=3, color='#FF6B6B'),
        marker=dict(size=8, color='#FF6B6B', line=dict(width=2, color='white'))
    )
    
    # Add horizontal lines for min and max
    max_count = df['Medibox Count'].max()
    min_count = df['Medibox Count'].min()
    
    fig.add_hline(y=max_count, line_dash="dash", line_color="green", 
                  annotation_text=f"Peak: {max_count} objects", annotation_position="top right")
    fig.add_hline(y=min_count, line_dash="dash", line_color="orange", 
                  annotation_text=f"Minimum: {min_count} objects", annotation_position="bottom right")
    
    # Enhance layout
    fig.update_layout(
        height=450,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='lightgray'),
        yaxis=dict(showgrid=True, gridcolor='lightgray')
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Inventory Analysis")
        
        # Calculate inventory metrics
        total_frames = len(results)
        total_detections = int(df['Medibox Count'].sum())
        avg_per_frame = df['Medibox Count'].mean()
        max_count = int(df['Medibox Count'].max())
        min_count = int(df['Medibox Count'].min())
        frames_with_objects = len(df[df['Medibox Count'] > 0])
        
        # Display key metrics in columns
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric("📦 Peak Inventory", max_count, help="Maximum medibox pieces detected in a single frame")
            st.metric("📉 Minimum Count", min_count, help="Lowest count detected")
        
        with metric_col2:
            st.metric("📊 Average Count", f"{avg_per_frame:.1f}", help="Average medibox pieces per frame")
            st.metric("🎯 Detection Rate", f"{(frames_with_objects/total_frames)*100:.1f}%", help="Percentage of frames with detections")
        
        with metric_col3:
            st.metric("🔢 Total Detections", total_detections, help="Sum of all detections across frames")
            st.metric("📹 Total Frames", total_frames, help="Number of frames analyzed")
    
    with col2:
        st.subheader("📋 Frame-by-Frame Data")
        st.dataframe(
            df[['Frame', 'Timestamp', 'Medibox Count']],
            hide_index=True,
            height=300
        )

def frame_inspector_tab():
    st.header("Frame Inspector")
    
    if not st.session_state.processing_complete or not st.session_state.analysis_results:
        st.info("🔄 No frames available. Please analyze a video first.")
        return
    
    results = st.session_state.analysis_results
    
    # Frame navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Previous", disabled=st.session_state.current_frame_index <= 0):
            st.session_state.current_frame_index = max(0, st.session_state.current_frame_index - 1)
            st.rerun()
    
    with col2:
        frame_index = st.slider(
            "Frame Number",
            min_value=0,
            max_value=len(results) - 1,
            value=st.session_state.current_frame_index,
            key="frame_slider"
        )
        if frame_index != st.session_state.current_frame_index:
            st.session_state.current_frame_index = frame_index
    
    with col3:
        if st.button("➡️ Next", disabled=st.session_state.current_frame_index >= len(results) - 1):
            st.session_state.current_frame_index = min(len(results) - 1, st.session_state.current_frame_index + 1)
            st.rerun()
    
    # Current frame data
    current_result = results[st.session_state.current_frame_index]
    
    # Display frame info
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Frame:** {current_result['frame_index'] + 1}/{len(results)}")
        st.info(f"**Timestamp:** {format_timestamp(current_result['timestamp'])}")
    with col2:
        st.info(f"**Medibox Count:** {current_result['medibox_count']}")
        st.info(f"**Detections:** {len(current_result['detections'])}")
    
    # Display frame with enhanced bounding boxes
    if current_result['detections']:
        annotated_frame = draw_bounding_boxes(
            current_result['frame'].copy(),
            current_result['detections']
        )
        frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        
        # Enhanced caption with inventory info
        caption = f"Frame {current_result['frame_index'] + 1} | Count: {current_result['medibox_count']} objects | Time: {format_timestamp(current_result['timestamp'])}"
    else:
        frame_rgb = cv2.cvtColor(current_result['frame'], cv2.COLOR_BGR2RGB)
        caption = f"Frame {current_result['frame_index'] + 1} | No objects detected | Time: {format_timestamp(current_result['timestamp'])}"
    
    st.image(frame_rgb, caption=caption, use_container_width=True)
    
    # Detection details
    if current_result['detections']:
        st.subheader("🎯 Detection Details")
        detection_df = pd.DataFrame([
            {
                'Object': i + 1,
                'Label': det['label'],
                'Confidence': f"{det['score']:.2f}",
                'Bounding Box': f"({det['bounding_box'][0]}, {det['bounding_box'][1]}) to ({det['bounding_box'][2]}, {det['bounding_box'][3]})"
            }
            for i, det in enumerate(current_result['detections'])
        ])
        st.dataframe(detection_df, hide_index=True)

def test_single_image(test_image, api_key, detection_prompt):
    """Test the API with a single image"""
    try:
        # Initialize AI client
        ai_client = LandingAIClient(api_key)
        
        # Convert uploaded file to PIL Image
        pil_image = Image.open(test_image)
        
        with st.spinner("🔍 Analyzing test image..."):
            detections = ai_client.detect_objects(pil_image, detection_prompt)
        
        # Display results
        st.success(f"✅ Test completed! Found {len(detections)} medibox objects")
        
        # Show image with bounding boxes
        if detections:
            # Convert PIL to OpenCV format for drawing
            img_array = np.array(pil_image)
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            else:
                img_cv = img_array
            
            annotated_img = draw_bounding_boxes(img_cv.copy(), detections)
            annotated_rgb = cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB)
            st.image(annotated_rgb, caption="Test Image with Detections")
        else:
            st.image(pil_image, caption="Test Image (No detections)")
        
        # Show raw API response
        with st.expander("🔍 Raw API Response"):
            st.json(detections)
            
    except Exception as e:
        st.error(f"❌ Test failed: {str(e)}")

def analysis_history_tab():
    """Display analysis history from database"""
    st.header("📚 Analysis History")
    
    try:
        # Get recent analyses
        analyses = get_analysis_history(limit=20)
        
        if not analyses:
            st.info("No previous analyses found. Complete a video analysis to see history here.")
            return
        
        # Display analyses in a table format
        st.subheader("Recent Analyses")
        
        # Create summary data for display
        history_data = []
        for analysis in analyses:
            history_data.append({
                "ID": analysis.id,
                "Filename": analysis.filename,
                "Date": analysis.created_at.strftime("%Y-%m-%d %H:%M"),
                "Frames": analysis.total_frames,
                "Total Objects": analysis.total_detections,
                "Avg per Frame": f"{analysis.avg_per_frame:.1f}",
                "Max in Frame": analysis.max_in_frame,
                "Processing Time": f"{analysis.processing_time_seconds:.1f}s" if analysis.processing_time_seconds else "N/A"
            })
        
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True)
        
        # Analysis details section
        st.subheader("View Analysis Details")
        
        # Select analysis for detailed view
        selected_id = st.selectbox(
            "Select analysis to view details:",
            options=[a.id for a in analyses],
            format_func=lambda x: f"#{x} - {next(a.filename for a in analyses if a.id == x)}"
        )
        
        if selected_id:
            selected_analysis = get_analysis_by_id(selected_id)
            if selected_analysis:
                # Display detailed analysis information
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Frames", selected_analysis.total_frames)
                    st.metric("File Size", f"{selected_analysis.file_size_mb:.1f} MB")
                
                with col2:
                    st.metric("Total Detections", selected_analysis.total_detections)
                    st.metric("Frame Interval", f"{selected_analysis.frame_interval}s")
                
                with col3:
                    st.metric("Max Objects", selected_analysis.max_in_frame)
                    st.metric("Min Objects", selected_analysis.min_in_frame)
                
                # Show trend chart for this analysis
                if selected_analysis.analysis_results:
                    st.subheader("Detection Trend")
                    
                    # Extract data for plotting
                    frame_data = []
                    for result in selected_analysis.analysis_results:
                        frame_data.append({
                            'Frame': result['frame_index'],
                            'Timestamp': result['timestamp'],
                            'Count': result['medibox_count']
                        })
                    
                    trend_df = pd.DataFrame(frame_data)
                    
                    # Create trend chart
                    fig = px.line(
                        trend_df, 
                        x='Timestamp', 
                        y='Count',
                        title='Medibox Count Over Time',
                        labels={'Timestamp': 'Time (seconds)', 'Count': 'Medibox Count'}
                    )
                    fig.update_traces(mode='lines+markers')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Export option
                if st.button("Export Analysis Data", key=f"export_{selected_id}"):
                    csv_data = export_results_to_csv(selected_analysis.analysis_results)
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"analysis_{selected_id}_{selected_analysis.filename}.csv",
                        mime="text/csv"
                    )
                
                # Delete option (admin only)
                if check_permission("admin"):
                    if st.button("Delete Analysis", key=f"delete_{selected_id}", type="secondary"):
                        if delete_analysis(selected_id):
                            st.success("Analysis deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete analysis")
        
    except Exception as e:
        st.error(f"Error loading analysis history: {str(e)}")
        st.info("Database may not be properly configured. Please check the connection.")

if __name__ == "__main__":
    main()
