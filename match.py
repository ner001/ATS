import streamlit as st
import requests

# Set page config
st.set_page_config(page_title="Llama3 Resume Entity Extractor", layout="centered")

st.title("📄 Resume & Job Description Entity Extractor ")

# Upload files
resume_file = st.file_uploader("Upload Resume File", type=["txt", "pdf"])
job_file = st.file_uploader("Upload Job Description File", type=["txt", "pdf"])

# Function to read file content
def read_file(file):
    if file is not None:
        return file.read().decode("utf-8", errors="ignore")
    return ""

# Generate on button click
if st.button("🔍 Analyze"):
    resume_text = read_file(resume_file)
    job_text = read_file(job_file)

    if not resume_text or not job_text:
        st.error("Please upload both files.")
    else:
        with st.spinner("Generating response using Llama3..."):

            # Format the combined text
            combined_text = f"\n\n=== Resume ===\n{resume_text}\n\n=== Job Description ===\n{job_text}"

            # Build prompt
            prompt = f"""

You are an AI assistant designed to evaluate how well a candidate fits a specific job role based on their resume and a structured job description. The job description includes multiple requirement categories, each with an importance weight. Your task is to extract claims about how well the candidate meets each requirement and present them in a structured JSON format.

## Instructions:

1. Analyze the **Resume Data** and the **Job Description Data** provided below.
2. For each requirement (skill, education, experience, soft skill, etc.) in the job description, evaluate the degree to which the candidate meets the requirement based on the resume.
3. For each requirement, extract and return the following fields:
   - **requirement**: the original job requirement or skill.
   - **match**: choose one of the following: "FULL", "PARTIAL","NEAR FULL" or "NONE".
   - **evidence**: a short explanation or quote from the resume that supports your evaluation.
   - **source**: "RESUME" if the evidence is explicitly present in the resume or "Inference"
   - **importance**: put the corresponding weight from the job description file
PLEASE MAKE SURE TO PUT ONLY THINGS THAT OCCUR IN THE RESUME DATA and Be very critical in your assessment.
4. Output the result in this JSON format:
[
  {{
    "requirement": "",
    "match": "",
    "evidence": "",
    "source": "",
    "importance": 0.0
  }},
  ...
]

## Resume Data:
{resume_text}

## Job Description Data:
{job_text}

"""


            # Send request to Ollama
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "Llama3:latest",
                    "prompt": prompt,
                    "stream": False
                }
            )

            if response.status_code == 200:
                result = response.json()["response"]
                st.success("✅ Extraction complete!")
                st.text_area("🧠 LLaMA 3 Output", result, height=400)

                # Save to file
                with open("llama_output.txt", "w", encoding="utf-8") as f:
                    f.write(result)
                st.download_button("💾 Download Result", result, file_name="llama_output.txt")
            else:
                st.error("❌ Error generating response. Is Ollama running with the LLaMA 3 model?")