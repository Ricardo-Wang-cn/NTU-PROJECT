import streamlit as st

from supabase import create_client, Client

# 初始化云端连接 (请替换成你在 Supabase 申请的地址)
SUPABASE_URL = "https://tpokdzclxncdtmfxvkuy.supabase.co"
SUPABASE_KEY = "sb_publishable_ihHrH-gkKfN480wulWcikw_x5JBNPFs"
supabase: Client = create_client("https://tpokdzclxncdtmfxvkuy.supabase.co", "sb_publishable_ihHrH-gkKfN480wulWcikw_x5JBNPFs")

import pandas as pd
import re
import altair as alt
import base64
from openai import OpenAI

# --- 必须放在最前面的初始化代码 ---
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Home (Scan)"

if 'global_db' not in st.session_state:
    st.session_state['global_db'] = pd.DataFrame(columns=['Equation', 'User Answer', 'Correct Answer', 'Status', 'Error Type', 'Timestamp', 'Explanation'])

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""

# 初始化登录状态
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""

# 简单的登录/注册逻辑
def show_login_ui():
    st.title("🔐 Login to Mistake-Driven Learning")
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

# ================= 1. UI 配置 =================
st.set_page_config(
    page_title="Mistake-Driven Learning", 
    page_icon="", 
    layout="wide" 
)

# 初始化主题状态
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'dark'  # 默认深色主题

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
        background: rgba(30, 40, 60, 0.6);
        color: #40e0d0;
        border: 2px solid rgba(64, 224, 208, 0.4);
        backdrop-filter: blur(10px);
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: rgba(64, 224, 208, 0.2);
        color: #40e0d0;
        border-color: rgba(64, 224, 208, 0.6);
        box-shadow: 0 0 15px rgba(64, 224, 208, 0.3);
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
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(100, 116, 139, 0.1);
            margin-top: 1rem;
            border: 1px solid rgba(100, 116, 139, 0.1);
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
            border-bottom: 1px solid rgba(100, 116, 139, 0.1) !important;
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
            border-right: 1px solid rgba(100, 116, 139, 0.1) !important;
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
            border-color: rgba(100, 116, 139, 0.2) !important;
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
            border: 1px solid rgba(100, 116, 139, 0.2);
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
        }
        
        .stButton > button[kind="secondary"] {
            background: rgba(241, 245, 249, 0.9);
            color: #3b82f6;
            border: 2px solid #3b82f6;
        }
        
        /* 侧边栏按钮在浅色模式下 */
        section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
            background: rgba(241, 245, 249, 0.9);
            color: #3b82f6;
            border: 2px solid #3b82f6;
        }
        
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
        }
        
        .stTextArea > div > div > textarea {
            background: rgba(255, 255, 255, 0.9);
            border: 2px solid rgba(100, 116, 139, 0.2);
            color: #1e293b;
        }
        
        div[data-testid="stFileUploader"] {
            background: rgba(255, 255, 255, 0.8);
            border: 2px dashed rgba(59, 130, 246, 0.3);
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
            border-bottom: 1px solid rgba(100, 116, 139, 0.1) !important;
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
    # 统一替换所有可能的符号
    text_block = text_block.replace('÷', '/').replace('x', '*').replace('X', '*')
    text_block = text_block.replace('×', '*')  # 也处理×符号
    text_block = text_block.replace('（', '(').replace('）', ')')
    
    results = []
    timestamp = pd.Timestamp.now().strftime("%H:%M")
    
    lines = text_block.split('\n')
    progress_bar = st.progress(0)
    total_lines = len(lines)
    processed_count = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            processed_count += 1
            if total_lines > 0:
                progress_bar.progress(min(processed_count / total_lines, 1.0))
            continue
            
        # 检查是否包含等号
        if '=' not in line:
            processed_count += 1
            if total_lines > 0:
                progress_bar.progress(min(processed_count / total_lines, 1.0))
            continue
            
        # 分割等号
        parts = line.split('=', 1) 
        if len(parts) != 2: 
            processed_count += 1
            if total_lines > 0:
                progress_bar.progress(min(processed_count / total_lines, 1.0))
            continue
            
        lhs_str = parts[0].strip()
        rhs_str = parts[1].strip()
        
        # 移除左侧表达式中的所有空格
        lhs_str = lhs_str.replace(' ', '').replace('\t', '')
        
        # 如果左侧为空，跳过
        if not lhs_str:
            processed_count += 1
            if total_lines > 0:
                progress_bar.progress(min(processed_count / total_lines, 1.0))
            continue
        
        # 验证左侧表达式：只允许数字、运算符和括号
        # 使用更简单的正则表达式，-号放在字符类末尾
        if not re.match(r'^[0-9+\-*/\.()]+$', lhs_str):
            processed_count += 1
            if total_lines > 0:
                progress_bar.progress(min(processed_count / total_lines, 1.0))
            continue
        
        # 验证右侧是否为有效数字
        try:
            user_ans = float(rhs_str.strip())
        except (ValueError, TypeError):
            processed_count += 1
            if total_lines > 0:
                progress_bar.progress(min(processed_count / total_lines, 1.0))
            continue
            
        # 计算左侧表达式
        try:
            correct_ans = eval(lhs_str)
            # 确保结果是数字
            if not isinstance(correct_ans, (int, float)):
                processed_count += 1
                if total_lines > 0:
                    progress_bar.progress(min(processed_count / total_lines, 1.0))
                continue
        except (SyntaxError, NameError, TypeError, ZeroDivisionError) as e:
            # 如果计算出错，跳过这一行
            processed_count += 1
            if total_lines > 0:
                progress_bar.progress(min(processed_count / total_lines, 1.0))
            continue
        
        # 判断是否正确
        is_right = abs(correct_ans - user_ans) < 0.01
        
        # 判断错误类型
        err_type = "Mixed Ops"
        if '(' in lhs_str: 
            err_type = "Parentheses Priority"
        elif '+' in lhs_str and '*' not in lhs_str and '/' not in lhs_str: 
            err_type = "Addition"
        elif '-' in lhs_str and '*' not in lhs_str and '/' not in lhs_str and '+' not in lhs_str: 
            err_type = "Subtraction"
        elif '*' in lhs_str: 
            err_type = "Multiplication"
        elif '/' in lhs_str: 
            err_type = "Division"
        
        # 显示用的方程（转换回×和÷）
        display_eq = lhs_str.replace('*', '×').replace('/', '÷')
        
        # 生成解释
        explanation = "Correct!"
        if not is_right:
            explanation = get_ai_explanation(display_eq, user_ans, correct_ans)
        
        # 添加到结果
        results.append({
            'Equation': display_eq,
            'User Answer': int(user_ans) if isinstance(user_ans, float) and user_ans.is_integer() else user_ans,
            'Correct Answer': int(correct_ans) if isinstance(correct_ans, float) and correct_ans.is_integer() else (int(correct_ans) if isinstance(correct_ans, int) else correct_ans),
            'Status': "Correct" if is_right else "Incorrect",
            'Error Type': "None" if is_right else err_type,
            'Timestamp': timestamp,
            'Explanation': explanation
        })
        
        processed_count += 1
        if total_lines > 0:
            progress_bar.progress(min(processed_count / total_lines, 1.0))
            
    progress_bar.empty()
    return results

# ================= 4. 侧边栏 (纯净版) =================
# ================= 4. 侧边栏 (导航与系统控制) =================
with st.sidebar:
    # --- 1. 顶部图标 ---
    st.image("https://cdn-icons-png.flaticon.com/512/2997/2997235.png", width=60)
    
    # --- 2. 重要：必须先初始化变量，才能在下面的按钮中使用 ---
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = "Home (Scan)"
    
    # 显示当前登录的用户
    st.markdown(f"👤 **User:** {st.session_state.get('user_name', 'Guest')}")
    st.markdown("---")

    # --- 3. 导航菜单 (Home / Dashboard / Forum) ---
    # 首页扫描
    if st.button("🏠 Home (Scan)", 
                 type="primary" if st.session_state['current_page'] == "Home (Scan)" else "secondary", 
                 use_container_width=True):
        st.session_state['current_page'] = "Home (Scan)"
        st.rerun()
    
    # 学习看板
    if st.button("📊 My Dashboard", 
                 type="primary" if st.session_state['current_page'] == "My Dashboard" else "secondary", 
                 use_container_width=True):
        st.session_state['current_page'] = "My Dashboard"
        st.rerun()
    
    # 全局论坛 (联网功能)
    if st.button("🌐 Global Forum", 
                 type="primary" if st.session_state['current_page'] == "Global Forum" else "secondary", 
                 use_container_width=True):
        st.session_state['current_page'] = "Global Forum"
        st.rerun()
    
    st.markdown("---")
    
    # --- 4. 系统设置 (主题/状态) ---
    
    # 主题切换
    theme_text = "☀️ Light Mode" if st.session_state['theme'] == 'dark' else "🌙 Dark Mode"
    if st.button(f"{theme_text}", type="secondary", use_container_width=True):
        st.session_state['theme'] = 'light' if st.session_state['theme'] == 'dark' else 'dark'
        st.rerun()
    
    st.markdown("---")
    st.success("🟢 AI System: Online")
    
    # 退出登录按钮 (新增：方便切换账号)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['user_name'] = ""
        st.rerun()

    st.markdown("---")
    
    # 重置本地临时数据
    if st.button("🗑️ Reset Local Data", type="secondary", help="Only clears current session data"):
        st.session_state['global_db'] = pd.DataFrame(columns=['Equation', 'User Answer', 'Correct Answer', 'Status', 'Error Type', 'Timestamp', 'Explanation'])
        st.rerun()

# --- 5. 获取当前页面名称，供下方逻辑使用 ---
page = st.session_state['current_page']


# ================= 5. 页面内容控制 =================

# 获取当前显示的页面名称
page = st.session_state['current_page']

# --- 页面 A: AI 扫描识别 ---
if page == "Home (Scan)":
    with st.container():
        st.title("AI Scan & Learn")
        st.caption(f"Welcome, {st.session_state['user_name']}! Upload homework to analyze mistakes.")
    
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
                    if row['Status'] == 'Incorrect': st.error("✘")
                    else: st.success("✔")
                with c2: st.markdown(f"**{row['Equation']}**")
                with c3: st.caption(f"Correct Answer: {row['Correct Answer']}")
                
                if row['Status'] == 'Incorrect':
                    with st.expander(f"See AI Analysis"):
                        st.info(f"**Explanation:**\n{row['Explanation']}")
            st.markdown("<hr style='opacity:0.1'>", unsafe_allow_html=True)
    else:
        st.info("No data available. Go to Scan page first.")

# --- 页面 C: 全局联网论坛 (跨设备交互) ---
# --- 页面 C: 全局联网论坛 (增强版：支持图片与回复) ---
elif page == "Global Forum":
    st.title("🌐 Global Discussion Forum")
    st.caption(f"Share insights & images. Logged in as: {st.session_state['user_name']}")

    # --- 1. 发帖区域 (带图片上传) ---
    with st.expander("📝 Create a New Post (Text & Image)"):
        msg = st.text_area("What's on your mind?", placeholder="Type your message here...", key="new_post_text")
        uploaded_img = st.file_uploader("Upload an image (optional)", type=['png', 'jpg', 'jpeg'], key="forum_img_uploader")
        
        if st.button("Post to Community", type="primary", use_container_width=True):
            if msg or uploaded_img:
                try:
                    img_url = None
                    # 如果有图片，先上传到 Supabase Storage
                    if uploaded_img:
                        file_path = f"public/{st.session_state['user_name']}_{pd.Timestamp.now().timestamp()}.jpg"
                        # 上传文件
                        supabase.storage.from_("forum_images").upload(file_path, uploaded_img.getvalue())
                        # 获取公开访问链接
                        img_url = supabase.storage.from_("forum_images").get_public_url(file_path)

                    # 将帖子存入数据库
                    supabase.table("forum").insert({
                        "username": st.session_state['user_name'], 
                        "content": msg,
                        "image_url": img_url
                    }).execute()
                    st.success("Posted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Post failed: {e}")

    st.markdown("---")

    # --- 2. 消息列表显示 (带回复与图片展开) ---
    st.subheader("Community Feed")
    try:
        # 获取帖子列表
        posts_res = supabase.table("forum").select("*").order("id", desc=True).limit(30).execute()
        posts = posts_res.data
        
        if posts:
            for p in posts:
                # 帖子主体容器
                with st.container():
                    # 顶部：用户信息与时间
                    col_user, col_time = st.columns([1, 1])
                    col_user.markdown(f"<strong style='color: #40e0d0; font-size: 1.1rem;'>@{p['username']}</strong>", unsafe_allow_html=True)
                    col_time.markdown(f"<div style='text-align: right; color: gray; font-size: 0.8rem;'>{p['created_at'][:16].replace('T', ' ')}</div>", unsafe_allow_html=True)
                    
                    # 内容：文字
                    if p['content']:
                        st.markdown(f"<p style='color: #e0e7ff; font-size: 1.05rem; margin: 10px 0;'>{p['content']}</p>", unsafe_allow_html=True)
                    
                    # 内容：图片 (如果有图片，显示展开按钮)
                    if p['image_url']:
                        with st.expander("🖼️ View Attached Image"):
                            st.image(p['image_url'], use_container_width=True)
                    
                    # --- 回复区 (核心修改：点击展开) ---
                    # 获取该帖子的回复
                    replies_res = supabase.table("forum_replies").select("*").eq("post_id", p['id']).order("created_at", asc=True).execute()
                    replies = replies_res.data
                    
                    reply_label = f"💬 {len(replies)} Replies" if replies else "💬 Reply to this"
                    
                    with st.expander(reply_label):
                        # 显示已有回复
                        for r in replies:
                            st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 8px; margin-bottom: 5px; border-left: 2px solid #40e0d0;">
                                <span style="color: #40e0d0; font-weight: bold;">@{r['username']}:</span>
                                <span style="color: #cbd5e1;">{r['content']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # 发表新回复
                        with st.form(key=f"reply_form_{p['id']}", clear_on_submit=True):
                            new_reply = st.text_input("Write a reply...", key=f"input_{p['id']}")
                            if st.form_submit_button("Reply"):
                                if new_reply:
                                    supabase.table("forum_replies").insert({
                                        "post_id": p['id'],
                                        "username": st.session_state['user_name'],
                                        "content": new_reply
                                    }).execute()
                                    st.rerun()

                    st.markdown("<hr style='opacity: 0.1; margin: 20px 0;'>", unsafe_allow_html=True)
        else:
            st.info("The forum is empty. Start the conversation!")
            
    except Exception as e:
        st.error(f"Could not load posts: {e}")








