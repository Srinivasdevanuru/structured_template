from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import tempfile
import os
import json
import shutil
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid

# Import your existing TIUResumeProcessor class
from tiu_resume_processor_normal import TIUResumeProcessor

# Initialize FastAPI app
app = FastAPI(
    title="TIU Resume Processor API",
    description="Convert JSON resume data to TIU Consulting format PDF",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request validation
class ResumeData(BaseModel):
    candidateName: str
    currentCompany: Optional[str] = ""
    totalExperience: Optional[str] = ""
    currentRole: Optional[str] = ""
    professionalSummary: Optional[str] = ""
    keySkills: Optional[List[str]] = []
    programmingLanguages: Optional[List[str]] = []
    toolsPlatforms: Optional[List[str]] = []
    frameworksLibraries: Optional[List[str]] = []
    methodologies: Optional[List[str]] = []
    databases: Optional[List[str]] = []
    otherSkills: Optional[List[str]] = []
    experienceDetails: Optional[str] = "[]"
    educationDetails: Optional[str] = "[]"
    projectDetails: Optional[str] = "[]"
    certifications: Optional[List[str]] = []
    additionalInformation: Optional[str] = ""

class ProcessResponse(BaseModel):
    message: str
    filename: str
    timestamp: str

# Create temp directory for storing generated files
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with automatic file upload and PDF generation"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TIU Resume Processor API</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6; color: #333; background: #f8f9fa;
            }
            .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 40px; }
            .header h1 { color: #1f4e79; margin-bottom: 10px; }
            .card { 
                background: white; border-radius: 10px; padding: 30px; 
                margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .upload-area {
                border: 2px dashed #007bff; border-radius: 10px; padding: 40px;
                text-align: center; transition: all 0.3s ease; cursor: pointer;
                position: relative; overflow: hidden;
            }
            .upload-area:hover { border-color: #0056b3; background: #f8f9ff; }
            .upload-area.dragover { border-color: #0056b3; background: #e3f2fd; }
            .upload-area.processing { border-color: #ffc107; background: #fffbf0; }
            .btn {
                background: #007bff; color: white; padding: 12px 24px;
                border: none; border-radius: 6px; cursor: pointer;
                font-size: 16px; transition: background 0.3s ease;
                text-decoration: none; display: inline-block;
            }
            .btn:hover { background: #0056b3; }
            .btn-secondary {
                background: #6c757d; margin-left: 10px;
            }
            .btn-secondary:hover { background: #545b62; }
            #fileInput {
                position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                opacity: 0; cursor: pointer; z-index: 10;
            }
            .upload-text { pointer-events: none; }
            .upload-icon { font-size: 48px; margin-bottom: 20px; color: #007bff; }
            .api-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .endpoint { 
                background: #f8f9fa; padding: 20px; border-radius: 8px;
                border-left: 4px solid #007bff;
            }
            .method { 
                font-weight: bold; color: white; padding: 4px 8px;
                border-radius: 4px; font-size: 12px; margin-right: 10px;
            }
            .get { background: #28a745; }
            .post { background: #007bff; }
            .feature-list { list-style: none; }
            .feature-list li { padding: 8px 0; }
            .feature-list li:before { content: "✓"; color: #28a745; font-weight: bold; margin-right: 10px; }
            .json-example {
                background: #2d3748; color: #e2e8f0; padding: 20px;
                border-radius: 8px; overflow-x: auto; font-family: 'Courier New', monospace;
                font-size: 14px; line-height: 1.4;
            }
            .progress { display: none; margin-top: 20px; text-align: center; }
            .progress-bar {
                width: 100%; height: 20px; background: #e9ecef;
                border-radius: 10px; overflow: hidden; margin-bottom: 10px;
            }
            .progress-fill {
                height: 100%; background: #007bff;
                animation: loading 2s infinite ease-in-out;
            }
            @keyframes loading {
                0%, 100% { width: 0%; }
                50% { width: 100%; }
            }
            .status-message {
                padding: 15px; border-radius: 8px; margin-top: 20px;
                font-weight: 500; text-align: center;
            }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .processing { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 TIU Resume Processor</h1>
                <p>Upload JSON resume → Get PDF instantly</p>
            </div>

            <!-- Automatic File Upload Section -->
            <div class="card">
                <h2>📁 Upload JSON Resume</h2>
                <div class="upload-area" id="uploadArea">
                    <div class="upload-text">
                        <div class="upload-icon">📄</div>
                        <h3>Drop your JSON file here or click to browse</h3>
                        <p>PDF will be generated automatically upon upload</p>
                        <p style="font-size: 14px; color: #666; margin-top: 10px;">
                            Supported format: JSON files only
                        </p>
                    </div>
                    <input type="file" id="fileInput" accept=".json">
                </div>
                
                <div class="progress" id="progress">
                    <div class="progress-bar"><div class="progress-fill"></div></div>
                    <p id="progressText">Processing your resume...</p>
                </div>
                
                <div id="statusMessage"></div>
                
                <button type="button" class="btn btn-secondary" onclick="showExample()" style="margin-top: 20px;">
                    Show JSON Example
                </button>
            </div>

            <!-- Features Section -->
            <div class="card">
                <h2>✨ Features</h2>
                <ul class="feature-list">
                    <li>Instant PDF generation on file upload</li>
                    <li>Professional TIU Consulting branded PDF output</li>
                    <li>Automatic JSON validation and error handling</li>
                    <li>Drag & drop file upload support</li>
                    <li>Support for complete resume data including experience, education, skills</li>
                    <li>RESTful API with interactive documentation</li>
                    <li>Cross-platform compatibility</li>
                </ul>
            </div>

            <!-- API Endpoints -->
            <div class="card">
                <h2>🔗 API Endpoints</h2>
                <div class="api-grid">
                    <div class="endpoint">
                        <h3><span class="method post">POST</span>/upload</h3>
                        <p>Upload JSON file and get PDF resume instantly</p>
                    </div>
                    <div class="endpoint">
                        <h3><span class="method post">POST</span>/process</h3>
                        <p>Send JSON data directly via API</p>
                    </div>
                    <div class="endpoint">
                        <h3><span class="method get">GET</span>/docs</h3>
                        <p>Interactive API documentation (Swagger UI)</p>
                    </div>
                    <div class="endpoint">
                        <h3><span class="method get">GET</span>/health</h3>
                        <p>API health check endpoint</p>
                    </div>
                </div>
            </div>

            <!-- Documentation Links -->
            <div class="card">
                <h2>📖 Documentation & Testing</h2>
                <p>Explore and test the API using our interactive documentation:</p>
                <a href="/docs" class="btn">Swagger UI Documentation</a>
                <a href="/redoc" class="btn btn-secondary">ReDoc Documentation</a>
            </div>

            <!-- JSON Example -->
            <div class="card" id="jsonExample" style="display: none;">
                <h2>📝 JSON Format Example</h2>
                <div class="json-example">
{
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
  "otherSkills": ["Project Management", "Team Leadership"],
  "experienceDetails": "[{\"jobTitle\":\"Senior Developer\",\"company\":\"Tech Corp\",\"duration\":\"2020-Present\",\"responsibilities\":[\"Led development team\",\"Architected solutions\"]}]",
  "educationDetails": "[{\"degree\":\"B.S. Computer Science\",\"institution\":\"University\",\"graduationYear\":\"2018\"}]",
  "certifications": ["AWS Certified", "Scrum Master"],
  "additionalInformation": "Patents and publications..."
}
                </div>
            </div>
        </div>

        <script>
            const fileInput = document.getElementById('fileInput');
            const uploadArea = document.getElementById('uploadArea');
            const progress = document.getElementById('progress');
            const progressText = document.getElementById('progressText');
            const statusMessage = document.getElementById('statusMessage');

            // Automatic file processing when file is selected
            fileInput.addEventListener('change', handleFileUpload);

            // Drag and drop functionality
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    handleFileUpload();
                }
            });

            async function handleFileUpload() {
                const file = fileInput.files[0];
                
                if (!file) return;
                
                // Validate file type
                if (!file.name.toLowerCase().endsWith('.json')) {
                    showStatus('Please select a JSON file only.', 'error');
                    return;
                }

                // Show processing state
                uploadArea.classList.add('processing');
                progress.style.display = 'block';
                statusMessage.innerHTML = '';
                progressText.textContent = 'Processing your resume...';
                
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        progressText.textContent = 'Download starting...';
                        
                        // Get the PDF blob and download it
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `${file.name.replace('.json', '')}_resume_${new Date().getTime()}.pdf`;
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        
                        showStatus('✅ PDF generated and downloaded successfully!', 'success');
                        
                        // Reset file input for next upload
                        fileInput.value = '';
                        
                    } else {
                        const error = await response.json();
                        showStatus(`❌ Error: ${error.detail}`, 'error');
                    }
                } catch (error) {
                    showStatus(`❌ Error processing file: ${error.message}`, 'error');
                } finally {
                    progress.style.display = 'none';
                    uploadArea.classList.remove('processing');
                }
            }

            function showStatus(message, type) {
                statusMessage.innerHTML = `<div class="status-message ${type}">${message}</div>`;
                
                // Auto-hide success messages after 5 seconds
                if (type === 'success') {
                    setTimeout(() => {
                        statusMessage.innerHTML = '';
                    }, 5000);
                }
            }
            
            function showExample() {
                const example = document.getElementById('jsonExample');
                example.style.display = example.style.display === 'none' ? 'block' : 'none';
            }
        </script>
    </body>
    </html>
    """

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a JSON file and get PDF resume automatically"""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be a JSON file")
    
    try:
        # Read and validate JSON content
        content = await file.read()
        json_data = json.loads(content.decode('utf-8'))
        
        # Validate required fields
        if not json_data.get('candidateName'):
            raise HTTPException(status_code=400, detail="candidateName is required in JSON")
        
        # Process the resume
        pdf_path = await process_resume_data(json_data)
        
        # Generate filename based on candidate name
        candidate_name = json_data.get('candidateName', 'resume')
        safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_name}_TIU_Resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Return the PDF file
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=filename
        )
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/process")
async def process_json(resume_data: ResumeData):
    """Process JSON resume data directly and return PDF"""
    try:
        # Convert Pydantic model to dict
        json_data = resume_data.model_dump()
        
        # Process the resume
        pdf_path = await process_resume_data(json_data)
        
        # Generate filename
        candidate_name = json_data.get('candidateName', 'resume')
        safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_name}_TIU_Resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Return the PDF file
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=filename
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/api/process", response_model=ProcessResponse)
async def api_process_json(resume_data: ResumeData):
    """Alternative endpoint that returns JSON response instead of file"""
    try:
        json_data = resume_data.model_dump()
        pdf_path = await process_resume_data(json_data)
        
        # Move to permanent location with unique name
        candidate_name = json_data.get('candidateName', 'resume')
        safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        unique_filename = f"{safe_name}_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        permanent_path = os.path.join(TEMP_DIR, unique_filename)
        shutil.move(pdf_path, permanent_path)
        
        return ProcessResponse(
            message="Resume processed successfully",
            filename=unique_filename,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a previously generated PDF file"""
    file_path = os.path.join(TEMP_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type='application/pdf',
        filename=filename
    )

@app.get("/health")
async def health_check():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "TIU Resume Processor API"
    }

@app.get("/stats")
async def get_stats():
    """Get API usage statistics"""
    temp_files = len([f for f in os.listdir(TEMP_DIR) if f.endswith('.pdf')])
    
    return {
        "generated_resumes": temp_files,
        "temp_directory_size": sum(
            os.path.getsize(os.path.join(TEMP_DIR, f)) 
            for f in os.listdir(TEMP_DIR)
        ),
        "uptime": "Running",
        "timestamp": datetime.now().isoformat()
    }

async def process_resume_data(json_data: Dict[str, Any]) -> str:
    """Helper function to process resume data and return PDF path"""
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
        
        return temp_output_path
    
    finally:
        # Clean up input file
        if os.path.exists(temp_input_path):
            os.unlink(temp_input_path)

# Cleanup function to remove old temporary files
@app.on_event("startup")
async def startup_event():
    """Clean up old temporary files on startup"""
    import time
    current_time = time.time()
    for filename in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, filename)
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getctime(file_path)
            # Remove files older than 1 hour
            if file_age > 3600:
                os.remove(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
