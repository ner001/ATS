import streamlit as st
import requests

# Set page config
st.set_page_config(page_title="Llama3 Resume Entity Extractor", layout="centered")

st.title("📄 Resume & Job Description Entity Extractor")

# Upload files
resume_file = st.file_uploader("Upload Resume File", type=["txt", "pdf"])
job_description = st.file_uploader("Upload Job Description File", type=["txt", "pdf"])
llama_output = st.file_uploader("Upload Job Matching File", type=["txt", "pdf"])

# Function to read file content
def read_file(file):
    if file is not None:
        return file.read().decode("utf-8", errors="ignore")
    return ""

# Generate on button click
if st.button("🔍 Analyze"):
    resume_text = read_file(resume_file)
    job_text = read_file(job_description)
    matching_text = read_file(llama_output)

    if not resume_text or not job_text:
        st.error("Please upload both the resume and job description files.")
    else:
        with st.spinner("Generating response using LLaMA 3..."):

            # Build prompt with formatting enforcement
            prompt = f"""




You are a professional HR analyst and your ONLY task is to output a structured evaluation in **valid JSON format only**.

Follow this exact format:
{{
  "title": "string - Candidate name and job title",
  "summary": "string - Executive summary of the candidate’s fit",
  "match_score": float,
  "score_explanation": "string - Explain the score, including penalties or mismatches",
  "findings": [
    {{
      "summary": "string - Skill or requirement",
      "explanation": "string - Why the candidate meets or lacks this requirement",
      "score": integer (0–100)
    }},
    ...
  ]
}}

Strict rules:
- Output **only** valid JSON. Do NOT write explanations, markdown, or any prose before or after.
- `match_score` must be between 0 and 1 (e.g., 0.72 means 72% match).
- Give 5 to 10 findings with thoughtful scoring.
- Base your judgment on job description, resume, and the match breakdown file.

--MATCHING FILE--
{matching_text}

--RESUME--
{resume_text}

--JOB DESCRIPTION--
{job_text}

"""


            # Send request to Ollama
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3",
                    "prompt": prompt,
                    "stream": False
                }
            )

            if response.status_code == 200:
                result = response.json().get("response", "").strip()
                st.success("✅ Extraction complete!")
                st.text_area("🧠 LLaMA 3 Output (JSON)", result, height=400)

                # Save to file
                with open("llama_output.json", "w", encoding="utf-8") as f:
                    f.write(result)
                st.download_button("💾 Download Result", result, file_name="llama_output.json")
            else:
                st.error("❌ Error generating response. Is Ollama running with the LLaMA 3 model?")