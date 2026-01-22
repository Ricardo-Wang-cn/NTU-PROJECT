import streamlit as st
import pandas as pd
import re
import altair as alt
import base64
from openai import OpenAI

# ================= 1. UI 配置 =================
st.set_page_config(
    page_title="Mistake-Driven Learning (Advanced)", 
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

# ================= 2. Qwen3 API 配置 =================

QWEN_API_KEY = "sk-9b1d3f982246432b9ef1f624572c418e"
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

client = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL)

# --- 功能 A: 图像识别 (OCR) ---
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def call_qwen_ocr(uploaded_file):
    try:
        base64_image = encode_image(uploaded_file)
        # 提示词优化：让模型知道可能有多项式
        completion = client.chat.completions.create(
            model="qwen3-omni-flash",
            messages=[
                {
                    "role": "system", 
                    "content": "Identify all math equations. Return ONLY the equations, one per line. Format example: '1 + 2 + 3 = 6'. Convert x/X to *. Convert ÷ to /."
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
        return f"OCR Error: {str(e)}"

# --- 功能 B: 生成错题讲解 (AI Tutor) ---
def get_qwen_explanation(equation_str, user_ans, correct_ans):
    """
    针对错题生成简短讲解。
    """
    try:
        prompt = f"""
        The student answered '{equation_str} = {user_ans}', which is WRONG. 
        The CORRECT answer is {correct_ans}.
        Please explain the calculation steps briefly. If it's a mixed operation, explain the order of operations.
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
        return "Calculation error. Please check your steps."

# ================= 3. 数据处理逻辑 (核心升级) =================

if 'global_db' not in st.session_state:
    st.session_state['global_db'] = pd.DataFrame(columns=['Equation', 'User Answer', 'Correct Answer', 'Status', 'Error Type', 'Timestamp', 'Explanation'])

def parse_and_solve(text_block):
    """
    核心升级：不再使用死板的 regex 提取 "a+b=c"。
    而是按行分割 -> 找等号 -> 提取左边表达式 -> 使用 eval 计算 -> 对比右边答案。
    """
    # 1. 全局清洗符号
    text_block = text_block.replace('÷', '/').replace('x', '*').replace('X', '*')
    text_block = text_block.replace('=', '=') # 确保等号统一
    
    results = []
    timestamp = pd.Timestamp.now().strftime("%H:%M")
    
    # 按行处理
    lines = text_block.split('\n')
    progress_bar = st.progress(0)
    total_lines = len(lines)
    processed_count = 0
    
    for line in lines:
        line = line.strip()
        if not line or '=' not in line:
            processed_count += 1
            continue
            
        # 2. 以等号分割左右两边
        # split maxsplit=1 防止如果有两个等号导致报错
        parts = line.split('=', 1) 
        if len(parts) != 2: 
            processed_count += 1
            continue
            
        lhs_str = parts[0].strip() # 左边：表达式 (如 "1+2+3")
        rhs_str = parts[1].strip() # 右边：用户答案 (如 "6")
        
        # 过滤掉非数学字符，防止 eval 报错
        # 只允许数字、小数点、加减乘除、空格
        if not re.match(r'^[\d\s\+\-\*\/\.]+$', lhs_str):
            processed_count += 1
            continue
            
        try:
            # 3. 智能计算左边真值
            correct_ans = eval(lhs_str) # eval 能自动处理 1+2+3 或 2*3+1
            user_ans = float(rhs_str)
            
            # 判定对错
            is_right = abs(correct_ans - user_ans) < 0.01
            
            # 判定类型 (简单启发式)
            err_type = "Mixed Ops"
            if '+' in lhs_str and '-' not in lhs_str and '*' not in lhs_str: err_type = "Addition"
            elif '-' in lhs_str and '+' not in lhs_str: err_type = "Subtraction"
            elif '*' in lhs_str and '+' not in lhs_str: err_type = "Multiplication"
            elif '/' in lhs_str: err_type = "Division"
            
            # 格式化显示 (把 * 变回 x)
            display_eq = lhs_str.replace('*', '×').replace('/', '÷')
            
            # 生成解释
            explanation = "Correct!"
            if not is_right:
                explanation = get_qwen_explanation(display_eq, user_ans, correct_ans)
            
            # 存入结果
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
            # 如果 eval 失败或者转换失败，跳过这行
            print(f"Skipping line: {line} due to error: {e}")
            pass
        
        processed_count += 1
        if total_lines > 0:
            progress_bar.progress(min(processed_count / total_lines, 1.0))
            
    progress_bar.empty()
    return results

# ================= 4. 侧边栏 =================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2997/2997235.png", width=60)
    page = st.radio("Menu", ["Home (Scan)", "My Dashboard"], label_visibility="collapsed")
    st.markdown("---")
    
    st.success("🟢 Qwen3 Omni: Online")
    
    use_simulation = st.checkbox("Simulation Mode", value=False)
    
    st.markdown("---")
    if st.button("Reset Data", type="secondary"):
        st.session_state['global_db'] = pd.DataFrame(columns=['Equation', 'User Answer', 'Correct Answer', 'Status', 'Error Type', 'Timestamp', 'Explanation'])
        st.rerun()

# ================= 5. 页面内容 =================

if page == "Home (Scan)":
    st.title("📸 AI Scan (Advanced)")
    st.caption("Supports: 1+2+3=6, Mixed Operations")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg'])
        if uploaded_file:
            st.image(uploaded_file, caption="Source", width=300)
            if st.button("⚡ Start Recognition", type="primary"):
                if use_simulation:
                    # 模拟一个复杂算式数据
                    st.session_state['ocr_result'] = "6+9+1=16\n7x3+1=20\n100-10-10=80"
                    st.success("Done (Simulated)")
                else:
                    with st.spinner("Qwen3 is analyzing complex equations..."):
                        res = call_qwen_ocr(uploaded_file)
                        st.session_state['ocr_result'] = res
                        st.success("Analysis Complete!")

    with col2:
        st.markdown("### 📝 Verify & Learn")
        current_text = st.session_state.get('ocr_result', "")
        user_input = st.text_area("Equations", value=current_text, height=200)
        
        if st.button("Confirm & Analyze ➡️", use_container_width=True):
            if user_input:
                with st.spinner("Analyzing logic & generating lessons..."):
                    new_data = parse_and_solve(user_input)
                    if new_data:
                        new_df = pd.DataFrame(new_data)
                        st.session_state['global_db'] = pd.concat([st.session_state['global_db'], new_df], ignore_index=True)
                        st.success(f"Successfully analyzed {len(new_data)} equations!")
                    else:
                        st.error("No valid math found. Format: '1+2=3'")

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
        
        display_df = wrong_df if not wrong_df.empty else df
        
        for index, row in display_df.iterrows():
            if row['Status'] == 'Incorrect':
                with st.container():
                    c1, c2, c3 = st.columns([0.5, 2, 2])
                    with c1: st.error("❌")
                    with c2: st.markdown(f"**{row['Equation']}**")
                    with c3: st.caption(f"Correct: {row['Correct Answer']}")
                    
                    with st.expander(f"🤖 AI Tutor: Analysis for {row['Equation']}"):
                        st.info(f"**AI Explanation:**\n{row['Explanation']}")
                        
                st.markdown("<hr style='opacity:0.2'>", unsafe_allow_html=True)
    else:
        st.info("No data yet.")
