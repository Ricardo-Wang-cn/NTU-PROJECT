import streamlit as st

# ================= 页面配置 (必须放在最前面) =================
st.set_page_config(
    page_title="Mistake-Driven Learning", 
    page_icon="📚", 
    layout="wide" 
)

from supabase import create_client, Client

# 初始化云端连接 (请替换成你在 Supabase 申请的地址)
SUPABASE_URL = "https://tpokdzclxncdtmfxvkuy.supabase.co"
SUPABASE_KEY = "sb_publishable_ihHrH-gkKfN480wulWcikw_x5JBNPFs"
supabase: Client = create_client("https://tpokdzclxncdtmfxvkuy.supabase.co", "sb_publishable_ihHrH-gkKfN480wulWcikw_x5JBNPFs")

import pandas as pd
import altair as alt
import base64
from openai import OpenAI

# --- Session State 初始化 ---
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Home (Scan)"

if 'global_db' not in st.session_state:
    st.session_state['global_db'] = pd.DataFrame(columns=['Equation', 'User Answer', 'Correct Answer', 'Status', 'Error Type', 'Timestamp', 'Explanation'])

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""

if 'ai_chat_history' not in st.session_state:
    st.session_state['ai_chat_history'] = []

if 'ai_chat_open' not in st.session_state:
    st.session_state['ai_chat_open'] = False

if 'theme' not in st.session_state:
    st.session_state['theme'] = 'dark'

# 简单的登录/注册逻辑
def show_login_ui():
    st.title("Login to Mistake-Driven Learning")
    col1, col2 = st.tabs(["Login", "Register"])
    with col1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            # 在云端查找用户
            res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
            if len(res.data) > 0:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = u
                st.rerun()
            else: st.error("Invalid credentials")
    with col2:
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password", type="password")
        if st.button("Register"):
            supabase.table("users").insert({"username": new_u, "password": new_p}).execute()
            st.success("Registered! Now login.")

# 如果未登录，直接停止后续代码运行
if not st.session_state['logged_in']:
    show_login_ui()
    st.stop() # 关键：不运行后面的代码

# ================= 1. UI 样式配置 =================
st.markdown("""
<style>
    /* 科技感深色背景 - 深蓝灰渐变 */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 25%, #1e2749 50%, #0f1419 75%, #0a0e27 100%);
        background-size: 400% 400%;
        animation: gradientShift 20s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* 顶部Header区域 - 深色风格 */
    header[data-testid="stHeader"] {
        background: rgba(10, 15, 30, 0.95) !important;
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(64, 224, 208, 0.15);
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    }
    
    /* 顶部装饰条 */
    .stApp > header {
        background: rgba(10, 15, 30, 0.95) !important;
    }
    
    /* 菜单按钮区域 */
    #MainMenu {
        visibility: hidden;
    }
    
    /* 设置按钮区域 */
    .stDeployButton {
        display: none;
    }
    
    /* 顶部工具栏 */
    div[data-testid="stToolbar"] {
        background: rgba(10, 15, 30, 0.95) !important;
    }
    
    /* 移除顶部默认装饰 */
    .stApp > div:first-child {
        background: transparent !important;
    }
    
    /* 顶部所有白色背景元素 */
    header, .stApp header, [data-testid="stHeader"] {
        background: rgba(10, 15, 30, 0.95) !important;
        backdrop-filter: blur(20px);
    }
    
    /* 顶部按钮和链接 */
    header button, header a {
        color: #40e0d0 !important;
    }
    
    header button:hover, header a:hover {
        color: #00d4ff !important;
    }
    
    /* 移除顶部所有可能的白色背景 */
    .stApp header,
    .stApp > div:first-child,
    .stApp > div:first-child > div,
    header[data-testid="stHeader"],
    header[data-testid="stHeader"] > div {
        background: rgba(10, 15, 30, 0.95) !important;
        backdrop-filter: blur(20px);
    }
    
    /* 修复顶部间距 */
    .stApp > div:first-child > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* 主内容区域 - 深色玻璃态 */
    .main .block-container {
        background: rgba(20, 25, 40, 0.85);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(64, 224, 208, 0.1);
        margin-top: 1rem;
        border: 1px solid rgba(64, 224, 208, 0.1);
    }
    
    /* 移除所有白色背景 */
    .main {
        background: transparent !important;
    }
    
    /* 页面容器 */
    .stApp > div:first-child > div:first-child {
        background: transparent !important;
    }
    
    /* 确保没有白色边距 */
    .stApp > div {
        background: transparent !important;
    }
    
    /* 移除顶部间距的白色 */
    .stApp > header + div {
        background: transparent !important;
    }
    
    /* 卡片容器样式 - 深色科技感 */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(30, 40, 60, 0.9) 0%, rgba(20, 30, 50, 0.8) 100%);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(64, 224, 208, 0.2);
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(64, 224, 208, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border-color: rgba(64, 224, 208, 0.4);
    }
    
    /* 侧边栏样式 - 与主页面统一 */
    section[data-testid="stSidebar"] {
        background: rgba(20, 25, 40, 0.85) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(64, 224, 208, 0.15);
        box-shadow: 2px 0 20px rgba(0, 0, 0, 0.5);
    }
    
    /* 侧边栏内容区域 */
    section[data-testid="stSidebar"] > div {
        background: transparent !important;
    }
    
    /* 侧边栏内所有文本颜色 - 确保可见 */
    section[data-testid="stSidebar"] * {
        color: #e0e7ff !important;
    }
    
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label {
        color: #e0e7ff !important;
    }
    
    /* 侧边栏标题 */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #e0e7ff !important;
    }
    
    /* 侧边栏成功/信息提示框文字 */
    section[data-testid="stSidebar"] .stSuccess,
    section[data-testid="stSidebar"] .stInfo,
    section[data-testid="stSidebar"] .stWarning {
        color: #e0e7ff !important;
    }
    
    section[data-testid="stSidebar"] .stSuccess *,
    section[data-testid="stSidebar"] .stInfo *,
    section[data-testid="stSidebar"] .stWarning * {
        color: #e0e7ff !important;
    }
    
    /* 侧边栏分隔线 */
    section[data-testid="stSidebar"] hr {
        border-color: rgba(64, 224, 208, 0.3) !important;
        background-color: rgba(64, 224, 208, 0.3) !important;
    }
    
    /* 侧边栏图片 - 无边框，仅提亮 */
    section[data-testid="stSidebar"] img {
        opacity: 1 !important;
        filter: brightness(1.3);
        background: transparent !important;
        padding: 0 !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* 侧边栏图片容器 - 无边框 */
    section[data-testid="stSidebar"] .stImage {
        background: transparent !important;
        padding: 0 !important;
        border: none !important;
        box-shadow: none !important;
        margin-bottom: 20px !important;
    }
    
    /* 侧边栏所有容器 */
    section[data-testid="stSidebar"] .element-container,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #e0e7ff !important;
    }
    
    /* 字体优化 - 浅色文字 */
    h1, h2, h3 {
        font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
        color: #e0e7ff;
        font-weight: 700;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
    }
    
    /* 普通文本颜色 */
    .stMarkdown, p, div, span, label {
        color: #cbd5e1 !important;
    }
    
    /* 确保所有markdown内容都有足够的对比度 */
    .stMarkdown *,
    .stMarkdown strong,
    .stMarkdown b,
    .stMarkdown p,
    .stMarkdown div,
    .stMarkdown span {
        color: #cbd5e1 !important;
    }
    
    /* 容器内的文本 */
    .main .block-container .stMarkdown,
    .main .block-container .stMarkdown *,
    .main .block-container p,
    .main .block-container span,
    .main .block-container div:not(.stButton):not(.stMetric) {
        color: #cbd5e1 !important;
    }
    
    /* 按钮动态效果 - 科技感青色 */
    .stButton > button {
        background: linear-gradient(135deg, #40e0d0 0%, #00d4ff 100%);
        color: #0a0e27;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(64, 224, 208, 0.4), 0 0 20px rgba(64, 224, 208, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 8px 25px rgba(64, 224, 208, 0.6), 0 0 30px rgba(64, 224, 208, 0.3);
        background: linear-gradient(135deg, #00d4ff 0%, #40e0d0 100%);
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:active {
        transform: translateY(0) scale(0.98);
        box-shadow: 0 2px 10px rgba(64, 224, 208, 0.4);
    }
    
    /* Primary 按钮特殊效果 - 科技感渐变 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00d4ff 0%, #40e0d0 50%, #00b8d4 100%);
        background-size: 200% 200%;
        animation: gradientMove 3s ease infinite;
        color: #0a0e27;
        box-shadow: 0 4px 20px rgba(64, 224, 208, 0.5), 0 0 25px rgba(64, 224, 208, 0.3);
    }
    
    @keyframes gradientMove {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .stButton > button[kind="primary"]:hover {
        animation: none;
        background-position: 100% 50%;
    }
    
    /* Secondary 按钮样式 - 深色边框 */
    .stButton > button[kind="secondary"] {
        background: rgba(30, 40, 60, 0.8);
        color: #40e0d0;
        border: 2px solid rgba(64, 224, 208, 0.5);
        backdrop-filter: blur(10px);
        font-weight: 600;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: rgba(64, 224, 208, 0.25);
        color: #40e0d0;
        border-color: rgba(64, 224, 208, 0.7);
        box-shadow: 0 0 15px rgba(64, 224, 208, 0.3);
    }
    
    /* 侧边栏 Secondary 按钮 - 深色模式增强可见性 */
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background: rgba(40, 50, 70, 0.9) !important;
        color: #40e0d0 !important;
        border: 2px solid rgba(64, 224, 208, 0.6) !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background: rgba(64, 224, 208, 0.3) !important;
        color: #40e0d0 !important;
        border-color: rgba(64, 224, 208, 0.8) !important;
        box-shadow: 0 4px 15px rgba(64, 224, 208, 0.4);
    }
    
    /* 上传组件优化 - 深色风格 */
    div[data-testid="stFileUploader"] {
        margin-bottom: 20px;
        background: rgba(20, 30, 50, 0.6);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 1rem;
        border: 2px dashed rgba(64, 224, 208, 0.3);
        transition: all 0.3s ease;
    }
    
    div[data-testid="stFileUploader"]:hover {
        border-color: rgba(64, 224, 208, 0.6);
        background: rgba(30, 40, 60, 0.7);
        box-shadow: 0 0 15px rgba(64, 224, 208, 0.2);
    }
    
    /* 上传组件内的提示文字 - 黑色字体 */
    div[data-testid="stFileUploader"] p,
    div[data-testid="stFileUploader"] span,
    div[data-testid="stFileUploader"] div,
    div[data-testid="stFileUploader"] label,
    div[data-testid="stFileUploader"] * {
        color: #000000 !important;
        font-weight: 600 !important;
    }
    
    /* 上传组件的图标 - 黑色 */
    div[data-testid="stFileUploader"] svg {
        color: #000000 !important;
        fill: #000000 !important;
        stroke: #000000 !important;
        opacity: 1 !important;
    }
    
    /* 确保所有文字都是黑色 */
    div[data-testid="stFileUploader"] *:not(svg) {
        color: #000000 !important;
    }
    
    /* 文本区域样式 - 深色 */
    .stTextArea > div > div > textarea {
        background: rgba(20, 30, 50, 0.8);
        backdrop-filter: blur(10px);
        border: 2px solid rgba(64, 224, 208, 0.2);
        border-radius: 12px;
        color: #e0e7ff !important;
        transition: all 0.3s ease;
    }
    
    /* 文本区域占位符文字 - 提高对比度 */
    .stTextArea > div > div > textarea::placeholder {
        color: #cbd5e1 !important;
        opacity: 0.9 !important;
        font-weight: 500 !important;
    }
    
    .stTextArea > div > div > textarea::-webkit-input-placeholder {
        color: #cbd5e1 !important;
        opacity: 0.9 !important;
        font-weight: 500 !important;
    }
    
    .stTextArea > div > div > textarea::-moz-placeholder {
        color: #cbd5e1 !important;
        opacity: 0.9 !important;
        font-weight: 500 !important;
    }
    
    .stTextArea > div > div > textarea:-ms-input-placeholder {
        color: #cbd5e1 !important;
        opacity: 0.9 !important;
        font-weight: 500 !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: rgba(64, 224, 208, 0.6);
        box-shadow: 0 0 0 3px rgba(64, 224, 208, 0.1), 0 0 15px rgba(64, 224, 208, 0.2);
        background: rgba(25, 35, 55, 0.9);
    }
    
    /* 文本区域标签文字 */
    .stTextArea > label {
        color: #e0e7ff !important;
        font-weight: 600 !important;
    }
    
    /* Radio 按钮样式 - 深色 */
    .stRadio > div {
        background: rgba(20, 30, 50, 0.6);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 0.5rem;
        border: 1px solid rgba(64, 224, 208, 0.1);
    }
    
    /* 成功/错误/信息提示框样式 - 深色 */
    .stSuccess, .stError, .stInfo, .stWarning {
        border-radius: 12px;
        padding: 1rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(64, 224, 208, 0.1);
    }
    
    /* 图表容器 - 深色 */
    .stAltairChart {
        background: rgba(20, 30, 50, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid rgba(64, 224, 208, 0.1);
    }
    
    /* Expander 样式 - 深色 */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(64, 224, 208, 0.1) 0%, rgba(0, 212, 255, 0.1) 100%);
        border-radius: 8px;
        transition: all 0.3s ease;
        border: 1px solid rgba(64, 224, 208, 0.1);
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, rgba(64, 224, 208, 0.2) 0%, rgba(0, 212, 255, 0.2) 100%);
        border-color: rgba(64, 224, 208, 0.3);
    }
    
    /* 滚动条美化 - 科技感 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(10, 15, 30, 0.5);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #40e0d0 0%, #00d4ff 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #00d4ff 0%, #40e0d0 100%);
        box-shadow: 0 0 10px rgba(64, 224, 208, 0.5);
    }
    
    /* 图片容器 */
    .stImage > img {
        border-radius: 12px;
        border: 1px solid rgba(64, 224, 208, 0.2);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    /* 移除所有默认白色背景 */
    div[data-baseweb="base"] {
        background: transparent !important;
    }
    
    /* 确保body也是深色 */
    body {
        background: transparent !important;
    }
    
    /* 移除Streamlit默认的白色装饰 */
    .stApp > div:first-child {
        background: transparent !important;
    }
    
    /* 顶部状态栏 */
    .stStatusWidget {
        background: rgba(10, 15, 30, 0.8) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(64, 224, 208, 0.2);
    }
    
    /* 确保所有div背景透明或深色 */
    div:not([class*="metric"]):not([class*="block-container"]):not([data-testid]) {
        background: transparent !important;
    }
    
    /* 修复可能的白色边框 */
    * {
        border-color: rgba(64, 224, 208, 0.1) !important;
    }
    
    /* 交互体验提升 - 拖拽上传提示动画 */
    div[data-testid="stFileUploader"] {
        position: relative;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stFileUploader"]:hover {
        transform: scale(1.02);
    }
    
    /* 文件上传区域的拖拽提示 */
    div[data-testid="stFileUploader"]::after {
        content: 'Drag & Drop Files Here';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: rgba(64, 224, 208, 0.7);
        font-size: 0.85rem;
        font-weight: 600;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
        z-index: 1;
        background: rgba(20, 30, 50, 0.8);
        padding: 8px 16px;
        border-radius: 8px;
        border: 2px dashed rgba(64, 224, 208, 0.5);
    }
    
    div[data-testid="stFileUploader"]:hover::after {
        opacity: 1;
    }
    
    /* 成功/错误消息动画 */
    .stSuccess, .stError, .stInfo, .stWarning {
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* 按钮点击波纹效果 */
    .stButton > button {
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .stButton > button:active::after {
        width: 300px;
        height: 300px;
    }
    
    /* 加载动画增强 */
    .stSpinner > div {
        border-color: #40e0d0 !important;
    }
    
    /* 卡片悬停增强 */
    div[data-testid="metric-container"] {
        cursor: pointer;
    }
    
    /* 确保所有文本元素在深色主题下都有足够的对比度 */
    .main .block-container *:not(button):not(input):not(textarea):not(select):not(svg):not(path) {
        color: #cbd5e1 !important;
    }
    
    /* 特别处理strong和b标签 */
    strong, b {
        color: #e0e7ff !important;
        font-weight: 700 !important;
    }
    
    /* 确保列容器内的文本可见 */
    [data-testid="column"] .stMarkdown,
    [data-testid="column"] .stMarkdown *,
    [data-testid="column"] p,
    [data-testid="column"] span,
    [data-testid="column"] strong,
    [data-testid="column"] b {
        color: #cbd5e1 !important;
    }
    
    [data-testid="column"] strong,
    [data-testid="column"] b {
        color: #e0e7ff !important;
    }
</style>
""", unsafe_allow_html=True)

# 根据主题应用样式
def apply_theme(theme):
    if theme == 'light':
        st.markdown("""
        <style>
        /* 浅色主题样式 */
        .stApp {
            background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 25%, #cbd5e1 50%, #f1f5f9 75%, #ffffff 100%);
            background-size: 400% 400%;
            animation: gradientShift 20s ease infinite;
        }
        
        .main .block-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(100, 116, 139, 0.35);
            margin-top: 1rem;
            border: 1px solid rgba(100, 116, 139, 0.35);
        }
        
        /* 顶栏 - 与主页面统一，确保覆盖所有顶栏元素 */
        header[data-testid="stHeader"],
        .stApp > header,
        header,
        .stApp header,
        [data-testid="stHeader"],
        div[data-testid="stToolbar"],
        .stApp header,
        .stApp > div:first-child,
        .stApp > div:first-child > div,
        header[data-testid="stHeader"] > div,
        header > div,
        header * {
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(20px) !important;
        }
        
        header[data-testid="stHeader"],
        .stApp > header,
        header {
            border-bottom: 1px solid rgba(100, 116, 139, 0.35) !important;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05) !important;
        }
        
        /* 顶栏所有文字和按钮 */
        header button, 
        header a,
        header span,
        header div,
        header p,
        header * {
            color: #3b82f6 !important;
        }
        
        header button:hover, 
        header a:hover {
            color: #2563eb !important;
        }
        
        /* 侧边栏 - 与主页面统一 */
        section[data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(20px);
            border-right: 1px solid rgba(100, 116, 139, 0.35) !important;
        }
        
        section[data-testid="stSidebar"] > div {
            background: transparent !important;
        }
        
        /* 侧边栏所有文字颜色 - 深色 */
        section[data-testid="stSidebar"] *,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] .element-container {
            color: #334155 !important;
        }
        
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] h5,
        section[data-testid="stSidebar"] h6 {
            color: #1e293b !important;
        }
        
        section[data-testid="stSidebar"] .stSuccess,
        section[data-testid="stSidebar"] .stInfo,
        section[data-testid="stSidebar"] .stWarning,
        section[data-testid="stSidebar"] .stSuccess *,
        section[data-testid="stSidebar"] .stInfo *,
        section[data-testid="stSidebar"] .stWarning * {
            color: #334155 !important;
        }
        
        /* 侧边栏按钮文字 */
        section[data-testid="stSidebar"] .stButton > button {
            color: #3b82f6 !important;
        }
        
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            color: white !important;
        }
        
        section[data-testid="stSidebar"] hr {
            border-color: rgba(100, 116, 139, 0.4) !important;
            background-color: rgba(100, 116, 139, 0.4) !important;
        }
        
        /* 侧边栏图片在浅色模式下 */
        section[data-testid="stSidebar"] img {
            filter: brightness(1);
        }
        
        section[data-testid="stSidebar"] .stImage {
            background: transparent !important;
        }
        
        /* 所有标题文字 - 深色 */
        h1, h2, h3, h4, h5, h6 {
            color: #1e293b !important;
        }
        
        /* 所有正文文字 - 深色 */
        .stMarkdown, 
        p, 
        div, 
        span, 
        label,
        .stCaption,
        .stText,
        .stCode,
        .stMarkdownContainer,
        .element-container,
        .stAlert,
        .stSuccess,
        .stError,
        .stInfo,
        .stWarning {
            color: #334155 !important;
        }
        
        /* 确保所有markdown内容在浅色主题下都有足够的对比度 */
        .stMarkdown *,
        .stMarkdown strong,
        .stMarkdown b,
        .stMarkdown p,
        .stMarkdown div,
        .stMarkdown span {
            color: #1e293b !important;
        }
        
        /* 容器内的文本 - 浅色主题下使用深色 */
        .main .block-container .stMarkdown,
        .main .block-container .stMarkdown *,
        .main .block-container p,
        .main .block-container span,
        .main .block-container div:not(.stButton):not(.stMetric) {
            color: #1e293b !important;
        }
        
        /* 确保所有文本元素都是深色 */
        body,
        .main,
        .main *:not(button):not(input):not(textarea):not(select) {
            color: #334155 !important;
        }
        
        /* 输入框文字 */
        input,
        textarea,
        select {
            color: #1e293b !important;
        }
        
        /* 占位符文字 */
        ::placeholder,
        ::-webkit-input-placeholder,
        ::-moz-placeholder,
        :-ms-input-placeholder {
            color: #64748b !important;
            opacity: 0.8 !important;
        }
        
        /* 链接颜色 */
        a {
            color: #3b82f6 !important;
        }
        
        a:hover {
            color: #2563eb !important;
        }
        
        /* 表格文字 */
        table,
        th,
        td {
            color: #334155 !important;
        }
        
        /* 图表文字 */
        .stAltairChart,
        .stAltairChart * {
            color: #334155 !important;
        }
        
        div[data-testid="metric-container"] {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 252, 0.8) 100%);
            border: 1px solid rgba(100, 116, 139, 0.4);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(100, 116, 139, 0.1);
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
        }
        
        .stButton > button[kind="secondary"] {
            background: rgba(241, 245, 249, 0.95);
            color: #2563eb;
            border: 2px solid #3b82f6;
            font-weight: 600;
        }
        
        .stButton > button[kind="secondary"]:hover {
            background: rgba(59, 130, 246, 0.15);
            color: #1d4ed8;
            border-color: #2563eb;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }
        
        /* 侧边栏按钮在浅色模式下 - 增强可见性 */
        section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
            background: rgba(255, 255, 255, 0.95) !important;
            color: #2563eb !important;
            border: 2px solid #3b82f6 !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
            background: rgba(59, 130, 246, 0.15) !important;
            color: #1d4ed8 !important;
            border-color: #2563eb !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }
        
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
        }
        
        .stTextArea > div > div > textarea {
            background: rgba(255, 255, 255, 0.9);
            border: 2px solid rgba(100, 116, 139, 0.4);
            color: #1e293b;
        }
        
        .stTextArea > div > div > textarea:focus {
            border: 2px solid rgba(59, 130, 246, 0.6);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        div[data-testid="stFileUploader"] {
            background: rgba(255, 255, 255, 0.8);
            border: 2px dashed rgba(59, 130, 246, 0.5);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        }
        
        div[data-testid="stFileUploader"]:hover {
            border-color: rgba(59, 130, 246, 0.7);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        }
        
        div[data-testid="stFileUploader"] * {
            color: #1e293b !important;
        }
        
        /* 确保顶栏完全覆盖 - 增加优先级 */
        .stApp header[data-testid="stHeader"],
        .stApp > header[data-testid="stHeader"],
        body > header[data-testid="stHeader"],
        html body header[data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(20px) !important;
            border-bottom: 1px solid rgba(100, 116, 139, 0.35) !important;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05) !important;
        }
        
        /* 顶栏内部所有元素 */
        header[data-testid="stHeader"] *,
        header[data-testid="stHeader"] > *,
        header[data-testid="stHeader"] > div > * {
            background: transparent !important;
            color: #3b82f6 !important;
        }
        
        /* 确保工具栏也是浅色 */
        div[data-testid="stToolbar"],
        div[data-testid="stToolbar"] * {
            background: rgba(255, 255, 255, 0.95) !important;
            color: #3b82f6 !important;
        }
        
        /* 确保所有文本元素在浅色主题下都有足够的对比度 */
        .main .block-container *:not(button):not(input):not(textarea):not(select):not(svg):not(path) {
            color: #1e293b !important;
        }
        
        /* 特别处理strong和b标签 - 浅色主题 */
        strong, b {
            color: #0f172a !important;
            font-weight: 700 !important;
        }
        
        /* 确保列容器内的文本可见 - 浅色主题 */
        [data-testid="column"] .stMarkdown,
        [data-testid="column"] .stMarkdown *,
        [data-testid="column"] p,
        [data-testid="column"] span,
        [data-testid="column"] strong,
        [data-testid="column"] b {
            color: #1e293b !important;
        }
        
        [data-testid="column"] strong,
        [data-testid="column"] b {
            color: #0f172a !important;
        }
        
        /* 增强所有边框对比度 - 浅色主题 */
        * {
            border-color: rgba(100, 116, 139, 0.3) !important;
        }
        
        /* Radio 按钮边框增强 */
        .stRadio > div {
            border: 1px solid rgba(100, 116, 139, 0.4) !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        }
        
        /* Expander 边框增强 */
        .streamlit-expanderHeader {
            border: 1px solid rgba(100, 116, 139, 0.4) !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        }
        
        .streamlit-expanderHeader:hover {
            border-color: rgba(100, 116, 139, 0.5) !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
        }
        
        /* Expander 内容区域边框 */
        .streamlit-expanderContent {
            border: 1px solid rgba(100, 116, 139, 0.3) !important;
            border-top: none !important;
        }
        
        /* 图表容器边框增强 */
        .stAltairChart {
            border: 1px solid rgba(100, 116, 139, 0.4) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }
        
        /* 成功/错误/信息提示框边框增强 */
        .stSuccess, .stError, .stInfo, .stWarning {
            border: 1px solid rgba(100, 116, 139, 0.4) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }
        
        /* 输入框边框增强 */
        input[type="text"],
        input[type="password"],
        input[type="number"],
        select {
            border: 1px solid rgba(100, 116, 139, 0.4) !important;
        }
        
        input[type="text"]:focus,
        input[type="password"]:focus,
        input[type="number"]:focus,
        select:focus {
            border: 1px solid rgba(59, 130, 246, 0.6) !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        /* 图片容器边框增强 */
        .stImage > img {
            border: 1px solid rgba(100, 116, 139, 0.4) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        /* 表格边框增强 */
        table {
            border: 1px solid rgba(100, 116, 139, 0.4) !important;
        }
        
        th, td {
            border: 1px solid rgba(100, 116, 139, 0.3) !important;
        }
        
        /* 分隔线增强 */
        hr {
            border-color: rgba(100, 116, 139, 0.4) !important;
            background-color: rgba(100, 116, 139, 0.4) !important;
            height: 1px !important;
        }
        </style>
        """, unsafe_allow_html=True)

# 应用当前主题
if st.session_state['theme'] == 'light':
    apply_theme('light')

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
                    "content": """你是一个高精度的数学 OCR。请提取图片中的所有数学等式。
                    
                    【严格执行指令】：
                    1. 禁止使用 LaTeX 格式（禁止出现 $ 符号，禁止出现 \sqrt, \div, \frac 等代码）。
                    2. 必须使用普通的数学符号：
                       - 根号用 √
                       - 除号用 ÷
                       - 乘号用 ×
                       - 平方用 ^2
                    3. 原样输出等式，每行一个。
                    
                    例子：
                    图片：√9 ÷ 3 = 2
                    正确输出：√9 ÷ 3 = 2
                    错误输出：$\sqrt{9} \div 3 = 2$
                    """
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all math equations from this image using plain text symbols:"},
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
        学生在做这道题：'{equation_str}' 时填写的答案是 '{user_ans}'，这是错误的。
        这道题的正确答案应该是 '{correct_ans}'。

        请执行以下任务：
        1. 简要说明错误原因（不超过 30 个字）。
        2. 根据该题涉及的数学概念，出一道类似的“挑战题”。
        3. 提供这道挑战题的正确答案。

        请严格按照以下格式输出：
        错误分析：[这里写你的解释]

        ---
        **🚀 举一反三：类似挑战**
        题目：[这里写新题目]
        答案：[这里写新题目的正确答案]
        """
        
        completion = client.chat.completions.create(
            model="qwen3-omni-flash",
            messages=[
                {"role": "system", "content": "你是一个专业的数学导师。你的回答需要简洁、精准（100字以内）。"},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        return completion.choices[0].message.content
    except:
        return "检查计算步骤。尝试再练习一道同类型的题吧！"

# --- 功能 C: AI 在线问答 ---
def get_ai_chat_response(user_message, chat_history):
    """AI在线问答功能"""
    try:
        # 构建对话历史
        messages = [
            {"role": "system", "content": """你是一个友好的数学学习助手。你可以：
            1. 回答数学相关问题
            2. 解释数学概念
            3. 帮助解决数学难题
            4. 提供学习建议
            请用简洁、易懂的语言回答，支持中英文。"""}
        ]
        
        # 添加历史对话（最多保留最近5轮）
        for msg in chat_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # 添加当前问题
        messages.append({"role": "user", "content": user_message})
        
        completion = client.chat.completions.create(
            model="qwen3-omni-flash",
            messages=messages,
            stream=False
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"抱歉，AI暂时无法回答。错误：{str(e)}"

# ================= 3. 数据处理逻辑 =================

def get_correct_answer_from_ai(problem_str):
    """专门调用 AI 获取复杂数学题的标准答案"""
    try:
        response = client.chat.completions.create(
            model="qwen3-omni-flash",
            messages=[
                {"role": "system", "content": "你是一个数学计算器。只返回算式的最终结果（数字或最简表达式），不要任何文字解释。"},
                {"role": "user", "content": f"算出这个算式的结果: {problem_str}"}
            ],
            stream=False
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Error"

def parse_and_solve(text_block):
    results = []
    timestamp = pd.Timestamp.now().strftime("%H:%M")
    
    # 将文本按行拆分
    lines = text_block.split('\n')
    
    # 过滤掉空行
    valid_lines = [l.strip() for l in lines if l.strip()]
    if not valid_lines:
        return []

    # 进度提示
    progress_bar = st.progress(0)
    total = len(valid_lines)
    
    for i, line in enumerate(valid_lines):
        # 1. 拆分等号：例如将 "√9 ÷ 3 = 2" 拆分为 "√9 ÷ 3" 和 "2"
        if '=' in line:
            parts = line.split('=', 1)
            problem_side = parts[0].strip()   # 题目：√9 ÷ 3
            student_ans = parts[1].strip()    # 学生的答案：2
        else:
            problem_side = line
            student_ans = "None"

        # 2. 调用后台 AI 算出这道题真正的答案
        correct_ans = get_correct_answer_from_ai(problem_side)
        
        # 3. 结果判定 (去掉空格后进行字符串比对)
        is_right = (student_ans.replace(" ", "") == correct_ans.replace(" ", ""))
        
        # 4. 自动识别错误类型 (为了 Dashboard 的图表)
        err_type = "Arithmetic"
        if '√' in problem_side or 'sqrt' in problem_side: 
            err_type = "Roots"
        elif '∫' in problem_side or 'int' in problem_side: 
            err_type = "Calculus"
        elif '^' in problem_side:
            err_type = "Exponents"

        # 5. 生成结果字典
        results.append({
            'Equation': problem_side,
            'User Answer': student_ans,
            'Correct Answer': correct_ans,
            'Status': "Correct" if is_right else "Incorrect",
            'Error Type': "None" if is_right else err_type,
            'Timestamp': timestamp,
            'Explanation': "Perfect!" if is_right else get_ai_explanation(problem_side, student_ans, correct_ans)
        })
        
        # 更新进度条
        progress_bar.progress((i + 1) / total)
    
    # 完成后清除进度条
    progress_bar.empty()
    return results
    
# ================= 4. 侧边栏 (导航与系统控制) =================
with st.sidebar:
    # --- 1. 顶部图标 ---
    st.image("https://cdn-icons-png.flaticon.com/512/2997/2997235.png", width=60)
    
    # 显示当前登录的用户
    st.markdown(f"**User:** {st.session_state.get('user_name', 'Guest')}")
    st.markdown("---")

    # --- 3. 导航菜单 (Home / Dashboard / Forum) ---
    # 首页扫描
    if st.button("Home (Scan)", 
                 type="primary" if st.session_state['current_page'] == "Home (Scan)" else "secondary", 
                 use_container_width=True):
        st.session_state['current_page'] = "Home (Scan)"
        st.rerun()
    
    # 学习看板
    if st.button("My Dashboard", 
                 type="primary" if st.session_state['current_page'] == "My Dashboard" else "secondary", 
                 use_container_width=True):
        st.session_state['current_page'] = "My Dashboard"
        st.rerun()
    
    # 全局论坛 (联网功能)
    if st.button("Global Forum", 
                 type="primary" if st.session_state['current_page'] == "Global Forum" else "secondary", 
                 use_container_width=True):
        st.session_state['current_page'] = "Global Forum"
        st.rerun()
    
    st.markdown("---")
    
    # --- 4. 系统设置 (主题/状态) ---
    
    # 主题切换
    theme_text = "Light Mode" if st.session_state['theme'] == 'dark' else "Dark Mode"
    if st.button(f"{theme_text}", type="secondary", use_container_width=True):
        st.session_state['theme'] = 'light' if st.session_state['theme'] == 'dark' else 'dark'
        st.rerun()
    
    st.markdown("---")
    st.success("🟢 AI System: Online")
    
    # 退出登录按钮 (新增：方便切换账号)
    if st.button("Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['user_name'] = ""
        st.rerun()

    st.markdown("---")
    
    # 重置本地临时数据
    if st.button(
    "Reset Local Data",
    type="secondary",
    use_container_width=True,
    help="Only clears current session data"
):
    

        st.rerun()

# ================= 5. 页面内容控制 =================
page = st.session_state['current_page']

# --- 页面 A: AI 扫描识别 ---
if page == "Home (Scan)":
    with st.container():
        st.title("Advanced AI Math Scanner")
        st.caption(f"Welcome, {st.session_state['user_name']}! Now supporting Arithmetic, Roots, Calculus, and more.")
    
    # ... 其余上传逻辑保持不变 ...
    
    with st.container():
        st.markdown("### 1. Upload Image")
        uploaded_file = st.file_uploader("Choose an image...", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
        
        if uploaded_file:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(uploaded_file, caption="Uploaded Homework", width=500)
            
            if st.button("Start AI Analysis", type="primary", use_container_width=True):
                with st.spinner("AI is analyzing image..."):
                    res = call_ai_ocr(uploaded_file)
                    st.session_state['ocr_result'] = res
                    st.success("Scan Complete!")

    st.markdown("---")

    with st.container():
        st.markdown("### 2. Verify & Process")
        current_text = st.session_state.get('ocr_result', "")
        user_input = st.text_area(
            "Recognized Equations (Editable)", 
            value=current_text, 
            height=150,
            placeholder="Waiting for scan result..."
        )
        
        if st.button("Confirm & Generate Lessons", use_container_width=True):
            if user_input:
                with st.spinner("AI is generating learning guide..."):
                    new_data = parse_and_solve(user_input)
                    if new_data:
                        new_df = pd.DataFrame(new_data)
                        st.session_state['global_db'] = pd.concat([st.session_state['global_db'], new_df], ignore_index=True)
                        st.success(f"Success! {len(new_data)} equations processed. Check Dashboard.")
                    else:
                        st.error("No valid equations found.")
            else:
                st.warning("Input is empty.")

# --- 页面 B: 数据统计仪表盘 ---
elif page == "My Dashboard":
    st.title("Learning Dashboard")
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
            c4.metric("Weak Spot", top_issue)
        
        if not wrong_df.empty:
            st.markdown("---")
            chart_data = wrong_df['Error Type'].value_counts().reset_index()
            chart_data.columns = ['Type', 'Count']
            chart = alt.Chart(chart_data).mark_bar(color='#40e0d0').encode(x='Count', y=alt.Y('Type', sort='-x')).properties(height=150)
            st.altair_chart(chart, use_container_width=True)

        st.markdown("---")
        st.subheader("AI Feedback & Review")
        
        display_df = wrong_df if not wrong_df.empty else df
        for index, row in display_df.iterrows():
            with st.container():
                c1, c2, c3 = st.columns([0.5, 2, 2])
                with c1: 
                    # 找到 Dashboard 循环显示错题的地方
                    if row['Status'] == 'Incorrect':
                        with st.expander(f"See AI Analysis"):
                            # row['Explanation'] 现在包含了解释、横线和新题目
                            st.info(f"{row['Explanation']}")
                    else: st.success("")
                with c2: st.markdown(f"**{row['Equation']}**")
                with c3: st.caption(f"Correct Answer: {row['Correct Answer']}")
                
                if row['Status'] == 'Incorrect':
                    with st.expander(f"See AI Analysis"):
                        st.info(f"**Explanation:**\n{row['Explanation']}")
            st.markdown("<hr style='opacity:0.1'>", unsafe_allow_html=True)
    else:
        st.info("No data available. Go to Scan page first.")

# --- 页面 C: 全局联网论坛 (修正版) ---
elif page == "Global Forum":
    st.title("Global Discussion Forum")
    st.caption(f"Logged in as: {st.session_state['user_name']}")

    # --- 1. 发帖区域 ---
    with st.expander("Create a New Post"):
        msg = st.text_area("What's on your mind?", key="new_post_text")
        uploaded_img = st.file_uploader("Upload an image (optional)", type=['png', 'jpg', 'jpeg'])
        
        if st.button("Post to Community", type="primary"):
            if msg or uploaded_img:
                try:
                    img_url = None
                    if uploaded_img:
                        # 生成唯一文件名
                        file_name = f"{st.session_state['user_name']}_{int(pd.Timestamp.now().timestamp())}.jpg"
                        # 上传到存储桶
                        supabase.storage.from_("forum_images").upload(file_name, uploaded_img.getvalue())
                        # 获取链接
                        img_url = supabase.storage.from_("forum_images").get_public_url(file_name)

                    supabase.table("forum").insert({
                        "username": st.session_state['user_name'], 
                        "content": msg,
                        "image_url": img_url
                    }).execute()
                    st.success("Posted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Post failed: {e}. (Make sure bucket 'forum_images' is created in Supabase Storage)")

    st.markdown("---")

    # --- 2. 消息列表 ---
    try:
        posts_res = supabase.table("forum").select("*").order("id", desc=True).limit(20).execute()
        for p in posts_res.data:
            with st.container():
                st.markdown(f"<strong style='color: #40e0d0;'>@{p['username']}</strong>", unsafe_allow_html=True)
                if p['content']:
                    st.write(p['content'])
                
                # 图片展开
                if p.get('image_url'):
                    with st.expander("View Image"):
                        st.image(p['image_url'])

                # --- 回复逻辑修正 ---
                replies_res = supabase.table("forum_replies").select("*").eq("post_id", p['id']).order("created_at", desc=False).execute()
                replies = replies_res.data
                
                with st.expander(f"{len(replies)} Replies"):
                    for r in replies:
                        st.markdown(f"**@{r['username']}:** {r['content']}")
                    
                    with st.form(key=f"reply_{p['id']}", clear_on_submit=True):
                        rep_text = st.text_input("Reply...")
                        if st.form_submit_button("Send"):
                            if rep_text:
                                supabase.table("forum_replies").insert({
                                    "post_id": p['id'],
                                    "username": st.session_state['user_name'],
                                    "content": rep_text
                                }).execute()
                                st.rerun()
            st.markdown("---")
    except Exception as e:
        st.error(f"Error loading feed: {e}")

# ================= 6. 右下角浮动AI聊天组件 =================
# 添加固定定位的CSS样式
st.markdown("""
<style>
/* 固定在右下角的聊天容器 */
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stVerticalBlock"] > div[data-testid="stButton"] > button:contains("AI")) {
    position: fixed !important;
    bottom: 20px !important;
    right: 20px !important;
    z-index: 9999 !important;
}

/* 浮动按钮样式增强 */
.chat-float-btn {
    position: fixed;
    bottom: 25px;
    right: 25px;
    z-index: 99999;
}

/* 聊天窗口固定样式 */
.chat-window-fixed {
    position: fixed;
    bottom: 90px;
    right: 25px;
    width: 360px;
    z-index: 99998;
    background: linear-gradient(135deg, rgba(20, 25, 40, 0.98) 0%, rgba(30, 40, 60, 0.98) 100%);
    border-radius: 16px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(64, 224, 208, 0.3);
    backdrop-filter: blur(20px);
    padding: 15px;
}
</style>
""", unsafe_allow_html=True)

# 在页面最右下角添加浮动聊天
with st.container():
    # 使用空列来推到右边
    _, _, _, chat_col = st.columns([1, 1, 1, 1])
    
    with chat_col:
        # 浮动按钮
        if st.button("💬 AI Chat" if not st.session_state['ai_chat_open'] else "✕ Close Chat", 
                     key="float_ai_btn", 
                     type="primary",
                     use_container_width=True):
            st.session_state['ai_chat_open'] = not st.session_state['ai_chat_open']
            st.rerun()

# 聊天窗口（展开时显示）
if st.session_state['ai_chat_open']:
    # 使用popover或expander的效果
    with st.container():
        _, _, chat_window = st.columns([1, 1, 2])
        
        with chat_window:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #40e0d0 0%, #00d4ff 100%); 
                        color: #0a0e27; padding: 12px 16px; border-radius: 12px 12px 0 0; 
                        font-weight: 700; margin-bottom: 0;">
                🤖 AI Math Assistant
            </div>
            """, unsafe_allow_html=True)
            
            # 聊天历史容器
            chat_box = st.container(height=250)
            with chat_box:
                if not st.session_state['ai_chat_history']:
                    st.markdown("*👋 Hi! I'm your AI math tutor. Ask me anything!*")
                else:
                    for msg in st.session_state['ai_chat_history']:
                        if msg['role'] == 'user':
                            st.markdown(f"""
                            <div style="text-align: right; margin: 8px 0;">
                                <span style="background: linear-gradient(135deg, #40e0d0, #00d4ff); 
                                             color: #0a0e27; padding: 8px 12px; border-radius: 12px; 
                                             display: inline-block; max-width: 85%;">
                                    {msg['content']}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="text-align: left; margin: 8px 0;">
                                <span style="background: rgba(64, 224, 208, 0.15); 
                                             color: #e0e7ff; padding: 8px 12px; border-radius: 12px; 
                                             display: inline-block; max-width: 85%; 
                                             border: 1px solid rgba(64, 224, 208, 0.3);">
                                    {msg['content']}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
            
            # 输入表单
            with st.form(key="ai_chat_form_float", clear_on_submit=True):
                user_q = st.text_input("Ask a question...", 
                                       placeholder="e.g., How to solve x² + 5x + 6 = 0?",
                                       label_visibility="collapsed")
                col1, col2 = st.columns([3, 1])
                with col1:
                    send = st.form_submit_button("Send", type="primary", use_container_width=True)
                with col2:
                    clear = st.form_submit_button("🗑️", use_container_width=True)
                
                if send and user_q:
                    st.session_state['ai_chat_history'].append({"role": "user", "content": user_q})
                    with st.spinner("Thinking..."):
                        response = get_ai_chat_response(user_q, st.session_state['ai_chat_history'])
                        st.session_state['ai_chat_history'].append({"role": "assistant", "content": response})
                    st.rerun()
                
                if clear:
                    st.session_state['ai_chat_history'] = []
                    st.rerun()








