import streamlit as st
import pandas as pd
import re
import altair as alt
import base64
from openai import OpenAI

# ================= 1. UI 配置 =================
st.set_page_config(
    page_title="Mistake-Driven Learning", 
    page_icon="🎓", 
    layout="wide" 
)

st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    
    /* 卡片容器样式 */
    div[data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }
    
    /* 字体优化 */
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #2d3748; }
    
    /* 上传组件优化 */
    div[data-testid="stFileUploader"] {
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ================= 2. API 配置 (内置 Key) =================

QWEN_API_KEY = "sk-9b1d3f982246432b9ef1f624572c418e"
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

client = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL)

# --- 功能 A: 图像识别 (OCR) ---
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def call_ai_ocr(uploaded_file):
    try:
        base64_image = encode_image(uploaded_file)
        completion = client.chat.completions.create(
            model="qwen3-omni-flash",
            messages=[
                {
                    "role": "system", 
                    "content": "Identify all math equations. Return ONLY the equations, one per line. Format example: '3 * (2 + 3) = 15'. Keep parentheses '()' if they exist. Convert x/X to *. Convert ÷ to /."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract math equations from this image:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                }
            ],
            modalities=["text"], stream=False
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- 功能 B: 生成错题讲解 (AI Tutor) ---
def get_ai_explanation(equation_str, user_ans, correct_ans):
    try:
        prompt = f"""
        The student answered '{equation_str} = {user_ans}', which is WRONG. 
        The CORRECT answer is {correct_ans}.
        Please explain the error. If parentheses are involved, explain the priority.
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
        return "Check calculation steps."

# ================= 3. 数据处理逻辑 =================

if 'global_db' not in st.session_state:
    st.session_state['global_db'] = pd.DataFrame(columns=['Equation', 'User Answer', 'Correct Answer', 'Status', 'Error Type', 'Timestamp', 'Explanation'])

def parse_and_solve(text_block):
    text_block = text_block.replace('÷', '/').replace('x', '*').replace('X', '*')
    text_block = text_block.replace('（', '(').replace('）', ')')
    
    results = []
    timestamp = pd.Timestamp.now().strftime("%H:%M")
    
    lines = text_block.split('\n')
    progress_bar = st.progress(0)
    total_lines = len(lines)
    processed_count = 0
    
    for line in lines:
        line = line.strip()
        if not line or '=' not in line:
            processed_count += 1
            continue
            
        parts = line.split('=', 1) 
        if len(parts) != 2: 
            processed_count += 1
            continue
            
        lhs_str = parts[0].strip()
        rhs_str = parts[1].strip()
        
        # 允许数字、运算符号、括号
        if not re.match(r'^[\d\s\+\-\*\/\.\(\)]+$', lhs_str):
            processed_count += 1
            continue
            
        try:
            correct_ans = eval(lhs_str) 
            user_ans = float(rhs_str)
            
            is_right = abs(correct_ans - user_ans) < 0.01
            
            err_type = "Mixed Ops"
            if '(' in lhs_str: err_type = "Parentheses Priority"
            elif '+' in lhs_str and '*' not in lhs_str: err_type = "Addition"
            elif '-' in lhs_str: err_type = "Subtraction"
            elif '*' in lhs_str: err_type = "Multiplication"
            elif '/' in lhs_str: err_type = "Division"
            
            display_eq = lhs_str.replace('*', '×').replace('/', '÷')
            
            explanation = "Correct!"
            if not is_right:
                explanation = get_ai_explanation(display_eq, user_ans, correct_ans)
            
            results.append({
                'Equation': display_eq,
                'User Answer': int(user_ans) if user_ans.is_integer() else user_ans,
                'Correct Answer': int(correct_ans) if correct_ans.is_integer() else correct_ans,
                'Status': "Correct" if is_right else "Incorrect",
                'Error Type': "None" if is_right else err_type,
                'Timestamp': timestamp,
                'Explanation': explanation
            })
            
        except Exception as e:
            pass
        
        processed_count += 1
        if total_lines > 0:
            progress_bar.progress(min(processed_count / total_lines, 1.0))
            
    progress_bar.empty()
    return results

# ================= 4. 侧边栏 (纯净版) =================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2997/2997235.png", width=60)
    
    # 导航菜单
    page = st.radio("Menu", ["Home (Scan)", "My Dashboard"], label_visibility="collapsed")
    
    st.markdown("---")
    
    # 移除了所有 Simulation Mode 和 Qwen 字样
    st.success("🟢 AI System: Online")
    
    st.markdown("---")
    if st.button("Reset All Data", type="secondary"):
        st.session_state['global_db'] = pd.DataFrame(columns=['Equation', 'User Answer', 'Correct Answer', 'Status', 'Error Type', 'Timestamp', 'Explanation'])
        st.rerun()

# ================= 5. 页面内容 =================

if page == "Home (Scan)":
    st.title("📸 AI Scan & Learn")
    st.caption("Upload homework. The AI analyzes mistakes instantly.")
    
    # === 布局：垂直分布 (Vertical Layout) ===
    
    # 1. 上传区域 (Top)
    st.markdown("### 1. Upload Image")
    uploaded_file = st.file_uploader("Choose an image...", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
    
    if uploaded_file:
        # 图片居中显示
        st.image(uploaded_file, caption="Uploaded Homework", width=500)
        
        # 识别按钮
        if st.button("⚡ Start AI Analysis", type="primary", use_container_width=True):
            # 这里的 Spinner 文案已改为通用的 AI
            with st.spinner("AI is analyzing image..."):
                res = call_ai_ocr(uploaded_file)
                st.session_state['ocr_result'] = res
                st.success("Scan Complete!")

    # 分隔线
    st.markdown("---")

    # 2. 结果确认区域 (Bottom)
    st.markdown("### 2. Verify & Process")
    
    current_text = st.session_state.get('ocr_result', "")
    
    # 如果还没有识别结果，给一个占位符提示
    if not current_text and not uploaded_file:
         st.info("👆 Please upload an image above to start.")
    
    # 文本框永远显示（即使为空）
    user_input = st.text_area(
        "Recognized Equations (Editable)", 
        value=current_text, 
        height=150,
        placeholder="Waiting for scan result..."
    )
    
    # 确认按钮
    if st.button("Confirm & Generate Lessons ➡️", use_container_width=True):
        if user_input:
            # 这里的 Spinner 文案也改为通用的 AI
            with st.spinner("AI is generating learning guide..."):
                new_data = parse_and_solve(user_input)
                if new_data:
                    new_df = pd.DataFrame(new_data)
                    st.session_state['global_db'] = pd.concat([st.session_state['global_db'], new_df], ignore_index=True)
                    st.success(f"Success! {len(new_data)} equations processed. Check Dashboard.")
                else:
                    st.error("No valid equations found. Please check the format.")
        else:
            st.warning("Input is empty.")

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
        st.subheader("📝 AI Feedback & Review")
        
        display_df = wrong_df if not wrong_df.empty else df
        
        for index, row in display_df.iterrows():
            if row['Status'] == 'Incorrect':
                with st.container():
                    c1, c2, c3 = st.columns([0.5, 2, 2])
                    with c1: st.error("❌")
                    with c2: st.markdown(f"**{row['Equation']}**")
                    with c3: st.caption(f"Correct: {row['Correct Answer']}")
                    
                    with st.expander(f"🤖 AI Analysis for {row['Equation']}"):
                        st.info(f"**Explanation:**\n{row['Explanation']}")
                        
                st.markdown("<hr style='opacity:0.2'>", unsafe_allow_html=True)
    else:
        st.info("No data available yet.")
