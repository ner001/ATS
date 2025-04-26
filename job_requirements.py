import streamlit as st
import requests
import json
import time
import re

def generate_job_requirements(job_title, model="llama3:latest"):
    """Generate structured job requirements using Ollama API."""
    url = "http://localhost:11434/api/generate"
    prompt = f"""    -Goal-  
            You are a job description parser. Your task is to extract and structure the requirements from a job description.
            Given a job description for a {job_title} position, extract and structure the requirements into the following JSON format with weights (0-1) and penalties.  
            -Output Requirements-  
            1. **Job Type**: Use the provided `{job_title}`.  
            2. **Categories**: Organize requirements into:  
            - `Core skills` (critical for the role)  
            - `Technical skills` (tools/frameworks)  
            - `Experience requirements` (years/projects)  
            - `Education requirements` (degrees/certifications)  
            - `Soft skills` (communication, teamwork)  
            3. **Weights**: Assign each item a weight between 0 (least important) and 1 (most important).  
            4. **Penalties**: Define penalties for missing requirements (e.g., `missing_core_skills: 20`). 

            -Important Instructions-
            - Be COMPREHENSIVE: Include ALL possible skills and keywords that might appear on resumes for this role
            - For technical roles, list specific technologies, frameworks, and tools (e.g., for AI Engineer, include TensorFlow, PyTorch, Keras, scikit-learn, etc.)
            - For all roles, include industry-specific terminology and certifications
            - Create an IDEAL requirements profile that can be used as a benchmark for evaluating candidate resumes
            - Include at least 8-10 items in each category whenever relevant
            - Assign realistic weights that reflect actual industry priorities for this role
            - Make penalties proportional to the importance of each category

            Output must follow this exact format:
            ```json
            {{
            "job_type": "{job_title}",
            "importance_weights": {{
                "Core skills": [
                {{
                    "skill": "<exact_skill_name>",
                    "weight": <0.0-1.0>
                }}
                ],
                "Technical skills": [
                {{
                    "skill": "<exact_skill_name>",
                    "weight": <0.0-1.0>
                }}
                ],
                "Experience requirements": [
                {{
                    "requirement": "<exact_experience>",
                    "weight": <0.0-1.0>
                }}
                ],
                "Education requirements": [
                {{
                    "requirement": "<exact_education>",
                    "weight": <0.0-1.0>
                }}
                ],
                "Soft skills": [
                {{
                    "skill": "<exact_soft_skill>",
                    "weight": <0.0-1.0>
                }}
                ]
            }},
            "penalties": {{
                "missing_core_skills": <points>,
                "missing_technical_skills": <points>,
                "missing_experience": <points>,
                "missing_education": <points>
            }}
            }}
            ```
            
            Rules:
            - Return ONLY the JSON block
            - No explanations or comments
            - Weights must be between 0.0 and 1.0
            - Penalties must be integers
            - Ensure valid JSON format with proper quotes and commas
            - This output will be used directly for resume screening, so be thorough and precise"""
        
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        json_response = response.json()
        
        # Extract the response text
        full_response = json_response.get("response", "")
        
        # Try to find JSON between triple backticks if they exist
        json_match = re.search(r'```json\n(.*?)\n```', full_response, re.DOTALL)
        if not json_match:
            # If no backticks, try to find JSON content directly (looking for opening brace)
            json_match = re.search(r'({.*})', full_response, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
            # Clean up any remaining markdown artifacts
            json_str = json_str.replace('```', '').strip()
            try:
                requirements = json.loads(json_str)
                return requirements, None
            except json.JSONDecodeError as e:
                return None, f"Error: Model returned invalid JSON. Details:\n{str(e)}\nRaw response:\n{full_response}"
        else:
            return None, f"Error: Could not find JSON in response. Raw response:\n{full_response}"

    except requests.exceptions.RequestException as e:
        return None, f"Error connecting to Ollama: {e}\nMake sure Ollama is running and the model is loaded."
    except Exception as e:
        return None, f"Unexpected error: {e}"


def display_job_requirements(requirements):
    """Display the job requirements in a structured format."""
    if not requirements:
        st.error("No requirements to display")
        return

    job_type = requirements.get('job_type', 'Unknown Position')
    st.subheader(f"Job Requirements for: {job_type}")

    st.header("Importance Weights")
    weights = requirements.get("importance_weights", {})

    for category, items in weights.items():
        with st.expander(f"📌 {category}", expanded=True):
            if not items:
                st.write("No items in this category")
                continue
                
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        skill = item.get("skill", "") or item.get("requirement", "")
                        weight = item.get("weight", 0)
                        # Create a colored bar to visualize weight
                        col1, col2 = st.columns([3, 7])
                        with col1:
                            st.write(f"**{skill}**")
                        with col2:
                            st.progress(weight)
                            st.caption(f"Weight: {weight}")
                    else:
                        st.write(f"- {item}")
            else:
                st.write("Invalid format for this category")

    st.header("Penalties for Missing Requirements")
    penalties = requirements.get("penalties", {})

    if penalties:
        cols = st.columns(len(penalties))
        for i, (penalty, points) in enumerate(penalties.items()):
            cols[i].metric(
                label=penalty.replace("_", " ").title(),
                value=f"-{points} pts",
                delta=None,
                delta_color="inverse"
            )
    else:
        st.warning("No penalty information available")

    with st.expander("📄 View Raw JSON"):
        st.code(json.dumps(requirements, indent=2), language="json")


def edit_job_requirements(requirements):
    """Allow editing of job requirements."""
    st.header("Edit Job Requirements")

    edited_requirements = dict(requirements)
    
    # Allow editing the job title
    new_job_title = st.text_input(
        "Job Title",
        value=requirements.get("job_type", ""),
        key="edit_job_title"
    )
    edited_requirements["job_type"] = new_job_title

    weights = requirements.get("importance_weights", {})
    penalties = requirements.get("penalties", {})

    new_weights = {}

    # Create tabs for different categories
    tabs = st.tabs([f"📌 {category}" for category in weights.keys()])
    
    for i, (category, items) in enumerate(weights.items()):
        with tabs[i]:
            new_items = []

            if isinstance(items, list):
                for j, item in enumerate(items):
                    if isinstance(item, dict):
                        with st.container():
                            st.markdown(f"##### Item {j+1}")
                            col1, col2, col3, col4 = st.columns([3, 3, 2, 1])
                            with col1:
                                key = "skill" if "skill" in item else "requirement"
                                updated_key = st.selectbox(
                                    "Type",
                                    ["skill", "requirement"],
                                    index=0 if key == "skill" else 1,
                                    key=f"{category}_{j}_type"
                                )
                            with col2:
                                updated_value = st.text_input(
                                    "Name",
                                    value=item.get(key, ""),
                                    key=f"{category}_{j}_name"
                                )
                            with col3:
                                updated_weight = st.slider(
                                    "Weight",
                                    min_value=0.0,
                                    max_value=1.0,
                                    value=float(item.get("weight", 0.5)),
                                    step=0.1,
                                    key=f"{category}_{j}_weight"
                                )
                            with col4:
                                delete = st.checkbox("Delete", key=f"{category}_{j}_delete")
                            
                            if not delete and updated_value:
                                new_item = {updated_key: updated_value, "weight": updated_weight}
                                new_items.append(new_item)
                            
                            st.divider()

            with st.expander(f"➕ Add New Item to {category}"):
                new_key = st.selectbox(
                    "Type",
                    ["skill", "requirement"],
                    key=f"{category}_new_type"
                )
                new_value = st.text_input("Name", key=f"{category}_new_name")
                new_weight = st.slider(
                    "Weight",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.1,
                    key=f"{category}_new_weight"
                )
                if st.button("Add", key=f"{category}_add"):
                    if new_value:
                        new_items.append({new_key: new_value, "weight": new_weight})
                        st.experimental_rerun()

            new_weights[category] = new_items

    edited_requirements["importance_weights"] = new_weights

    st.subheader("⚠️ Edit Penalties")
    
    penalties_container = st.container()
    with penalties_container:
        new_penalties = {}
        for penalty, value in penalties.items():
            cols = st.columns([4, 2, 1])
            with cols[0]:
                updated_penalty = st.text_input(
                    "Penalty",
                    value=penalty,
                    key=f"penalty_{penalty}_name"
                )
            with cols[1]:
                updated_value = st.number_input(
                    "Points",
                    value=int(value),
                    min_value=0,
                    key=f"penalty_{penalty}_value"
                )
            with cols[2]:
                delete = st.checkbox("Delete", key=f"penalty_{penalty}_delete")
            
            if not delete:
                new_penalties[updated_penalty] = updated_value

    with st.expander("➕ Add New Penalty"):
        cols = st.columns([3, 2, 1])
        with cols[0]:
            new_penalty = st.text_input("New Penalty Name", key="new_penalty_name")
        with cols[1]:
            new_penalty_value = st.number_input(
                "Points",
                min_value=0,
                value=10,
                key="new_penalty_points"
            )
        with cols[2]:
            if st.button("Add", key="add_penalty"):
                if new_penalty:
                    new_penalties[new_penalty] = new_penalty_value
                    st.experimental_rerun()

    edited_requirements["penalties"] = new_penalties

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Changes", type="primary"):
            st.success("✅ Job requirements updated successfully!")
            return edited_requirements
    with col2:
        if st.button("❌ Cancel", key="cancel_edit"):
            return requirements

    return None


def main():
    """Main application function."""
    st.set_page_config(
        page_title="Job Requirements Generator",
        page_icon="💼",
        layout="wide",
    )

    st.title("💼 Job Requirements Generator")
    st.markdown("Generate structured job requirements for any position using AI")

    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model selection with more information
        st.subheader("Model Selection")
        model_options = {
            "llama3:latest": "Llama 3 (Best quality)",
            "gemma:2b": "Gemma 2B (Faster)",
            "mistral:latest": "Mistral (Balanced)"
        }
        model_type = st.selectbox(
            "Choose Model",
            list(model_options.keys()),
            format_func=lambda x: model_options[x],
            index=0,
            help="Select an AI model to generate the job requirements"
        )
        
        # Choose output format
        output_format = "json"
        st.info("Output format: JSON")
        
        st.info("Make sure you have Ollama running locally with these models installed.")
        
        # Add some helpful information
        with st.expander("ℹ️ About this app"):
            st.markdown("""
            This app helps recruiters and hiring managers to:
            - Generate structured job requirements
            - Assign importance weights to skills
            - Define penalties for missing qualifications
            - Edit and customize the requirements
            
            The generated requirements can be used for:
            - Creating job descriptions
            - Evaluating candidate resumes
            - Standardizing hiring criteria
            """)

    col1, col2 = st.columns([3, 1])
    with col1:
        job_title = st.text_input(
            "Enter Job Title", 
            placeholder="e.g. Software Engineer, Data Scientist, Project Manager",
            key="job_title_input"
        )
    with col2:
        generate_button = st.button(
            "🚀 Generate Requirements", 
            type="primary", 
            disabled=not job_title,
            help="Click to generate structured requirements for this job title"
        )

    if generate_button:
        with st.spinner(f"Generating requirements for {job_title} using {model_type}..."):
            start_time = time.time()
            requirements, error = generate_job_requirements(job_title, model=model_type)
            end_time = time.time()

            if error:
                st.error(error)
            elif requirements:
                st.success(f"✅ Generated in {end_time - start_time:.2f} seconds using {model_type}")
                
                # Create tabs for view and edit
                view_tab, edit_tab = st.tabs(["👁️ View Requirements", "✏️ Edit Requirements"])
                
                with view_tab:
                    display_job_requirements(requirements)
                
                with edit_tab:
                    updated_requirements = edit_job_requirements(requirements)
                    if updated_requirements:
                        st.session_state.requirements = updated_requirements
                        with view_tab:
                            st.experimental_rerun()
            else:
                st.error("❌ No requirements were generated")

    # Add download button for JSON if requirements exist
    if 'requirements' in st.session_state:
        st.download_button(
            label="📥 Download JSON",
            data=json.dumps(st.session_state.requirements, indent=2),
            file_name=f"{st.session_state.requirements.get('job_type', 'job_requirements')}.json",
            mime="application/json"
        )


if __name__ == "__main__":
    main()
