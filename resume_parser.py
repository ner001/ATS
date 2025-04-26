import streamlit as st
from dotenv import load_dotenv
from llama_cloud_services import LlamaExtract
from pydantic import BaseModel, Field
from typing import List, Optional
from llama_cloud.core.api_error import ApiError
import os


# Load environment variables
load_dotenv()
api_key = os.environ["LLAMA_CLOUD_API_KEY"]

# Initialize LlamaExtract
llama_extract = LlamaExtract()

# Define all your Pydantic models here (same as your existing code)
class Education(BaseModel):
    institution: str = Field(description="The institution of the candidate")
    degree: str = Field(description="The degree of the candidate")
    start_date: Optional[str] = Field(
        default=None, description="The start date of the candidate's education"
    )
    end_date: Optional[str] = Field(
        default=None, description="The end date of the candidate's education"
    )

class Experience(BaseModel):
    company: str = Field(description="The name of the company")
    title: str = Field(description="The title of the candidate")
    description: Optional[str] = Field(
        default=None, description="The description of the candidate's experience"
    )
    start_date: Optional[str] = Field(
        default=None, description="The start date of the candidate's experience"
    )
    end_date: Optional[str] = Field(
        default=None, description="The end date of the candidate's experience"
    )

class TechnicalSkills(BaseModel):
    programming_languages: List[str] = Field(
        description="The programming languages the candidate is proficient in."
    )
    frameworks: List[str] = Field(
        description="The tools/frameworks the candidate is proficient in, e.g. React, Django, PyTorch, etc."
    )
    skills: List[str] = Field(
        description="Other general skills the candidate is proficient in, e.g. Data Engineering, Machine Learning, etc."
    )

class Resume(BaseModel):
    name: str = Field(description="The name of the candidate")
    phone: str = Field(description="The phone number of the candidate")
    email: str = Field(description="The email address of the candidate")
    links: List[str] = Field(
        description="The links to the candidate's social media profiles"
    )
    experience: List[Experience] = Field(description="The candidate's experience")
    education: List[Education] = Field(description="The candidate's education")
    technical_skills: TechnicalSkills = Field(
        description="The candidate's technical skills"
    )
    key_accomplishments: str = Field(
        description="Summarize the candidates highest achievements."
    )
    certifications: List[str] = Field(
        description="The certifications the candidate has."
    )
    projects: List[str] = Field(description="The projects the candidate has worked on.")
    languages: List[str] = Field(description="The languages the candidate speaks.")
    interests: List[str] = Field(description="The candidate's interests.")
    hobbies: List[str] = Field(description="The candidate's hobbies.")
    awards: List[str] = Field(description="The awards the candidate has received.")
    volunteer_experience: List[str] = Field(
        description="The volunteer experience the candidate has."
    )
    references: List[str] = Field(
        description="The references the candidate has."
    ) 
    summary: str = Field(
        description="A summary of the candidate's experience and skills."
    )
    location: str = Field(
        description="The location of the candidate."
    )

# Initialize or get the agent
def initialize_agent():
    try:
        existing_agent = llama_extract.get_agent(name="resume-screening")
        if existing_agent:
            llama_extract.delete_agent(existing_agent.id)
    except ApiError as e:
        if e.status_code == 404:
            pass
        else:
            raise

    agent = llama_extract.create_agent(name="resume-screening", data_schema=Resume)
    agent.data_schema = Resume
    return agent

# Streamlit UI
def main():
    st.title("Resume Parser")
    st.write("Upload a resume PDF to extract structured information")
    
    agent = initialize_agent()
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        with open("temp_resume.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.spinner("Extracting resume data..."):
            try:
                # Extract data and convert to Pydantic model
                result = agent.extract("temp_resume.pdf")
                
                # Convert the dictionary to your Pydantic model
                if isinstance(result.data, dict):
                    resume_data = Resume(**result.data)
                else:
                    resume_data = result.data
                
                # Display the extracted data
                st.subheader("Extracted Resume Data")
                
                # Basic Info - Now using proper Pydantic model access
                st.header("Basic Information")
                cols = st.columns(3)
                cols[0].write(f"**Name:** {resume_data.name}")
                cols[1].write(f"**Email:** {resume_data.email}")
                cols[2].write(f"**Phone:** {getattr(resume_data, 'phone', 'N/A')}")
                
                # Summary
                st.header("Summary")
                st.write(resume_data.summary)
                
                # Experience
                st.header("Experience")
                for exp in resume_data.experience:
                    st.subheader(f"{exp.title} at {exp.company}")
                    if exp.start_date or exp.end_date:
                        st.caption(f"{exp.start_date or 'N/A'} - {exp.end_date or 'Present'}")
                    if exp.description:
                        st.write(exp.description)
                
                # Education
                st.header("Education")
                for edu in resume_data.education:
                    st.subheader(edu.institution)
                    st.write(edu.degree)
                    if edu.start_date or edu.end_date:
                        st.caption(f"{edu.start_date or 'N/A'} - {edu.end_date or 'Present'}")
                
                # Technical Skills
                st.header("Technical Skills")
                if resume_data.technical_skills:
                    tech_skills = resume_data.technical_skills
                    cols = st.columns(3)
                    cols[0].write("**Programming Languages:**")
                    cols[0].write(", ".join(tech_skills.programming_languages) or "N/A")
                    
                    cols[1].write("**Frameworks:**")
                    cols[1].write(", ".join(tech_skills.frameworks) or "N/A")
                    
                    cols[2].write("**Skills:**")
                    cols[2].write(", ".join(tech_skills.skills) or "N/A")
                
                # Other sections (collapsible)
                with st.expander("Key Accomplishments"):
                    st.write(resume_data.key_accomplishments or "No accomplishments listed")
                
                with st.expander("Projects"):
                    if resume_data.projects:
                        for project in resume_data.projects:
                            st.write(f"- {project}")
                    else:
                        st.write("No projects listed")
                
                with st.expander("Certifications"):
                    if resume_data.certifications:
                        for cert in resume_data.certifications:
                            st.write(f"- {cert}")
                    else:
                        st.write("No certifications listed")
                
                # Show raw JSON data in expander
                with st.expander("View Raw JSON Data"):
                    st.json(resume_data.dict())
                
            except Exception as e:
                st.error(f"Error processing resume: {str(e)}")

if __name__ == "__main__":
    main() 