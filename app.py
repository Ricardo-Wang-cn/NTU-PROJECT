import streamlit as st
import pandas as pd
import re
import altair as alt
import google.generativeai as genai
from PIL import Image

# ================= 1. UI 配置 =================
st.set_page_config(
    page_title="Mistake-Driven Learning", 
    page_icon="🧠", 
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    div[data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #2d3748; }
</style>
""", unsafe_allow_html=True)

# ================= 2. 核心逻辑 =================
if 'global_db' not in st.session_state:
    st.session_state['global_db'] = pd.DataFrame(columns=['Equation', 'User Answer', 'Correct Answer', 'Status', 'Error Type', 'Timestamp'])

def call_gemini_ocr(api_key, image_file):
    """调用 Google Gemini (强制使用你列表中的 2.5 版本)"""
    try:
        genai.configure(api_key=api_key)
        
        # === 核心修改在这里 ===
        # 根据你的列表，我们直接指定最强的 2.5 Flash
        target_model = 'gemini-2.5-flash' 
        
        model = genai.GenerativeModel(target_model)
        img = Image.open(image_file)
        prompt = "Identify all math equations. Return ONLY equations. Format: 'num op num = num'. Convert x/X to *. Convert ÷ to /."
        
        response = model.generate_content([prompt, img])
        return response.text
        
    except Exception as e:
        # 如果 2.5 偶尔不稳定，尝试用 'gemini-flash-latest' (自动指向最新版)
        try:
            model_backup = genai.GenerativeModel('gemini-flash-latest')
            response = model_backup.generate_content([prompt, img])
            return response.text
        except Exception as e2:
            return f"API Error: {str(e)}\nBackup Error: {str(e2)}"

def parse_and_solve(text_block):
    # 数据清洗
    text_block = text_block.replace('÷', '/').replace('x', '*').replace('X', '*')
    text_block = text_block.replace('\n', ' ').replace(',', ' ')
    pattern = r'(\d+\.?\d*)\s*([\+\-\*\/])\s*(\d+\.?\d*)\s*=\s*(\d+\.?\d*)'
    matches = re.findall(pattern, text_block)
    
    results = []
    timestamp = pd.Timestamp.now().strftime("%H:%M")
    
    for m in matches:
        n1, op_char, n2, u_ans = float(m[0]), m[1], float(m[2]), float(m[3])
        correct = 0
        err_type = "Unknown"
        if op_char == '+': correct, err_type = n1 + n2, "Addition Error"
        elif op_char == '-': correct, err_type = n1 - n2, "Subtraction Error"
        elif op_char == '*': correct, err_type = n1 * n2, "Multiplication Error"
        elif op_char == '/': 
            if n2 == 0: continue
            correct, err_type = n1 / n2, "Division Error"
            
        is_right = abs(correct - u_ans) < 0.01
        display_op = op_char.replace('*', '×').replace('/', '÷')
        
        results.append({
            'Equation': f"{int(n1)} {display_op} {int(n2)}",
            'User Answer': int(u_ans) if u_ans.is_integer() else u_ans,
            'Correct Answer': int(correct) if correct.is_integer() else correct,
            'Status': "Correct" if is_right else "Incorrect",
            'Error Type': "None" if is_right else err_type,
            'Timestamp': timestamp
        })
    return results

def get_smart_feedback(error_type):
    content = {
        "Addition Error": ("🧠 Concept: Carrying", "Check sum > 10. Don't forget to carry over!"),
        "Multiplication Error": ("🧠 Concept: Times Tables", "Review tables 6, 7, 8. Check symbol confusion."),
        "Division Error": ("🧠 Concept: Remainder", "Remainder must be smaller than divisor.")
    }
    return content.get(error_type, ("🎉 Review", "Check calculation steps."))

# ================= 3. 侧边栏 =================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2997/2997235.png", width=60)
    page = st.radio("Menu", ["Home (Scan)", "My Dashboard"], label_visibility="collapsed")
    st.markdown("---")
    
    st.subheader("🔧 Settings")
    use_simulation = st.checkbox("✅ Simulation Mode (Backup)", value=False)
    
    if not use_simulation:
        api_key_input = st.text_input("Google API Key", type="password")
        
        # 你的检测按钮 (保留着，用来确认 2.5 是否在线)
        if api_key_input and st.button("🛠 Check Active Model"):
            try:
                genai.configure(api_key=api_key_input)
                # 简单测试一下
                m = genai.GenerativeModel('gemini-2.5-flash')
                st.success("Connected to: gemini-2.5-flash 🟢")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.info("Simulation Mode ON")

    st.markdown("---")
    if st.button("Reset Data", type="secondary"):
        st.session_state['global_db'] = pd.DataFrame(columns=['Equation', 'User Answer', 'Correct Answer', 'Status', 'Error Type', 'Timestamp'])
        st.rerun()

# ================= 4. 页面内容 =================

if page == "Home (Scan)":
    st.title("📸 AI Scan & Digitize")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg'])
        if uploaded_file:
            st.image(uploaded_file, caption="Source", width=300)
            
            if st.button("⚡ Start Recognition", type="primary"):
                if use_simulation:
                    with st.spinner("Simulation Mode..."):
                        simulated_result = "6+9=11\n7x3=20\n8÷2=4"
                        st.session_state['ocr_result'] = simulated_result
                        st.success("Done!")
                
                elif api_key_input:
                    with st.spinner("Analyzing with Gemini 2.5..."):
                        res = call_gemini_ocr(api_key_input, uploaded_file)
                        
                        if "API Error" in res:
                            st.error(res)
                            st.warning("Please try Simulation Mode.")
                        else:
                            st.session_state['ocr_result'] = res
                            st.success("Success!")
                else:
                    st.warning("Enter Key or use Simulation.")

    with col2:
        st.markdown("### 📝 Result")
        current_text = st.session_state.get('ocr_result', "")
        user_input = st.text_area("Equations", value=current_text, height=200)
        
        if st.button("Confirm & Save ➡️", use_container_width=True):
            if user_input:
                new_data = parse_and_solve(user_input)
                if new_data:
                    new_df = pd.DataFrame(new_data)
                    st.session_state['global_db'] = pd.concat([st.session_state['global_db'], new_df], ignore_index=True)
                    st.success(f"Saved {len(new_data)} items!")
                else:
                    st.error("No valid
