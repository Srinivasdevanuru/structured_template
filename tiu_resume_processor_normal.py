#!/usr/bin/env python3
"""
TIU Consulting Resume Processor - MODIFIED FOR YOUR INPUT FORMAT
Transforms candidate resume data into TIU Consulting template format
"""

import json
import sys
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.colors import black, blue, grey
from reportlab.platypus.flowables import HRFlowable


class TIUResumeProcessor:
    """Main class for processing TIU Consulting resumes according to template specifications"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        self.page_width = A4[0]
        self.page_height = A4[1]
        self.margin = 72  
    
    def setup_custom_styles(self):
        """Setup custom styles matching TIU Consulting template"""
        
        # Title style for main header
        self.styles.add(ParagraphStyle(
            name='TIUTitle',
            parent=self.styles['Title'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#1f4e79'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=12,
            spaceAfter=10,
            spaceBefore=15,
            textColor=colors.HexColor('#1f4e79'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='TIUBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Table text style 
        self.styles.add(ParagraphStyle(
            name='TableText',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leading=11, 
            spaceAfter=0,
            spaceBefore=0
        ))
        
        # Table header style
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            leading=11,
            spaceAfter=0,
            spaceBefore=0
        ))
        
        # Bullet point style
        self.styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=3,
            leftIndent=20,
            alignment=TA_LEFT,
            fontName='Helvetica'
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=grey,
            fontName='Helvetica'
        ))
    
    def transform_input_data(self, raw_data):
        """Transform the input JSON structure to match expected format"""
        
        # Parse JSON strings in the input data
        experience_details = []
        education_details = []
        project_details = []
        
        try:
            if raw_data.get('experienceDetails'):
                experience_details = json.loads(raw_data['experienceDetails'])
        except (json.JSONDecodeError, TypeError):
            experience_details = []
        
        try:
            if raw_data.get('educationDetails'):
                education_details = json.loads(raw_data['educationDetails'])
        except (json.JSONDecodeError, TypeError):
            education_details = []
            
        try:
            if raw_data.get('projectDetails'):
                project_details = json.loads(raw_data['projectDetails'])
        except (json.JSONDecodeError, TypeError):
            project_details = []
        
        # Transform to expected structure
        transformed_data = {
            'candidate_info': {
                'name': raw_data.get('candidateName', ''),
                'current_company': raw_data.get('currentCompany', ''),
                'total_experience': raw_data.get('totalExperience', ''),
                'current_role': raw_data.get('currentRole', ''),
                'key_skills': ', '.join(raw_data.get('keySkills', [])),
                'notice_period': '',  # Not in input data
                'current_ctc': '',    # Not in input data
                'expected_ctc': '',   # Not in input data
                'shortlisting_reason': ''  # Not in input data
            },
            'professional_summary': raw_data.get('professionalSummary', ''),
            'technical_skills': {
                'programming_languages': raw_data.get('programmingLanguages', []),
                'tools_and_platforms': raw_data.get('toolsPlatforms', []),
                'frameworks_and_libraries': raw_data.get('frameworksLibraries', []),
                # Check for both "methodologies" and "methodolgies"
                'methodologies': raw_data.get('methodologies', raw_data.get('methodolgies', [])),
                'databases': raw_data.get('databases', []),
                'other': raw_data.get('otherSkills', [])
            },
            'professional_experience': experience_details,
            'education': education_details,
            'certifications': raw_data.get('certifications', []),
            'projects': project_details,
            'additional_information': raw_data.get('additionalInformation', '')
        }
        
        return transformed_data
    
    def load_json_data(self, json_file_path):
        """Load and validate resume data from JSON file"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                raw_data = json.load(file)
            
            # Transform the data to expected format
            data = self.transform_input_data(raw_data)
            
            return data
        except FileNotFoundError:
            print(f"Error: JSON file '{json_file_path}' not found.")
            return None
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format in '{json_file_path}': {e}")
            return None
    
    def create_header_section(self, data):
        """Create the TIU Consulting header with properly formatted table"""
        story = []
        
        # Main title
        story.append(Paragraph("TIUConsulting – Candidate Profile", self.styles['TIUTitle']))
        story.append(Spacer(1, 15))
        
        # Candidate information table - FIXED LAYOUT
        candidate_info = data.get('candidate_info', {})
        
        # Create table data in proper 2x2 grid format
        table_data = [
            [Paragraph('Candidate Name:', self.styles['TableHeader']), 
             Paragraph(candidate_info.get('name', ''), self.styles['TableText']),
             Paragraph('Current Company:', self.styles['TableHeader']), 
             Paragraph(candidate_info.get('current_company', ''), self.styles['TableText'])],
            
            [Paragraph('Total Experience:', self.styles['TableHeader']), 
             Paragraph(candidate_info.get('total_experience', ''), self.styles['TableText']),
             Paragraph('Notice Period:', self.styles['TableHeader']), 
             Paragraph(candidate_info.get('notice_period', 'N/A'), self.styles['TableText'])],
            
            [Paragraph('Current Role:', self.styles['TableHeader']), 
             Paragraph(candidate_info.get('current_role', ''), self.styles['TableText']),
             Paragraph('Current CTC:', self.styles['TableHeader']), 
             Paragraph(candidate_info.get('current_ctc', 'N/A'), self.styles['TableText'])],
            
            [Paragraph('Key Skills:', self.styles['TableHeader']), 
             Paragraph(candidate_info.get('key_skills', ''), self.styles['TableText']),
             Paragraph('Expected CTC:', self.styles['TableHeader']), 
             Paragraph(candidate_info.get('expected_ctc', 'N/A'), self.styles['TableText'])],
            
            [Paragraph('Shortlisting Reason:', self.styles['TableHeader']), 
             '', '', '']
        ]
        
        # Add shortlisting reason as a separate row that spans all columns
        if candidate_info.get('shortlisting_reason'):
            table_data.append([Paragraph(candidate_info.get('shortlisting_reason', ''), self.styles['TableText']), 
                              '', '', ''])
        
        # Better column width distribution
        col_widths = [3.2*cm, 5.3*cm, 3.2*cm, 5.3*cm]
        info_table = Table(table_data, colWidths=col_widths)
        
        # Enhanced table styling with proper borders
        table_style = [
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]
        
        # Handle shortlisting reason spanning
        if len(table_data) > 5:
            table_style.extend([
                ('SPAN', (1, 4), (3, 4)),  # Empty cells in shortlisting reason label row
                ('SPAN', (0, 5), (3, 5)),  # Shortlisting reason content spans all columns
            ])
        
        info_table.setStyle(TableStyle(table_style))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def create_professional_summary(self, data):
        """Create professional summary section"""
        story = []
        
        story.append(Paragraph("PROFESSIONAL SUMMARY", self.styles['SectionHeader']))
        
        summary = data.get('professional_summary', 'No professional summary available.')
        story.append(Paragraph(summary, self.styles['TIUBody']))
        story.append(Spacer(1, 15))
        
        return story
    
    def create_technical_skills(self, data):
        """Create technical skills section with proper table formatting"""
        story = []
        
        story.append(Paragraph("TECHNICAL SKILLS", self.styles['SectionHeader']))
        
        skills = data.get('technical_skills', {})
        
        # Helper function to truncate long skill lists
        def format_skills_list(skills_list, max_length=80):
            if not skills_list:
                return 'N/A'
            skills_text = ', '.join(skills_list)
            if len(skills_text) > max_length:
                # Find a good break point
                truncated = skills_text[:max_length]
                last_comma = truncated.rfind(', ')
                if last_comma > 0:
                    truncated = truncated[:last_comma]
                return truncated + '...'
            return skills_text
        
        # Create skills table data with proper formatting
        table_data = [
            [Paragraph('Programming Languages:', self.styles['TableHeader']), 
             Paragraph(format_skills_list(skills.get('programming_languages', [])), self.styles['TableText']),
             Paragraph('Tools & Platforms:', self.styles['TableHeader']), 
             Paragraph(format_skills_list(skills.get('tools_and_platforms', [])), self.styles['TableText'])],
            
            [Paragraph('Frameworks & Libraries:', self.styles['TableHeader']), 
             Paragraph(format_skills_list(skills.get('frameworks_and_libraries', [])), self.styles['TableText']),
             Paragraph('Methodologies:', self.styles['TableHeader']), 
             Paragraph(format_skills_list(skills.get('methodologies', [])), self.styles['TableText'])],
            
            [Paragraph('Databases:', self.styles['TableHeader']), 
             Paragraph(format_skills_list(skills.get('databases', [])), self.styles['TableText']),
             Paragraph('Other:', self.styles['TableHeader']), 
             Paragraph(format_skills_list(skills.get('other', [])), self.styles['TableText'])]
        ]
        
        # Column widths for better fit
        col_widths = [3.5*cm, 4.5*cm, 3.5*cm, 5.5*cm]
        skills_table = Table(table_data, colWidths=col_widths)
        
        # Apply table styling with borders
        skills_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(skills_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def create_professional_experience(self, data):
        """Create professional experience section"""
        story = []
        
        story.append(Paragraph("PROFESSIONAL EXPERIENCE", self.styles['SectionHeader']))
        
        experiences = data.get('professional_experience', [])
        
        for i, exp in enumerate(experiences):
            # Job header
            job_title = exp.get('jobTitle', 'N/A')
            company = exp.get('company', 'N/A')
            duration = exp.get('duration', 'N/A')
            location = exp.get('location', '')
            
            if location:
                job_header = f"<b>{job_title} | {company} | {duration} | {location}</b>"
            else:
                job_header = f"<b>{job_title} | {company} | {duration}</b>"
            
            story.append(Paragraph(job_header, self.styles['TIUBody']))
            story.append(Spacer(1, 6))
            
            # Responsibilities
            responsibilities = exp.get('responsibilities', [])
            for responsibility in responsibilities:
                if responsibility.strip():  # Skip empty responsibilities
                    story.append(Paragraph(f"• {responsibility}", self.styles['BulletPoint']))
            
            # Add extra space between jobs
            if i < len(experiences) - 1:
                story.append(Spacer(1, 15))
        
        story.append(Spacer(1, 20))
        return story
    
    def create_education(self, data):
        """Create education section"""
        story = []
        
        story.append(Paragraph("EDUCATION", self.styles['SectionHeader']))
        
        education = data.get('education', [])
        
        for edu in education:
            degree = edu.get('degree', 'N/A')
            institution = edu.get('institution', 'N/A')
            graduation_year = edu.get('graduationYear', 'N/A')
            location = edu.get('location', '')
            
            story.append(Paragraph(f"<b>{degree}</b>", self.styles['TIUBody']))
            story.append(Paragraph(institution, self.styles['TIUBody']))
            
            if location:
                story.append(Paragraph(f"{graduation_year} | {location}", self.styles['TIUBody']))
            else:
                story.append(Paragraph(str(graduation_year), self.styles['TIUBody']))
            
            # Relevant coursework if available
            coursework = edu.get('relevantCoursework', '')
            if coursework:
                story.append(Paragraph(f"<b>Relevant Coursework:</b> {coursework}", self.styles['TIUBody']))
            
            story.append(Spacer(1, 10))
        
        story.append(Spacer(1, 15))
        return story
    
    def create_certifications(self, data):
        """Create certifications section"""
        story = []
        certifications = data.get('certifications', [])
        
        if certifications:
            story.append(Paragraph("CERTIFICATIONS & TRAINING", self.styles['SectionHeader']))
            
            for cert in certifications:
                if cert.strip():  # Skip empty certifications
                    # Remove extra quotes if present
                    clean_cert = cert.strip().strip('"').strip("'")
                    story.append(Paragraph(f"• {clean_cert}", self.styles['BulletPoint']))
            
            story.append(Spacer(1, 15))
        
        return story
    
    def create_projects(self, data):
        """Create projects section"""
        story = []
        projects = data.get('projects', [])
        
        if projects:
            story.append(Paragraph("PROJECTS", self.styles['SectionHeader']))
            
            for project in projects:
                # Check for "projectName" first; fall back to "name" if not present
                name = project.get('projectName', project.get('name', 'N/A'))
                story.append(Paragraph(f"<b>{name}</b>", self.styles['TIUBody']))
                
                technologies = project.get('technologies', [])
                if technologies:
                    tech_text = ', '.join(technologies)
                    story.append(Paragraph(f"<b>Technologies:</b> {tech_text}", self.styles['TIUBody']))
                
                description = project.get('description', '')
                if description:
                    story.append(Paragraph(description, self.styles['TIUBody']))
                
                story.append(Spacer(1, 12))
            
            story.append(Spacer(1, 10))
        
        return story
    
    def create_additional_information(self, data):
        """Create additional information section"""
        story = []
        additional_info = data.get('additional_information', '')
        
        if additional_info:
            story.append(Paragraph("ADDITIONAL INFORMATION", self.styles['SectionHeader']))
            story.append(Paragraph(additional_info, self.styles['TIUBody']))
            story.append(Spacer(1, 15))
        
        return story
    
    def create_footer(self):
        """Create footer for each page"""
        return Paragraph("PRIVATE & CONFIDENTIAL | TIUConsulting", self.styles['Footer'])
    
    def generate_pdf(self, data, output_path):
        """Generate complete PDF document"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin + 30  
        )
        
        story = []
        
        # Build document sections
        story.extend(self.create_header_section(data))
        story.extend(self.create_professional_summary(data))
        story.extend(self.create_technical_skills(data))
        story.extend(self.create_professional_experience(data))
        story.extend(self.create_education(data))
        story.extend(self.create_certifications(data))
        story.extend(self.create_projects(data))
        story.extend(self.create_additional_information(data))
        
        # Add footer
        story.append(Spacer(1, 20))
        story.append(self.create_footer())
        
        # Build PDF
        doc.build(story)
        print(f"PDF generated successfully: {output_path}")
    
    def process_resume(self, json_file_path, output_path):
        """Main processing method"""
        print(f"Processing resume: {json_file_path}")
        
        # Load and validate data
        data = self.load_json_data(json_file_path)
        if not data:
            return False
        
        # Generate PDF
        try:
            self.generate_pdf(data, output_path)
            return True
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False


def main():
    """Main function for command line usage"""
    if len(sys.argv) != 3:
        print("Usage: python3 tiu_resume_processor.py <input.json> <output.pdf>")
        print("Example: python3 tiu_resume_processor.py kurt_matis_data.json kurt_matis_resume.pdf")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Validate input file
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)
    
    # Create output directory if needed
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process resume
    processor = TIUResumeProcessor()
    success = processor.process_resume(input_file, output_file)
    
    if success:
        print("Resume processing completed successfully!")
        sys.exit(0)
    else:
        print("Resume processing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()