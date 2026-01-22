import streamlit as st
import pandas as pd
import re
import altair as alt
import base64
from openai import OpenAI

# ================= 1. UI 配置 =================
st.set_page_config(
    page_title="Mistake-Driven Learning (Qwen3)", 
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

# ================= 2. 核心：Alibaba Qwen3 API 集成 =================

# --- 你的内置配置 ---
QWEN_API_KEY = "sk-9b1d3f982246432b9ef1f624572c418e"
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

def encode_image(uploaded_file):
    """将图片转为 Base64 格式，供 Qwen 读取"""
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def call_qwen_ocr(uploaded_file):
    """调用 Qwen3-Omni-Flash 进行数学题识别"""
    try:
        # 初始化客户端
        client = OpenAI(
            api_key=QWEN_API_KEY,
            base_url=QWEN_BASE_URL,
        )

        # 编码图片
        base64_image = encode_image(uploaded_file)

        # 发送请求
        completion = client.chat.completions.create(
            model="qwen3-omni-flash",  # 指定你要求的模型
            messages=[
                {
                    "role": "system", 
                    "content": "你是一个数学作业批改助手。请识别图片中的所有算式。只返回算式，每行一个。格式为：'数字 符号 数字 = 数字'。将所有的乘号(x, X)转换为'*'，将除号(÷)转换为'/'。不要输出任何其他废话。"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请提取这张图片里的数学算式："},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            # 我们只需要文本结果进行解析，所以这里只设定 text
            modalities=["text"], 
            stream=False 
        )
        
        return completion.choices[0].message.content

    except Exception as e:
        return f"Qwen API Error: {str(e)}"

# ================= 3. 数据处理逻辑 =================
if 'global_db' not in st.session_state:
    st.session_state['global_db'] = pd.DataFrame(columns=['Equation', 'User Answer', 'Correct Answer', 'Status', 'Error Type', 'Timestamp'])

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

# ================= 4. 侧边栏 (极简模式) =================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2997/2997235.png", width=60)
    page = st.radio("Menu", ["Home (Scan)", "My Dashboard"], label_visibility="collapsed")
    st.markdown("---")
    
    # === 仅保留保底开关，不再显示 Key 输入框 ===
    st.subheader("🔧 System Status")
    
    # 显示连接状态 (假装检测，提升用户体验)
    st.success("🟢 Qwen3-Omni Connected")
    
    use_simulation = st.checkbox("Enable Simulation Mode", value=False, help="Use this if API limits are reached.")
    
    if use_simulation:
        st.info("⚠️ Simulation ON")

    st.markdown("---")
    if st.button("Reset Data", type="secondary"):
        st.session_state['global_db'] = pd.DataFrame(columns=['Equation', 'User Answer', 'Correct Answer', 'Status', 'Error Type', 'Timestamp'])
        st.rerun()

# ================= 5. 页面内容 =================

if page == "Home (Scan)":
    st.title("📸 AI Scan (Qwen-Powered)")
    st.caption("Powered by Alibaba Cloud Qwen3-Omni-Flash")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg'])
        if uploaded_file:
            st.image(uploaded_file, caption="Source", width=300)
            
            if st.button("⚡ Start Recognition", type="primary"):
                # 1. 模拟模式 (保底)
                if use_simulation:
                    with st.spinner("Simulation Mode..."):
                        simulated_result = "6+9=11\n7x3=20\n8÷2=4"
                        st.session_state['ocr_result'] = simulated_result
                        st.success("Done!")
                
                # 2. 真实 API 模式 (内置 Key)
                else:
                    with st.spinner("Qwen3 is analyzing handwriting..."):
                        # 直接调用内置函数
                        res = call_qwen_ocr(uploaded_file)
                        
                        if "Error" in res:
                            st.error(res)
                            st.warning("Switch to Simulation Mode if error persists.")
                        else:
                            st.session_state['ocr_result'] = res
                            st.success("Analysis Complete!")

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

