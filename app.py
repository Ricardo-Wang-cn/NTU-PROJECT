import streamlit as st
import pandas as pd
import re
import altair as alt
import base64
from openai import OpenAI

# ================= 1. UI 配置 =================
st.set_page_config(
    page_title="Mistake-Driven Learning (Qwen AI Tutor)", 
    page_icon="🎓", 
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

# ================= 2. Qwen3 API 配置 (内置 Key) =================

QWEN_API_KEY = "sk-9b1d3f982246432b9ef1f624572c418e"
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

client = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL)

# --- 功能 A: 图像识别 (OCR) ---
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def call_qwen_ocr(uploaded_file):
    try:
        base64_image = encode_image(uploaded_file)
        completion = client.chat.completions.create(
            model="qwen3-omni-flash",
            messages=[
                {
                    "role": "system", 
                    "content": "Identify all math equations. Return ONLY equations, one per line. Format: 'num op num = num'. Convert x/X to *. Convert ÷ to /."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract math equations:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                }
            ],
            modalities=["text"], stream=False
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"OCR Error: {str(e)}"

# --- 功能 B: 生成错题讲解 (AI Tutor) ---
def get_qwen_explanation(equation_str, user_ans, correct_ans):
    """
    针对具体的错题，生成简短的英文讲解。
    要求：解释竖式逻辑、进位/退位，<40 words。
    """
    try:
        prompt = f"""
        The student answered '{equation_str} = {user_ans}', which is WRONG. 
        The CORRECT answer is {correct_ans}.
        Please explain WHY based on vertical calculation steps (e.g., carrying, borrowing, alignment).
        Keep it extremely concise (under 40 English words).
        """
        
        completion = client.chat.completions.create(
            model="qwen3-omni-flash",
            messages=[
                {"role": "system", "content": "You are a concise math tutor."},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        return completion.choices[0].message.content
    except:
        return "Check your calculation steps carefully (AI Busy)."

# ================= 3. 数据处理逻辑 (核心修改) =================

if 'global_db' not in st.session_state:
    # 新增 'Explanation' 列，用于存储 AI 生成的文字
    st.session_state['global_db'] = pd.DataFrame(columns=['Equation', 'User Answer', 'Correct Answer', 'Status', 'Error Type', 'Timestamp', 'Explanation'])

def parse_and_solve(text_block):
    text_block = text_block.replace('÷', '/').replace('x', '*').replace('X', '*')
    text_block = text_block.replace('\n', ' ').replace(',', ' ')
    pattern = r'(\d+\.?\d*)\s*([\+\-\*\/])\s*(\d+\.?\d*)\s*=\s*(\d+\.?\d*)'
    matches = re.findall(pattern, text_block)
    
    results = []
    timestamp = pd.Timestamp.now().strftime("%H:%M")
    
    # 创建一个进度条，因为现在要调用 API 生成解释，会稍微慢一点点
    progress_bar = st.progress(0)
    total = len(matches)
    
    for i, m in enumerate(matches):
        n1, op_char, n2, u_ans = float(m[0]), m[1], float(m[2]), float(m[3])
        correct = 0
        err_type = "Unknown"
        
        if op_char == '+': correct, err_type = n1 + n2, "Addition"
        elif op_char == '-': correct, err_type = n1 - n2, "Subtraction"
        elif op_char == '*': correct, err_type = n1 * n2, "Multiplication"
        elif op_char == '/': 
            if n2 != 0: correct, err_type = n1 / n2, "Division"
            
        is_right = abs(correct - u_ans) < 0.01
        display_op = op_char.replace('*', '×').replace('/', '÷')
        equation_disp = f"{int(n1)} {display_op} {int(n2)}"
        
        # === 核心逻辑：如果是错题，立刻调用 AI 生成解释 ===
        explanation_text = "Correct!" # 默认
        if not is_right:
            # 只有错题才调用 Qwen 生成解释
            explanation_text = get_qwen_explanation(equation_disp, int(u_ans), int(correct))
        
        results.append({
            'Equation': equation_disp,
            'User Answer': int(u_ans) if u_ans.is_integer() else u_ans,
            'Correct Answer': int(correct) if correct.is_integer() else correct,
            'Status': "Correct" if is_right else "Incorrect",
            'Error Type': "None" if is_right else err_type,
            'Timestamp': timestamp,
            'Explanation': explanation_text # 存入数据库
        })
        progress_bar.progress((i + 1) / total)
        
    progress_bar.empty()
    return results

# ================= 4. 侧边栏 =================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2997/2997235.png", width=60)
    page = st.radio("Menu", ["Home (Scan)", "My Dashboard"], label_visibility="collapsed")
    st.markdown("---")
    
    st.success("🟢 Qwen3 AI: Active")
    st.caption("Auto-Tutor Enabled")
    
    use_simulation = st.checkbox("Simulation Mode", value=False)
    
    st.markdown("---")
    if st.button("Reset Data", type="secondary"):
        st.session_state['global_db'] = pd.DataFrame(columns=['Equation', 'User Answer', 'Correct Answer', 'Status', 'Error Type', 'Timestamp', 'Explanation'])
        st.rerun()

# ================= 5. 页面内容 =================

if page == "Home (Scan)":
    st.title("📸 AI Scan (Qwen-Powered)")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg'])
        if uploaded_file:
            st.image(uploaded_file, caption="Source", width=300)
            if st.button("⚡ Start Recognition", type="primary"):
                if use_simulation:
                    st.session_state['ocr_result'] = "6+9=11\n7x3=20\n8÷2=4"
                    st.success("Done (Simulated)")
                else:
                    with st.spinner("Qwen3 is reading equations..."):
                        res = call_qwen_ocr(uploaded_file)
                        st.session_state['ocr_result'] = res
                        st.success("Analysis Complete!")

    with col2:
        st.markdown("### 📝 Verify & Learn")
        current_text = st.session_state.get('ocr_result', "")
        user_input = st.text_area("Equations", value=current_text, height=200)
        
        if st.button("Confirm & Generate Lessons ➡️", use_container_width=True):
            if user_input:
                with st.spinner("Qwen3 is generating custom mini-lessons for mistakes..."):
                    new_data = parse_and_solve(user_input)
                    if new_data:
                        new_df = pd.DataFrame(new_data)
                        st.session_state['global_db'] = pd.concat([st.session_state['global_db'], new_df], ignore_index=True)
                        st.success(f"Processed {len(new_data)} items! Explanations generated.")
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
        st.subheader("📝 Mistake Analysis & AI Feedback")
        
        # 显示错题和解释
        display_df = wrong_df if not wrong_df.empty else df
        
        for index, row in display_df.iterrows():
            if row['Status'] == 'Incorrect':
                with st.container():
                    c1, c2, c3 = st.columns([0.5, 2, 2])
                    with c1: st.error("❌")
                    with c2: st.markdown(f"**{row['Equation']}**")
                    with c3: st.caption(f"Correct: {row['Correct Answer']}")
                    
                    # === 这里的解释现在是 Qwen 生成的动态内容 ===
                    with st.expander(f"🤖 AI Tutor: Why is {row['User Answer']} wrong?"):
                        st.info(f"**Analysis:**\n{row['Explanation']}")
                        
                st.markdown("<hr style='opacity:0.2'>", unsafe_allow_html=True)
    else:
        st.info("No data yet. Go upload some homework!")
