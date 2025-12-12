import streamlit as st
import joblib
import string
import random
from datetime import datetime
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Password Generator",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        padding: 10px;
        border-radius: 5px;
        font-size: 16px;
    }
    .password-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 18px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🔐 Menu")
    page = st.radio("Select Option", 
                    ["🔑 Password Generator", 
                     "📊 Model Loader",
                     "ℹ️ About"])

# Load model function
@st.cache_resource
def load_model():
    try:
        model = joblib.load('model-rt.pkl')
        return model, True
    except FileNotFoundError:
        return None, False

# Password Generator Page
if page == "🔑 Password Generator":
    st.title("🔐 Secure Password Generator")
    st.markdown("Generate strong, random passwords tailored to your needs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚙️ Settings")
        password_length = st.slider(
            "Password Length",
            min_value=8,
            max_value=32,
            value=16,
            help="Choose a length between 8-32 characters"
        )
        
        st.subheader("🔤 Character Types")
        include_uppercase = st.checkbox("Uppercase Letters (A-Z)", value=True)
        include_lowercase = st.checkbox("Lowercase Letters (a-z)", value=True)
        include_numbers = st.checkbox("Numbers (0-9)", value=True)
        include_symbols = st.checkbox("Special Symbols (!@#$%)", value=True)
    
    with col2:
        st.subheader("📋 Presets")
        preset = st.radio(
            "Or choose a preset:",
            ["Custom", "Low Security", "Medium Security", "High Security"],
            help="Quick presets for common use cases"
        )
        
        # Apply presets
        if preset == "Low Security":
            include_uppercase, include_lowercase, include_numbers, include_symbols = True, True, False, False
        elif preset == "Medium Security":
            include_uppercase, include_lowercase, include_numbers, include_symbols = True, True, True, False
        elif preset == "High Security":
            include_uppercase, include_lowercase, include_numbers, include_symbols = True, True, True, True
    
    # Generate password button
    if st.button("🎲 Generate Password", key="gen_btn"):
        # Build character pool
        char_pool = ""
        if include_uppercase:
            char_pool += string.ascii_uppercase
        if include_lowercase:
            char_pool += string.ascii_lowercase
        if include_numbers:
            char_pool += string.digits
        if include_symbols:
            char_pool += string.punctuation
        
        if not char_pool:
            st.error("❌ Please select at least one character type!")
        else:
            # Generate password
            password = ''.join(random.choice(char_pool) for _ in range(password_length))
            
            st.markdown("---")
            st.subheader("✅ Generated Password")
            st.markdown(f'<div class="password-box">{password}</div>', unsafe_allow_html=True)
            
            # Copy button
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"📏 Length: {len(password)} characters")
            with col2:
                if st.button("📋 Copy to Clipboard"):
                    st.success("✅ Copied! (Use Ctrl+V to paste)")
            with col3:
                st.warning(f"⏰ Generated: {datetime.now().strftime('%H:%M:%S')}")

# Model Loader Page
elif page == "📊 Model Loader":
    st.title("📊 Model Loader")
    st.markdown("Load and inspect your machine learning model")
    
    model, success = load_model()
    
    if success:
        st.success("✅ Model loaded successfully!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 Model Details")
            st.info(f"**Model Type:** {type(model).__name__}")
            st.info(f"**File Name:** model-rt.pkl")
        
        with col2:
            st.subheader("ℹ️ Information")
            st.info(f"**Load Status:** ✅ Success")
            st.info(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.error("❌ Could not load model-rt.pkl")
        st.warning("Make sure 'model-rt.pkl' is in the same directory as this script")
        st.code("python -m streamlit run app.py", language="bash")

# About Page
elif page == "ℹ️ About":
    st.title("ℹ️ About This App")
    
    st.markdown("""
    ### 🔐 Password Generator & Model Loader
    
    A user-friendly web application built with **Streamlit** that provides:
    
    #### Features:
    - **🔑 Password Generator**: Create secure, customizable passwords
    - **📊 Model Loader**: Load and inspect ML models using joblib
    - **⚙️ Easy Configuration**: Intuitive sliders and checkboxes
    - **📋 Quick Presets**: Pre-configured security levels
    
    #### How to Use:
    1. Select "Password Generator" from the menu
    2. Adjust settings or choose a preset
    3. Click "Generate Password"
    4. Copy your new password!
    
    #### Requirements:
    - Python 3.7+
    - streamlit
    - joblib
    
    #### Installation:
    ```bash
    pip install streamlit joblib
    ```
    
    #### Run the App:
    ```bash
    streamlit run app.py
    ```
    
    ---
    **Made with ❤️ using Streamlit**
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "🔐 Password Generator v1.0 | Built with Streamlit"
    "</div>",
    unsafe_allow_html=True
)

# Air Quality Prediction Page
st.set_page_config("Air Quality Prediction", layout="centered")
st.title("🌫️ Air Quality Index (AQI) Prediction")
st.markdown("Enter the pollutant concentrations below to predict the air quality index.")

# Define the feature columns
columns = ['PM2.5', 'PM10', 'NO', 'NO2', 'NOx', 'NH3', 'CO', 'SO2', 'O3', 'Benzene', 'Toluene', 'Xylene']
data = []

# Input form for better UX
with st.form("input_form"):
    st.subheader("Pollutant Concentrations (in µg/m³ or ppm):")
    col1, col2 = st.columns(2)
    inputs = {}

    # Create input fields
    for i, column in enumerate(columns):
        with (col1 if i % 2 == 0 else col2):
            value = st.number_input(f"{column}", min_value=0.0, step=0.1, format="%.2f")
            inputs[column] = value

    # Submit button
    submitted = st.form_submit_button("Predict AQI")

if submitted:
    try:
        # Convert inputs to DataFrame
        data = pd.DataFrame([list(inputs.values())], columns=columns)

        # Load model
        model = joblib.load('model-rt.pkl')
        prediction = model.predict(data)[0]  # Get scalar value

        # AQI quality determination
        aqi_quality_labels = ['Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor']
        def get_aqi_quality(aqi):
            if aqi <= 50:
                return aqi_quality_labels[0]
            elif aqi <= 100:
                return aqi_quality_labels[1]
            elif aqi <= 200:
                return aqi_quality_labels[2]
            elif aqi <= 300:
                return aqi_quality_labels[3]
            else:
                return aqi_quality_labels[4]

        air_quality = get_aqi_quality(prediction)

        # Display result
        st.success("Prediction completed successfully!")
        st.markdown(f"<h2 style='text-align: center;'>🌍 Predicted AQI: <span style='color: #ff4b4b;'>{int(prediction)}</span></h2>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>Air Quality Level: <span style='color: #4b8bff;'>{air_quality}</span></h3>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred during prediction: {e}")
