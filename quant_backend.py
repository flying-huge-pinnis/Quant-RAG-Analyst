from textblob import TextBlob
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime


# ================= 1. 数据持久化层 (Persistence Layer) =================
# 负责把你的“关注池”保存到硬盘上的 JSON 文件中
class WatchlistManager:
    def __init__(self, filename="watchlist.json"):
        self.filename = filename
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                # 默认初始化一些股票
                json.dump(["AAPL", "NVDA", "MSFT"], f)

    def load(self):
        """读取关注列表"""
        try:
            with open(self.filename, 'r') as f:
                return list(set(json.load(f)))  # 去重
        except:
            return []

    def add(self, ticker):
        """添加股票"""
        current = self.load()
        ticker = ticker.upper().strip()
        if ticker not in current:
            current.append(ticker)
            self._save(current)
            return True
        return False

    def remove(self, ticker):
        """移除股票"""
        current = self.load()
        if ticker in current:
            current.remove(ticker)
            self._save(current)
            return True
        return False

    def _save(self, data):
        with open(self.filename, 'w') as f:
            json.dump(data, f)


# ================= 2. 数据获取与海选层 (Data & Screener Layer) =================
class DataEngine:
    @staticmethod
    def get_fundamentals(ticker):
        """获取静态基本面数据（用于筛选和对比）"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                "symbol": ticker,
                "name": info.get('shortName', ticker),
                "price": info.get('currentPrice', 0),
                "pe": info.get('trailingPE', None),
                "roe": info.get('returnOnEquity', 0),  # 小数
                "market_cap": info.get('marketCap', 0),
                "debt_to_equity": info.get('debtToEquity', None)
            }
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    @staticmethod
    def run_screener(stock_pool, min_roe=0.15, max_pe=50):
        """执行海选逻辑"""
        results = []
        for ticker in stock_pool:
            data = DataEngine.get_fundamentals(ticker)
            if data and data['roe'] and data['pe']:
                # 筛选条件
                if data['roe'] > min_roe and 0 < data['pe'] < max_pe:
                    # 格式化数据方便前端展示
                    data['roe_pct'] = round(data['roe'] * 100, 2)
                    data['pe'] = round(data['pe'], 2)
                    data['market_cap_b'] = round(data['market_cap'] / 1e9, 2)
                    results.append(data)

        # 返回 DataFrame 方便排序
        return pd.DataFrame(results) if results else pd.DataFrame()


# ================= 3. 风险雷达层 (Risk Radar Layer) =================
# ================= 3. 风险雷达层 (Risk Radar Layer) [升级版] =================
class RiskRadar:
    @staticmethod
    def analyze_anomalies(ticker):
        """
        核心风控逻辑：分析单只股票的异常状态
        [升级] 引入 Sigma 系数，用统计学定义“异常”，而非死板的百分比。
        """
        try:
            stock = yf.Ticker(ticker)
            # 获取 6个月数据，为了计算更稳定的 20日/60日 波动率
            hist = stock.history(period="6mo")

            if hist.empty or len(hist) < 21:
                return {"level": "GRAY", "signals": ["数据不足"]}

            # --- 1. 数据清洗与准备 ---
            # 计算日收益率 (Pct Change)
            hist['Return'] = hist['Close'].pct_change()

            # 提取最新数据
            current_close = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            current_return = hist['Return'].iloc[-1]  # 今天的涨跌幅

            # 量能数据
            current_vol = hist['Volume'].iloc[-1]
            avg_vol_20 = hist['Volume'].rolling(window=20).mean().iloc[-1]
            vol_ratio = current_vol / (avg_vol_20 + 1)

            # --- 2. Sigma (异常系数) 计算核心 ---
            # 计算过去 20 天的日波动率 (标准差)
            # 注意：我们要用“昨天为止”的波动率来衡量“今天”的跌幅是否异常
            hist['Volatility_20d'] = hist['Return'].rolling(window=20).std()

            # 获取基准波动率 (昨天的 rolling std)
            base_volatility = hist['Volatility_20d'].iloc[-2]

            # 防止除以0
            if base_volatility == 0 or np.isnan(base_volatility):
                sigma = 0
            else:
                # Sigma = |今日涨跌幅| / 历史波动率
                sigma = abs(current_return) / base_volatility

            # --- 3. 🚦 信号判定逻辑 (基于 Sigma) ---
            signals = []
            level = "GREEN"

            # 阈值定义：
            # 1 Sigma = 正常波动 (68% 概率)
            # 2 Sigma = 显著波动 (95% 概率)
            # 3 Sigma = 极端异常 (99.7% 概率)

            # >>> 红色警报 (Critical) <<<
            if sigma > 3.0:
                level = "RED"
                signals.append(f"🚨 {sigma:.1f}σ 极端异常事件")
            elif current_return < -0.07:  # 保留一个绝对跌幅兜底
                level = "RED"
                signals.append(f"📉 暴跌 {current_return * 100:.1f}%")

            if vol_ratio > 3.0:
                if level != "RED": level = "RED"  # 量能异常也算红
                signals.append(f"💣 巨量换手 ({vol_ratio:.1f}倍)")

            # >>> 黄色预警 (Warning) <<<
            if level == "GREEN":
                if sigma > 2.0:
                    level = "YELLOW"
                    signals.append(f"⚡ {sigma:.1f}σ 显著波动")
                elif vol_ratio > 1.8:
                    level = "YELLOW"
                    signals.append(f"📢 成交放量 ({vol_ratio:.1f}倍)")

                # 均线检查 (跌破 60日线)
                ma60 = hist['Close'].rolling(window=60).mean().iloc[-1]
                if current_close < ma60 * 0.97:
                    level = "YELLOW"
                    signals.append("📉 有效跌破60日线")

            # >>> 正常状态 <<<
            if not signals:
                signals.append(f"波动平稳 ({sigma:.1f}σ)")

            return {
                "symbol": ticker,
                "level": level,
                "signals": signals,
                "data": {
                    "price": round(current_close, 2),
                    "change_pct": round(current_return * 100, 2),
                    "sigma": round(sigma, 2),
                    "volatility": round(base_volatility * 100, 2)  # 显示基础波动率
                }
            }

        except Exception as e:
            return {"level": "GRAY", "signals": [f"计算错误: {str(e)}"]}


# ================= 4. 深度分析层 (Deep Dive Layer) =================
# ==========================================
# 请将此代码块覆盖 quant_backend.py 中的 DeepAnalyzer 类
# 并确保导入了 pandas (已导入)
# ==========================================

class DeepAnalyzer:
    @staticmethod
    def _calculate_rsi(series, period=14):
        """
        计算 RSI 相对强弱指标 (无需引入 TA-Lib，纯 Pandas 实现，速度极快)
        原理：比较一段时间内的平均涨幅和平均跌幅。
        """
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]  # 只返回最新的 RSI 值

    @staticmethod
    def get_comprehensive_report(ticker):
        # 1. 获取基础数据
        base = DataEngine.get_fundamentals(ticker)

        # 2. 获取风险数据 (复用现有的 RiskRadar)
        risk = RiskRadar.analyze_anomalies(ticker)

        # 3. 获取更详细的财务数据 (yfinance info)
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            # 补充额外指标
            peg = info.get('pegRatio', None)  # 估值神器：PEG
            profit_margin = info.get('profitMargins', 0)  # 净利率

            # 计算技术指标 RSI
            hist = stock.history(period="2mo")  # 取2个月算 RSI 足够了
            if not hist.empty and len(hist) > 15:
                current_rsi = DeepAnalyzer._calculate_rsi(hist['Close'])
            else:
                current_rsi = 50  # 默认中性

        except:
            peg = None
            profit_margin = 0
            current_rsi = 50

        # ====================================================
        # 🧠 量化评分卡模型 (Scoring Card) - 满分 100
        # ====================================================
        score = 0
        details = []

        # --- 维度 A: 盈利与质量 (权重 30分) ---
        # 逻辑：好公司必须能赚钱，且效率高
        roe = base.get('roe', 0)
        if roe > 0.20:
            score += 15
            details.append(f"✅ 盈利能力极强 (ROE {roe:.1%}) [+15]")
        elif roe > 0.10:
            score += 10
            details.append(f"✅ 盈利能力达标 (ROE {roe:.1%}) [+10]")

        if profit_margin > 0.15:
            score += 15
            details.append(f"✅ 产品护城河深 (净利率 {profit_margin:.1%}) [+15]")
        elif profit_margin > 0.05:
            score += 5
            details.append(f"☑️ 净利率正常 ({profit_margin:.1%}) [+5]")

        # --- 维度 B: 估值性价比 (权重 30分) ---
        # 逻辑：好公司也不能买太贵。PEG < 1 是彼得林奇最爱。
        pe = base.get('pe')

        # 优先看 PEG (成长估值)
        if peg is not None and 0 < peg < 1.0:
            score += 30
            details.append(f"💎 估值严重被低估 (PEG {peg} < 1) [+30]")
        elif peg is not None and peg < 1.5:
            score += 20
            details.append(f"💎 估值合理 (PEG {peg}) [+20]")
        # 如果没 PEG，回退看 PE (静态估值)
        elif pe and 0 < pe < 20:
            score += 20
            details.append(f"⚖️ 市盈率低 (PE {pe:.1f}) [+20]")
        elif pe and 20 <= pe < 40:
            score += 10
            details.append(f"⚖️ 市盈率中等 (PE {pe:.1f}) [+10]")

        # --- 维度 C: 技术与趋势 (权重 40分) ---
        # 逻辑：不要在下跌趋势接飞刀，不要在历史高点追高

        # 1. 波动率惩罚 (基于 Sigma)
        sigma = risk['data'].get('sigma', 0)
        if sigma < 1.5:
            score += 10
            details.append(f"🌊 走势平稳 (Sigma {sigma}σ) [+10]")
        elif sigma > 3.0:
            score -= 20  # 严重惩罚
            details.append(f"🚨 极端异常波动 (Sigma {sigma}σ) [-20]")

        # 2. RSI 超买超卖判断
        # RSI < 30 为超卖(机会)，RSI > 70 为超买(风险)
        if current_rsi < 30:
            score += 20
            details.append(f"📉 处于超卖区间，反弹概率大 (RSI {current_rsi:.1f}) [+20]")
        elif 30 <= current_rsi <= 70:
            score += 10
            details.append(f"➡️ 处于中性区间 (RSI {current_rsi:.1f}) [+10]")
        elif current_rsi > 80:
            score -= 10
            details.append(f"🔥 严重超买，回调风险大 (RSI {current_rsi:.1f}) [-10]")

        # 3. 趋势确认 (基于 RiskRadar 的信号)
        if risk['level'] == 'GREEN':
            score += 10
            details.append("📈 趋势健康 (无风险信号) [+10]")
        elif risk['level'] == 'RED':
            score -= 10
            details.append("🩸 触发生命线警报 [-10]")

        # --- 最终分值修正 ---
        final_score = max(0, min(100, score))

        # 生成评级标签
        rating = "观望"
        if final_score >= 80:
            rating = "强力买入"
        elif final_score >= 60:
            rating = "增持"
        elif final_score >= 40:
            rating = "中性"
        else:
            rating = "减持/卖出"

        return {
            "base": base,
            "risk": risk,
            "ai_score": final_score,
            "rating": rating,
            "details": details,
            "metrics": {
                "peg": peg,
                "rsi": round(current_rsi, 1),
                "profit_margin": round(profit_margin * 100, 1)
            }
        }

# ... 之前的代码保持不变 ...
from textblob import TextBlob  # 引入自然语言处理库


# ================= 5. 舆情情报层 (News Intelligence Layer) =================
# 修改 quant_backend.py 中的 NewsEngine
# 确保文件头部引入了 TextBlob
from textblob import TextBlob
import yfinance as yf


# ... (前面的类保持不变) ...
# 确保文件头部引入了 TextBlob

class NewsEngine:
    @staticmethod
    def get_sentiment_analysis(ticker):
        print(f"--- [DEBUG] 正在抓取 {ticker} 新闻 ---")
        try:
            stock = yf.Ticker(ticker)
            news_list = stock.news

            if not news_list:
                return {"score": 0, "suggestion": "暂无新闻数据", "level": "NEUTRAL", "articles": []}

            total_polarity = 0
            valid_articles = 0
            analyzed_news = []

            for article in news_list[:5]:
                # ====================================================
                # 🔧 核心修复：智能解析嵌套结构
                # ====================================================

                # 1. 判断数据是在外层，还是在 'content' 里层
                raw_data = article.get('content', article)

                # 2. 提取标题 (兼容 title, headline, summary)
                title = raw_data.get('title') or raw_data.get('headline') or raw_data.get('summary') or ''

                # 3. 提取链接 (Yahoo 的链接结构非常复杂，做多重尝试)
                link = '#'
                if 'clickThroughUrl' in raw_data and raw_data['clickThroughUrl']:
                    link = raw_data['clickThroughUrl'].get('url', '#')
                elif 'canonicalUrl' in raw_data and raw_data['canonicalUrl']:
                    link = raw_data['canonicalUrl'].get('url', '#')
                else:
                    link = raw_data.get('link', raw_data.get('url', '#'))

                # 4. 提取时间
                pub_date = raw_data.get('pubDate', raw_data.get('providerPublishTime', ''))
                # ====================================================

                if not title:
                    continue

                # 简单中文过滤
                is_chinese = any(u'\u4e00' <= c <= u'\u9fff' for c in title)

                sentiment_icon = "⚪"
                polarity = 0

                if not is_chinese:
                    try:
                        analysis = TextBlob(title)
                        polarity = analysis.sentiment.polarity
                        if polarity != 0:
                            valid_articles += 1

                        if polarity > 0.1:
                            sentiment_icon = "🟢"
                        elif polarity < -0.1:
                            sentiment_icon = "🔴"
                    except:
                        pass

                total_polarity += polarity

                analyzed_news.append({
                    "title": title,
                    "link": link,
                    "icon": sentiment_icon,
                    "pubDate": pub_date
                })

            # 计算平均分
            if valid_articles > 0:
                avg_score = total_polarity / valid_articles
            else:
                avg_score = 0

            # 生成建议
            suggestion = "消息面平稳"
            level = "NEUTRAL"

            if avg_score > 0.15:
                suggestion = "🔥 消息面乐观 (利好驱动)"
                level = "POSITIVE"
            elif avg_score < -0.15:
                suggestion = "☔ 消息面悲观 (利空阴云)"
                level = "NEGATIVE"

            return {
                "score": round(avg_score, 2),
                "suggestion": suggestion,
                "level": level,
                "articles": analyzed_news
            }

        except Exception as e:
            print(f"!!! [ERROR] NewsEngine 报错: {e}")
            return {"score": 0, "suggestion": "分析服务异常", "level": "NEUTRAL", "articles": []}


# ... (之前的代码保持不变) ...

# ================= 6. 市场宇宙数据 (Market Universe) =================
# quant_backend.py - 覆盖 MarketUniverse 类

class MarketUniverse:
    """
    预定义的市场核心资产池 (Index Constituents)
    """

    @staticmethod
    def get_market_options():
        return {
            "🇺🇸 美股市场 (S&P 100核心)": [
                'AAPL', 'MSFT', 'NVDA', 'GOOG', 'AMZN', 'META', 'TSLA', 'BRK-B', 'LLY', 'AVGO',
                'JPM', 'V', 'TSM', 'WMT', 'XOM', 'MA', 'UNH', 'PG', 'COST', 'JNJ', 'MRK', 'HD',
                'ABBV', 'BAC', 'KO', 'PEP', 'NFLX', 'AMD', 'CRM', 'ADBE', 'DIS', 'MCD', 'CSCO'
            ],
            "🇭🇰 港股市场 (恒生科技+蓝筹)": [
                '0700.HK', '9988.HK', '3690.HK', '1810.HK', '9618.HK', '1024.HK', '2015.HK',  # 科网
                '0941.HK', '0005.HK', '1299.HK', '0388.HK', '2318.HK', '1211.HK', '0981.HK',  # 金融/蓝筹
                '1750.HK', '9866.HK', '9888.HK', '0883.HK'
            ],
            "🇦🇺 澳洲市场 (ASX 20核心)": [
                'BHP.AX', 'CBA.AX', 'CSL.AX', 'NAB.AX', 'WBC.AX', 'ANZ.AX', 'WDS.AX', 'MQG.AX',
                'WES.AX', 'TLS.AX', 'WOW.AX', 'RIO.AX', 'FMG.AX', 'GMG.AX', 'STO.AX', 'COL.AX'
            ],
            "🇨🇳 A股市场 (部分核心资产)": [
                # 注意：yfinance 对A股支持有时不稳定，需带 .SS 或 .SZ 后缀
                '600519.SS', '300750.SZ', '601318.SS', '600036.SS', '002594.SZ', '601012.SS',
                '000858.SZ', '600276.SS', '000333.SZ', '603288.SS'
            ]
        }

    @staticmethod
    def get_tickers_by_market(market_name):
        options = MarketUniverse.get_market_options()
        return options.get(market_name, [])

    #cd exercises
    #streamlit run app.py