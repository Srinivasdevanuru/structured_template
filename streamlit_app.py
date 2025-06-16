import streamlit as st
import json
import tempfile
import os
from datetime import datetime
import uuid
from typing import Dict, Any
import base64

# Import your existing TIUResumeProcessor class
from tiu_resume_processor_normal import TIUResumeProcessor

st.set_page_config(
    page_title="TIU Resume Processor",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS for better styling and auto-download functionality
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #1f4e79, #007bff);
        color: white;
        margin-bottom: 2rem;
        border-radius: 10px;
    }
    .upload-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .auto-download-section {
        background: #e8f5e8;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 2px solid #28a745;
        text-align: center;
    }
    .processing {
        background: #fff3cd;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 2px solid #ffc107;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def auto_download_pdf(pdf_bytes: bytes, filename: str):
    """Improved auto-download with HTTP fallback"""
    b64_pdf = base64.b64encode(pdf_bytes).decode()
    
    download_script = f"""
    <script>
        function downloadPDF() {{
            const isSecure = window.location.protocol === 'https:' || window.location.hostname === 'localhost';
            const link = document.createElement('a');
            link.href = 'data:application/pdf;base64,{b64_pdf}';
            link.download = '{filename}';
            
            if (isSecure) {{
                // Secure context: try auto-download
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }} else {{
                // Insecure context: open in new tab
                window.open(link.href, '_blank');
            }}
        }}
        
        setTimeout(downloadPDF, 1000);
    </script>
    """
    
    st.markdown(download_script, unsafe_allow_html=True)

def process_resume_data(json_data: Dict[str, Any]) -> tuple[bytes, str]:
    """Helper function to process resume data and return PDF bytes and filename"""
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_input:
        json.dump(json_data, temp_input, indent=2)
        temp_input_path = temp_input.name
    
    temp_output = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_output_path = temp_output.name
    temp_output.close()
    
    try:
        # Process the resume using your existing class
        processor = TIUResumeProcessor()
        success = processor.process_resume(temp_input_path, temp_output_path)
        
        if not success:
            raise Exception("Failed to generate PDF resume")
        
        # Read PDF file
        with open(temp_output_path, 'rb') as pdf_file:
            pdf_bytes = pdf_file.read()
        
        # Generate filename
        candidate_name = json_data.get('candidateName', 'resume')
        safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_name}_TIU_Resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return pdf_bytes, filename
    
    finally:
        # Clean up temporary files
        if os.path.exists(temp_input_path):
            os.unlink(temp_input_path)
        if os.path.exists(temp_output_path):
            os.unlink(temp_output_path)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 TIU Resume Processor</h1>
        <p>Upload JSON → PDF downloads automatically!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📁 Upload JSON", "✏️ Manual Input", "📖 Documentation"])
    
    with tab1:
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.subheader("Upload JSON Resume File")
        st.write("📤 **Upload your JSON file and the PDF will automatically download to your device!**")
        
        uploaded_file = st.file_uploader(
            "Choose a JSON file",
            type=['json'],
            help="Upload a JSON file - PDF will auto-download!",
            key="json_uploader"
        )
        
        if uploaded_file is not None:
            try:
                # Read and parse JSON
                json_data = json.loads(uploaded_file.read().decode('utf-8'))
                
                # Validate required fields
                if not json_data.get('candidateName'):
                    st.error("❌ candidateName is required in JSON")
                    st.markdown('</div>', unsafe_allow_html=True)
                    return
                
                # Show processing message
                st.markdown('<div class="processing">', unsafe_allow_html=True)
                st.write("🔄 **Processing and generating PDF...**")
                st.write(f"**Candidate:** {json_data.get('candidateName', 'N/A')}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Auto-process the resume
                try:
                    pdf_bytes, filename = process_resume_data(json_data)
                    
                    # Success message
                    st.markdown('<div class="auto-download-section">', unsafe_allow_html=True)
                    st.success("✅ PDF Generated Successfully!")
                    st.write("📥 **Download starting automatically...**")
                    st.write(f"📄 **File:** {filename}")
                    st.write("💡 *If download doesn't start, check your browser's download folder*")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Auto-download the PDF
                    auto_download_pdf(pdf_bytes, filename)
                    
                    # Fallback download button (hidden by default, shows if auto-download fails)
                    with st.expander("Manual Download (if auto-download failed)"):
                        st.download_button(
                            label="📥 Download PDF Manually",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf"
                        )
                        
                except Exception as e:
                    st.error(f"❌ Error processing resume: {str(e)}")
            
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON file format")
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.subheader("Manual Resume Input")
        st.write("📝 **Fill out the form and PDF will automatically download!**")
        
        with st.form("resume_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                candidate_name = st.text_input("Candidate Name*", placeholder="John Doe")
                current_company = st.text_input("Current Company", placeholder="Tech Corp")
                total_experience = st.text_input("Total Experience", placeholder="5+ years")
                current_role = st.text_input("Current Role", placeholder="Senior Developer")
            
            with col2:
                professional_summary = st.text_area("Professional Summary", placeholder="Experienced software developer...")
                key_skills = st.text_area("Key Skills (comma-separated)", placeholder="Python, JavaScript, React")
                programming_languages = st.text_area("Programming Languages", placeholder="Python, JavaScript, Java")
                certifications = st.text_area("Certifications", placeholder="AWS Certified, Scrum Master")
            
            # Additional fields
            st.subheader("Additional Information")
            
            col3, col4 = st.columns(2)
            with col3:
                tools_platforms = st.text_area("Tools & Platforms", placeholder="Git, Docker, AWS")
                frameworks_libraries = st.text_area("Frameworks & Libraries", placeholder="React, Django, FastAPI")
            
            with col4:
                methodologies = st.text_area("Methodologies", placeholder="Agile, Scrum")
                databases = st.text_area("Databases", placeholder="PostgreSQL, MongoDB")
            
            experience_details = st.text_area(
                "Experience Details (JSON format)", 
                placeholder='[{"jobTitle":"Senior Developer","company":"Tech Corp","duration":"2020-Present","responsibilities":["Led development team","Architected solutions"]}]'
            )
            
            education_details = st.text_area(
                "Education Details (JSON format)",
                placeholder='[{"degree":"B.S. Computer Science","institution":"University","graduationYear":"2018"}]'
            )
            
            additional_info = st.text_area("Additional Information", placeholder="Patents and publications...")
            
            # Auto-generate and download on submit
            submitted = st.form_submit_button("🚀 Generate PDF (Auto-Download)", type="primary", use_container_width=True)
            
            if submitted:
                if not candidate_name:
                    st.error("❌ Candidate Name is required")
                else:
                    # Prepare JSON data
                    json_data = {
                        "candidateName": candidate_name,
                        "currentCompany": current_company,
                        "totalExperience": total_experience,
                        "currentRole": current_role,
                        "professionalSummary": professional_summary,
                        "keySkills": [skill.strip() for skill in key_skills.split(',') if skill.strip()],
                        "programmingLanguages": [lang.strip() for lang in programming_languages.split(',') if lang.strip()],
                        "toolsPlatforms": [tool.strip() for tool in tools_platforms.split(',') if tool.strip()],
                        "frameworksLibraries": [fw.strip() for fw in frameworks_libraries.split(',') if fw.strip()],
                        "methodologies": [method.strip() for method in methodologies.split(',') if method.strip()],
                        "databases": [db.strip() for db in databases.split(',') if db.strip()],
                        "experienceDetails": experience_details or "[]",
                        "educationDetails": education_details or "[]",
                        "certifications": [cert.strip() for cert in certifications.split(',') if cert.strip()],
                        "additionalInformation": additional_info
                    }
                    
                    # Show processing message
                    st.markdown('<div class="processing">', unsafe_allow_html=True)
                    st.write("🔄 **Generating PDF...**")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    try:
                        pdf_bytes, filename = process_resume_data(json_data)
                        
                        # Success message
                        st.markdown('<div class="auto-download-section">', unsafe_allow_html=True)
                        st.success("✅ PDF Generated Successfully!")
                        st.write("📥 **Download starting automatically...**")
                        st.write(f"📄 **File:** {filename}")
                        st.write("💡 *If download doesn't start, check your browser's download folder*")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Auto-download the PDF
                        auto_download_pdf(pdf_bytes, filename)
                        
                        # Fallback download button
                        with st.expander("Manual Download (if auto-download failed)"):
                            st.download_button(
                                label="📥 Download PDF Manually",
                                data=pdf_bytes,
                                file_name=filename,
                                mime="application/pdf"
                            )
                            
                    except Exception as e:
                        st.error(f"❌ Error processing resume: {str(e)}")
    
    with tab3:
        st.subheader("📖 Documentation")
        
        st.markdown("""
        ### ⚡ Automatic Download Features
        - ✅ **Instant Auto-Download** - PDF downloads automatically to your device
        - ✅ **No Button Clicks** - Just upload JSON or submit form
        - ✅ **Browser Compatible** - Works in Chrome, Firefox, Safari, Edge
        - ✅ Professional TIU Consulting branded PDF output
        - ✅ Automatic JSON validation and error handling
        - ✅ Secure HTTPS processing
        
        ### How It Works
        1. **Upload JSON** → PDF auto-generates → **Automatic download to your Downloads folder**
        2. **Fill Form** → Submit → PDF auto-generates → **Automatic download to your Downloads folder**
        3. **No manual steps** - everything happens automatically!
        
        ### Browser Notes
        - 📁 PDF files download to your default Downloads folder
        - 🔒 Some browsers may ask for download permission (first time only)
        - 💡 If auto-download fails, use the manual download option
        """)
        
        st.subheader("JSON Format Example")
        example_json = {
            "candidateName": "John Doe",
            "currentCompany": "Tech Corp",
            "totalExperience": "5+ years",
            "currentRole": "Senior Developer",
            "professionalSummary": "Experienced software developer...",
            "keySkills": ["Python", "JavaScript", "React"],
            "programmingLanguages": ["Python", "JavaScript", "Java"],
            "toolsPlatforms": ["Git", "Docker", "AWS"],
            "frameworksLibraries": ["React", "Django", "FastAPI"],
            "methodologies": ["Agile", "Scrum"],
            "databases": ["PostgreSQL", "MongoDB"],
            "experienceDetails": '[{"jobTitle":"Senior Developer","company":"Tech Corp","duration":"2020-Present","responsibilities":["Led development team","Architected solutions"]}]',
            "educationDetails": '[{"degree":"B.S. Computer Science","institution":"University","graduationYear":"2018"}]',
            "certifications": ["AWS Certified", "Scrum Master"],
            "additionalInformation": "Patents and publications..."
        }
        
        st.json(example_json)

if __name__ == "__main__":
    main()
