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
    """调用 Google Gemini 2.5"""
    try:
        genai.configure(api_key=api_key)
        # 直接使用你列表里存在的 2.5 Flash
        model = genai.GenerativeModel('gemini-2.5-flash')
        img = Image.open(image_file)
        prompt = "Identify math equations. Return ONLY equations. Format: num op num = num. Convert x to *. Convert ÷ to /."
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        # 备用方案：自动指向最新版
        try:
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content([prompt, img])
            return response.text
        except Exception as e2:
            return f"API Error: {str(e)}"

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
        if api_key_input:
            st.success("Key Loaded")
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
                    with st.spinner("Gemini 2.5 Processing..."):
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
                    st.error("No valid math found.")

elif page == "My Dashboard":
    st.title("📊 Learning Dashboard")
    df = st.session_state['global_db']
    
    if not df.empty:
        wrong_df = df[df['Status'] == "Incorrect"]
        
        with st.container():
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total", len(df))
            c2.metric("Mistakes", len(wrong_df), delta_color="inverse")
            acc = (len(df)-len(wrong_df))/len(df)*100 if len(df) > 0 else 0
            c3.metric("Accuracy", f"{acc:.0f}%")
            top_issue = wrong_df['Error Type'].mode()[0] if not wrong_df.empty else "None"
            c4.metric("Weak Spot", top_issue, delta="-Priority")
        
        if not wrong_df.empty:
            st.markdown("---")
            chart_data = wrong_df['Error Type'].value_counts().reset_index()
            chart_data.columns = ['Type', 'Count']
            chart = alt.Chart(chart_data).mark_bar(color='#FF6B6B').encode(x='Count', y=alt.Y('Type', sort='-x')).properties(height=150)
            st.altair_chart(chart, use_container_width=True)

        st.markdown("---")
        st.subheader("📝 Mistake Analysis")
        for index, row in (wrong_df if not wrong_df.empty else df).iterrows():
            if row['Status'] == 'Incorrect':
                with st.container():
                    c1, c2, c3 = st.columns([0.5, 2, 2])
                    with c1: st.error("❌")
                    with c2: st.markdown(f"**{row['Equation']}**")
                    with c3: st.caption(f"Correct: {row['Correct Answer']}")
                    
                    title, advice = get_smart_feedback(row['Error Type'])
                    with st.expander("🤖 AI Tutor"):
                        st.info(f"**{title}**\n{advice}")
                st.markdown("<hr style='opacity:0.2'>", unsafe_allow_html=True)
    else:
        st.info("No data yet.")
