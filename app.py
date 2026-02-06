import streamlit as st
import pandas as pd
from rag_engine import RagEngine
import yfinance as yf
from quant_backend import WatchlistManager, DataEngine, RiskRadar, DeepAnalyzer, NewsEngine, MarketUniverse


# ================= 0. 语言配置 (i18n) =================
# 在侧边栏最顶部添加语言选择
if 'language' not in st.session_state:
    st.session_state['language'] = 'English'

# 文本字典
TRANSLATIONS = {
    'English': {
        'sidebar_title': "📡 Control Panel",
        'mode_label': "Work Mode:",
        'mode_screener': "🔍 Market Screener",
        'mode_deep': "📊 Deep Dive",
        'mode_pdf': "📑 AI PDF Analyst",
        'screener_title': "🇺🇸 US Market Core Assets",
        'deep_title': "🔎 Comprehensive Report",
        'pdf_title': "📑 AI Financial Report Generator",
        'pdf_caption': "Upload PDF -> Extract Data -> Generate Report (Auto-Pilot)",
        'api_key': "DeepSeek API Key:",
        'upload_label': "📂 Drag and drop PDF",
        'btn_generate': "🚀 Generate Deep Research Report",
        'processing': "🤖 AI is analyzing the full document...",
        'download': "📥 Download Report (Markdown)",
        'error_key': "❌ Please enter API Key",
        'error_file': "❌ Please upload a file",
        'status_ocr': "OCR & Text Cleaning...",
        'status_chunk': "Splitting Data Chunks...",
        'config': "1. Configuration",
        'report_area': "2. Analysis Result"
    },
    '中文': {
        'sidebar_title': "📡 控制台",
        'mode_label': "工作模式:",
        'mode_screener': "🔍 市场海选 (Screener)",
        'mode_deep': "📊 深度监控 (Deep Dive)",
        'mode_pdf': "📑 AI 财报解读 (PDF Analyst)",
        'screener_title': "🇺🇸 美股核心海选",
        'deep_title': "🔎 个股深研报告",
        'pdf_title': "📑 智能财报研报生成器",
        'pdf_caption': "上传财报 -> 自动提取核心数据 -> 生成深度研报 (无需对话)",
        'api_key': "输入 DeepSeek API Key:",
        'upload_label': "📂 拖入财报 PDF",
        'btn_generate': "🚀 立即生成深度研报",
        'processing': "🤖 AI 正在阅读全文档并撰写报告...",
        'download': "📥 下载报告 (Markdown)",
        'error_key': "❌ 请先输入 API Key",
        'error_file': "❌ 请先上传文件",
        'status_ocr': "正在进行 OCR 与文本清洗...",
        'status_chunk': "正在切分关键数据块...",
        'config': "1. 配置与上传",
        'report_area': "2. 分析报告"
    }
}


# ================= 1. 页面初始化配置 =================
st.set_page_config(
    page_title="AI Fund Manager | 修复版",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化后端管理器
wm = WatchlistManager()

# 初始化 Session State (这是修复的关键！)
if 'scan_result' not in st.session_state:
    st.session_state['scan_result'] = None


# 缓存雷达数据
@st.cache_data(ttl=300)
def get_cached_radar(ticker):
    return RiskRadar.analyze_anomalies(ticker)


# ================= 2. 侧边栏：核心雷达 =================
with st.sidebar:
    # 语言选择器 (放在最上面)
    lang_opt = st.radio("Language / 语言", ["English", "中文"], horizontal=True)
    st.session_state['language'] = lang_opt
    T = TRANSLATIONS[lang_opt] # 获取当前语言包

    st.title(T['sidebar_title'])

    # 模式切换 (使用字典里的文本)
    app_mode = st.radio(
        T['mode_label'],
        [T['mode_screener'], T['mode_deep'], T['mode_pdf']]
    )

# 2.2 渲染“红绿灯”列表
watchlist = wm.load()
selected_ticker = None

if not watchlist:
    st.sidebar.info("关注池为空，请先去海选添加股票。" if lang_opt == '中文' else "Watchlist is empty. Go to Screener to add stocks.")
else:
    radar_options = {}
    for ticker in watchlist:
        data = get_cached_radar(ticker)

        # ... (保留原本的 icon 判断代码) ...
        icon = "⚪"
        if data['level'] == "RED":
            icon = "🔴"
        elif data['level'] == "YELLOW":
            icon = "🟡"
        elif data['level'] == "GREEN":
            icon = "🟢"

        # ✅ 修复点：使用 .get() 安全获取，避免 KeyError
        safe_data = data.get('data', {})
        pct = safe_data.get('change_pct', 0)

        change_display = f"{pct:+.2f}%"

        label = f"{icon} {ticker} ({change_display})"
        radar_options[label] = ticker

    selection = st.sidebar.radio("点击查看详情:" if lang_opt == '中文' else "Select Ticker:", list(radar_options.keys()))
    if selection:
        selected_ticker = radar_options[selection]

# 2.3 快速添加/删除
st.sidebar.markdown("---")
with st.sidebar.expander("管理关注池" if lang_opt == '中文' else "Manage Watchlist"):
    new_t = st.text_input("手动添加代码:" if lang_opt == '中文' else "Add Ticker:", placeholder="AAPL").upper()
    if st.button("添加" if lang_opt == '中文' else "Add"):
        if wm.add(new_t):
            st.rerun()
        else:
            st.sidebar.warning("已存在" if lang_opt == '中文' else "Exists")

    if selected_ticker and st.button(f"移除 {selected_ticker}" if lang_opt == '中文' else f"Remove {selected_ticker}"):
        wm.remove(selected_ticker)
        st.rerun()

# ================= 3. 主界面逻辑 =================
# --- 场景 A: 市场海选 (Broad Scan) ---
# 🔴 关键修复：使用 T['mode_screener'] 进行判断
if app_mode == T['mode_screener']:
    st.title(T['screener_title']) # 使用字典标题
    st.caption("从 S&P 100 核心资产中，寻找被低估的优质标的。" if lang_opt == '中文' else "Find undervalued assets from S&P 100 core constituents.")

    # ================= [新增功能 1] 快速搜索添加 =================
    with st.expander("⚡ 快速添加通道 (直接输入代码)" if lang_opt == '中文' else "⚡ Quick Add (Ticker Symbol)", expanded=False):
        c1, c2 = st.columns([4, 1])
        with c1:
            quick_ticker = st.text_input("输入股票代码 (如 TSLA)" if lang_opt == '中文' else "Enter Symbol (e.g. TSLA)", placeholder="TSLA",
                                         label_visibility="collapsed").upper().strip()
        with c2:
            if st.button("➕ 立即添加" if lang_opt == '中文' else "➕ Add", use_container_width=True):
                if quick_ticker:
                    # 调用后端添加逻辑
                    if wm.add(quick_ticker):
                        st.toast(f"✅ {quick_ticker} 已加入关注池！", icon="🎉")
                        st.rerun()  # 强制刷新以更新侧边栏
                    else:
                        st.warning(f"⚠️ {quick_ticker} 已存在或无效")
                else:
                    st.warning("请输入代码")

    st.markdown("---")

    # ================= 原有海选逻辑 =================
    col_roe, col_pe = st.columns(2)

    with col_roe:
        min_roe = st.number_input("最低 ROE (%)" if lang_opt == '中文' else "Min ROE (%)", value=15.0, step=1.0) / 100

    with col_pe:
        max_pe = st.number_input("最高 P/E (倍)" if lang_opt == '中文' else "Max P/E", value=40.0, step=1.0)

    # 锁定美股池
    us_market_key = "🇺🇸 美股市场 (S&P 100核心)"
    target_pool = MarketUniverse.get_tickers_by_market(us_market_key)

    st.markdown(f"ℹ️ *当前锁定扫描 {len(target_pool)} 只 S&P 100 核心成分股*" if lang_opt == '中文' else f"ℹ️ *Scanning {len(target_pool)} S&P 100 constituents*")

    if st.button("🚀 开始扫描" if lang_opt == '中文' else "🚀 Start Scan", type="primary", use_container_width=True):
        progress_text = "AI 正在连接交易所读取财报..." if lang_opt == '中文' else "AI is fetching financial data..."
        my_bar = st.progress(0, text=progress_text)
        df = DataEngine.run_screener(target_pool, min_roe=min_roe, max_pe=max_pe)
        st.session_state['scan_result'] = df
        my_bar.progress(100, text="扫描完成！" if lang_opt == '中文' else "Scan Complete!")

    # ================= [新增功能 2] 结果精选添加 =================
    if st.session_state['scan_result'] is not None:
        df_result = st.session_state['scan_result']

        if not df_result.empty:
            st.success(f"🎯 命中 {len(df_result)} 只符合策略的股票" if lang_opt == '中文' else f"🎯 Found {len(df_result)} matching stocks")

            # 显示结果表格
            st.dataframe(
                df_result[['symbol', 'name', 'price', 'pe', 'roe_pct', 'market_cap_b']],
                column_config={
                    "symbol": "Code", "name": "Name",
                    "price": st.column_config.NumberColumn("Price", format="$%.2f"),
                    "pe": st.column_config.NumberColumn("P/E", format="%.1f"),
                    "roe_pct": st.column_config.NumberColumn("ROE", format="%.1f%%"),
                    "market_cap_b": st.column_config.NumberColumn("Mkt Cap (B)", format="$%.1fB"),
                },
                use_container_width=True,
                hide_index=True
            )

            st.markdown("### 📥 批量入库" if lang_opt == '中文' else "### 📥 Batch Add to Watchlist")
            all_candidates = df_result['symbol'].tolist()

            # 使用多选框让用户挑选
            selected_stocks = st.multiselect(
                "👇 请勾选你想要加入关注池的股票：" if lang_opt == '中文' else "👇 Select stocks to watch:",
                options=all_candidates,
                default=all_candidates
            )

            # 按钮只添加被选中的
            if st.button(f"将选中的 {len(selected_stocks)} 只股票加入监控" if lang_opt == '中文' else f"Add {len(selected_stocks)} selected stocks", type="primary"):
                added_count = 0
                for t in selected_stocks:
                    if wm.add(t):
                        added_count += 1

                if added_count > 0:
                    st.toast(f"✅ 成功添加 {added_count} 只新股票！", icon="🎉")
                    st.rerun()
                else:
                    st.info("选中的股票已经在你的关注池里了。" if lang_opt == '中文' else "Selected stocks are already in watchlist.")
        else:
            st.warning("⚠️ 暂无符合条件的股票，请尝试调整筛选参数。" if lang_opt == '中文' else "⚠️ No stocks found. Try adjusting parameters.")

# --- 场景 B: 深度监控 (Deep Dive) ---
# 🔴 关键修复：使用 T['mode_deep'] 进行判断
elif app_mode == T['mode_deep']:
    if not selected_ticker:
        st.info("👈 请在左侧选择一只股票查看深度报告。" if lang_opt == '中文' else "👈 Select a stock from the sidebar.")
    else:
        # 1. 获取基础数据
        report = DeepAnalyzer.get_comprehensive_report(selected_ticker)
        risk = report['risk']
        base = report['base']
        metrics = report.get('metrics', {})

        # 2. 标题区
        st.header(f"{T['deep_title']}: {base['symbol']} - {base['name']}")

        # ================= 3. 核心评分与指标区 =================
        st.markdown(f"### 🎯 {'AI Score' if lang_opt == 'English' else '量化综合评分'}: {report['ai_score']} / 100 ({report.get('rating', 'N/A')})")

        # 进度条
        st.progress(report['ai_score'] / 100)

        # 3.2 关键四维指标
        m1, m2, m3, m4 = st.columns(4)

        # RSI
        rsi_val = metrics.get('rsi', 50)
        m1.metric("RSI", f"{rsi_val:.1f}", help="<30 Oversold, >70 Overbought")

        # PEG
        peg_val = metrics.get('peg')
        peg_display = f"{peg_val:.2f}" if peg_val else "N/A"
        m2.metric("PEG", peg_display, help="<1.0 Undervalued")

        # 净利率
        margin_val = metrics.get('profit_margin', 0)
        m3.metric("Profit Margin", f"{margin_val:.1f}%")

        # Sigma
        sigma_val = risk['data'].get('sigma', 0)
        m4.metric("Sigma", f"{sigma_val}σ", help=">3.0 Extreme Anomaly")

        st.markdown("---")

        # ================= 4. 详细分析区 =================
        c_radar, c_details = st.columns([1, 1])

        with c_radar:
            st.subheader("📡 " + ("Risk Radar" if lang_opt == 'English' else "异常事件雷达"))
            level = risk['level']
            if level == "RED":
                st.error(f"🚨 **CRITICAL (Red)**")
            elif level == "YELLOW":
                st.warning(f"⚠️ **WARNING (Yellow)**")
            elif level == "GREEN":
                st.success(f"✅ **NORMAL (Green)**")
            else:
                st.info("⚪ No Data")

            if risk.get('signals'):
                for s in risk['signals']:
                    st.markdown(f"- {s}")
            else:
                st.caption("No abnormal signals" if lang_opt == 'English' else "暂无明显异常信号")

            with st.expander("Sigma Formula"):
                st.latex(r"\sigma = \frac{| \text{Today's Return} |}{\text{Volatility}_{20d}(\text{Yesterday})}")

        with c_details:
            st.subheader("📝 " + ("Scoring Details" if lang_opt == 'English' else "评分计算过程"))
            if 'details' in report:
                for detail in report['details']:
                    if "+" in detail:
                        st.success(detail)
                    elif "-" in detail:
                        st.error(detail)
                    else:
                        st.info(detail)
            else:
                st.write("No details available")

        # ================= 5. 原理说明 =================
        with st.expander("📚 " + ("Model Logic (3+1 Factors)" if lang_opt == 'English' else "查看 AI 评分底层逻辑 (3+1 因子模型)"), expanded=False):
            if lang_opt == '中文':
                st.markdown("""
                **本模型不依赖黑盒 AI，而是基于经典量化因子加权计算，计算过程透明：**
                **1. 💎 价值因子 (Value) - 30%** (PEG < 1)
                **2. 🏆 质量因子 (Quality) - 30%** (ROE & Margin)
                **3. 🌊 技术因子 (Momentum) - 40%** (RSI & Sigma)
                """)
            else:
                st.markdown("""
                **Transparent Quant Model based on classic factors:**
                **1. 💎 Value (30%)**: PEG Ratio < 1 implies undervaluation.
                **2. 🏆 Quality (30%)**: ROE & Profit Margin checks.
                **3. 🌊 Momentum (40%)**: RSI for mean reversion & Sigma for volatility.
                """)

        # ================= 6. 舆情与图表 =================
        st.markdown("---")
        st.subheader("📰 " + ("AI News Sentiment" if lang_opt == 'English' else "AI 舆情顾问"))

        news_data = NewsEngine.get_sentiment_analysis(selected_ticker)

        col_s1, col_s2 = st.columns([1, 3])
        with col_s1:
            score = news_data['score']
            label = "Neutral"
            if news_data['level'] == "POSITIVE":
                label = "Positive"
            elif news_data['level'] == "NEGATIVE":
                label = "Negative"
            st.metric("Sentiment Score", f"{score}", label)

        with col_s2:
            st.info(f"💡 **Suggestion:** {news_data['suggestion']}")

        with st.expander("Top News" if lang_opt == 'English' else "查看最新头条原文 (Top 5)", expanded=True):
            if news_data['articles']:
                for news in news_data['articles']:
                    st.markdown(f"{news['icon']} [{news['title']}]({news['link']})")
                    if news.get('pubDate'): st.caption(f"Date: {news['pubDate']}")
            else:
                st.write("No news found.")

        # 技术走势图
        st.markdown("---")
        st.subheader(f"📉 {selected_ticker} Chart")
        try:
            chart_data = yf.Ticker(selected_ticker).history(period="6mo")
            st.line_chart(chart_data['Close'])
        except:
            st.write("Chart Error")

        # 删除按钮
        st.markdown("---")
        if st.button(f"🗑️ Remove {selected_ticker}"):
            wm.remove(selected_ticker)
            st.rerun()

# --- 场景 C: AI 财报解读 (自动研报版) ---
# 🔴 关键修复：使用 T['mode_pdf'] 进行判断
elif app_mode == T['mode_pdf']:
    st.title(T['pdf_title']) # 使用字典标题
    st.caption(T['pdf_caption'])

    # 初始化
    if 'rag_engine' not in st.session_state:
        st.session_state['rag_engine'] = RagEngine()

    # 布局
    col_config, col_report = st.columns([1, 2])

    with col_config:
        st.subheader(T['config'])
        api_key = st.text_input(T['api_key'], type="password")
        uploaded_file = st.file_uploader(T['upload_label'], type=["pdf"])

        # 处理文件上传
        if uploaded_file:
            if 'last_file' not in st.session_state or st.session_state['last_file'] != uploaded_file.name:
                with st.status(T['processing'], expanded=True) as status:
                    st.write(T['status_ocr'])
                    msg = st.session_state['rag_engine'].process_pdf(uploaded_file)
                    st.write(T['status_chunk'])
                    status.update(label=msg, state="complete", expanded=False)
                    st.session_state['last_file'] = uploaded_file.name
                    st.session_state['report_content'] = None

        st.markdown("---")
        generate_btn = st.button(T['btn_generate'], type="primary", use_container_width=True)

    with col_report:
        st.subheader(T['report_area'])

        if generate_btn:
            if not api_key:
                st.error(T['error_key'])
            elif not uploaded_file:
                st.error(T['error_file'])
            else:
                with st.spinner(T['processing']):
                    # 传入当前语言选项
                    report = st.session_state['rag_engine'].generate_report(api_key, lang=st.session_state['language'])
                    st.session_state['report_content'] = report

        if st.session_state.get('report_content'):
            st.markdown(st.session_state['report_content'])
            st.download_button(
                label=T['download'],
                data=st.session_state['report_content'],
                file_name=f"{uploaded_file.name}_report.md",
                mime="text/markdown"
            )
        else:
            st.info("👈 Please upload file and click generate." if lang_opt == 'English' else "👈 请在左侧上传文件并点击生成按钮。")