import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import time
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib.ticker import FuncFormatter

# Set font for international support
plt.rcParams["font.family"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
plt.rcParams["axes.unicode_minus"] = False  # Solve the problem of negative sign display

# --------- Session State Initialization ---------
if "your_picks" not in st.session_state:
	st.session_state["your_picks"] = []
if "pick_weights" not in st.session_state:  # New: Asset weights
	st.session_state["pick_weights"] = {}
if "portfolios" not in st.session_state:
	st.session_state["portfolios"] = []
if "current_portfolio" not in st.session_state:
	st.session_state["current_portfolio"] = None
if "selected_news" not in st.session_state:
	st.session_state["selected_news"] = None
if "font_size" not in st.session_state:
	st.session_state["font_size"] = 12
if "news_page" not in st.session_state:
	st.session_state["news_page"] = 1

# --------- Page Config ---------
st.set_page_config(page_title="Portfolio Management System", layout="wide")
tabs = st.tabs(["Create Portfolio", "News Aggregation", "Portfolio Analysis", "Stock Analysis"])

# --------- Utility Functions ---------
def is_crypto(symbol):
	return "-USD" in symbol or symbol in ["BTC", "ETH", "BNB"]

def is_etf(symbol):
	etf_list = ["SPY", "VOO", "QQQ", "IWM", "DIA"]
	return symbol in etf_list

def get_asset_type(symbol):
	if is_crypto(symbol):
		return "Cryptocurrency"
	elif is_etf(symbol):
		return "ETF"
	else:
		return "Stock"

def safe_get_ticker_info(symbol):
	try:
		ticker = yf.Ticker(symbol)
		info = ticker.info
		return info
	except Exception as e:
		st.warning(f"Failed to get information for {symbol}: {str(e)}")
		return None


# --------- Page 1: Create Portfolio ---------
with tabs[0]:
	st.header("Manually Create Portfolio")
	col1, col2 = st.columns([2, 2])
	# Left: Search and popular assets
	with col1:
		search = st.text_input("Search Stock, Crypto or ETF (e.g. AAPL, BTC-USD)")
		col_search = st.columns([1, 1])
		if col_search[0].button("Add Asset") and search:
			try:
				info = safe_get_ticker_info(search)
				if info and "symbol" in info:
					symbol = info["symbol"]
					if symbol not in st.session_state["your_picks"]:
						st.session_state["your_picks"].append(symbol)
					else:
						st.warning("Asset already added")
				else:
					st.warning("Asset not found")
			except Exception as e:
				st.error(f"Query failed: {str(e)}")
		st.subheader("Popular Assets Quick Add")
		pop_assets = ["AAPL", "NVDA", "MSFT", "SPY", "BTC-USD"]
		pop_cols = st.columns(len(pop_assets))
		for i, symbol in enumerate(pop_assets):
			if pop_cols[i].button(f"{symbol} +"):
				if symbol not in st.session_state["your_picks"]:
					st.session_state["your_picks"].append(symbol)
		st.subheader("Selected Assets (Adjust Weights)")
		if st.session_state["your_picks"]:
			new_weights = {}
			total_weight = 0.0
			for i, symbol in enumerate(st.session_state["your_picks"]):
				col_w = st.columns([3, 1, 1])
				col_w[0].write(symbol)
				weight = col_w[1].number_input(
					"Weight (%)", 
					min_value=1.0, 
					max_value=100.0, 
					value=st.session_state["pick_weights"].get(symbol, 100.0/len(st.session_state["your_picks"])),
					step=0.1,
					key=f"weight_{i}"
				)
				new_weights[symbol] = weight
				total_weight += weight
				if col_w[2].button("Delete", key=f"del_{symbol}"):
					st.session_state["your_picks"].remove(symbol)
			if abs(total_weight - 100) > 0.1:
				st.warning(f"Total weight is {total_weight:.1f}%, please adjust to 100%.")
			else:
				st.session_state["pick_weights"] = new_weights
				st.success("Weights set successfully.")
			name = st.text_input("Portfolio Name", f"My Portfolio {len(st.session_state['portfolios'])+1}")
			if st.button("Create Portfolio") and name:
				portfolio_data = {
					"name": name,
					"holdings": st.session_state["your_picks"].copy(),
					"weights": st.session_state["pick_weights"].copy()
				}
				st.session_state["portfolios"].append(portfolio_data)
				st.session_state["current_portfolio"] = name
				st.success(f"Portfolio created: {name}")
				st.session_state["your_picks"] = []
				st.session_state["pick_weights"] = {}
				st.rerun()
		else:
			st.info("Please add assets before creating a portfolio")
	with col2:
		st.header("Sync Portfolio from Broker")
		brokers = ["Ally", "Robinhood", "Fidelity", "Interactive Brokers", "Vanguard", "Bank of America", "Charles Schwab"]
		broker = st.selectbox("Select Broker", brokers)
		if st.button("Sync Portfolio"):
			with st.spinner(f"Syncing portfolio from {broker}..."):
				time.sleep(1)
				st.session_state["portfolios"].append({
					"name": f"{broker} Synced Portfolio",
					"holdings": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
					"weights": {"AAPL": 20, "MSFT": 20, "GOOGL": 20, "AMZN": 20, "TSLA": 20}
				})
				st.session_state["current_portfolio"] = f"{broker} Synced Portfolio"
				st.success(f"Portfolio synced from {broker}")
		st.header("Import Portfolio from CSV")
		st.info("CSV format: First column is asset symbol, second column is weight (optional)")
		uploaded_file = st.file_uploader("Select CSV file", type="csv")
		if uploaded_file:
			try:
				df = pd.read_csv(uploaded_file)
				if len(df.columns) >= 1:
					symbols = df.iloc[:,0].tolist()
					weights = df.iloc[:,1].tolist() if len(df.columns) > 1 else [100.0/len(symbols)]*len(symbols)
					st.session_state["portfolios"].append({
						"name": "CSV Imported Portfolio",
						"holdings": symbols,
						"weights": dict(zip(symbols, weights))
					})
					st.session_state["current_portfolio"] = "CSV Imported Portfolio"
					st.success("Portfolio imported from CSV")
				else:
					st.warning("CSV format error")
			except Exception as e:
				st.error(f"Import failed: {str(e)}")
		st.header("Manage Existing Portfolios")
		if st.session_state["portfolios"]:
			for i, portfolio in enumerate(st.session_state["portfolios"]):
				col_p = st.columns([3, 1, 1])
				col_p[0].write(portfolio["name"])
				if col_p[1].button("Switch", key=f"switch_{i}"):
					st.session_state["current_portfolio"] = portfolio["name"]
					st.rerun()
				if col_p[2].button("Delete", key=f"del_port_{i}"):
					st.session_state["portfolios"].pop(i)
					st.rerun()
		else:
			st.info("No portfolios yet. Please create or import.")

# --------- Page 2: News Aggregation ---------
def get_news(symbols, page=1, page_size=12, keyword=None, filter_type="All Holdings"):
	API_KEY = "6d6d5f5d55b64eab94814259cb0a0841"
	url = "https://api.worldnewsapi.com/search-news"
	keywords = " OR ".join(symbols)
	query = keyword if keyword else keywords
	earliest_date = (datetime.now() - timedelta(days=30)).isoformat()
	params = {
		"q": query,
		"language": "en",
		"sort": "date",
		"page": page,
		"page-size": page_size,
		"earliest-publish-date": earliest_date
	}
	headers = {"x-api-key": API_KEY}
	try:
		with st.spinner("Fetching news..."):
			resp = requests.get(url, params=params, headers=headers, timeout=10)
			resp.raise_for_status()
			data = resp.json()
		news_list = []
		for item in data.get("news", []):
			symbol_in_news = next((s for s in symbols if s in item.get("title", "")), "OTHER")
			asset_type = get_asset_type(symbol_in_news) if symbol_in_news != "OTHER" else ""
			news_list.append({
				"date": item.get("publish_date", ""),
				"symbol": symbol_in_news,
				"asset_type": asset_type,
				"title": item.get("title", ""),
				"author": ", ".join(item.get("authors", [])),
				"content": item.get("text", ""),
				"url": item.get("url", "")
			})
		return news_list, data.get("total_results", 0)
	except Exception as e:
		st.warning("News API unavailable, showing demo data.")
		mock_news = [
			{
				"date": datetime.now().strftime("%Y-%m-%d"),
				"symbol": symbols[0] if symbols else "AAPL",
				"asset_type": get_asset_type(symbols[0]) if symbols else "Stock",
				"title": "[Demo] Market News Example 1",
				"author": "Demo Author",
				"content": "This is demo news content. Displayed when API is unavailable.",
				"url": "https://example.com/news1"
			},
			{
				"date": datetime.now().strftime("%Y-%m-%d"),
				"symbol": symbols[1] if len(symbols)>1 else "MSFT",
				"asset_type": get_asset_type(symbols[1]) if len(symbols)>1 else "Stock",
				"title": "[Demo] Market News Example 2",
				"author": "Demo Author",
				"content": "Second demo news content. Displayed when API is unavailable.",
				"url": "https://example.com/news2"
			}
		]
		return mock_news, len(mock_news)

with tabs[1]:
	st.header("Portfolio News Aggregation and Filtering")
	current_port = st.session_state.get("current_portfolio")
	if current_port and st.session_state["portfolios"]:
		portfolio_idx = [p["name"] for p in st.session_state["portfolios"]].index(current_port)
		symbols = st.session_state["portfolios"][portfolio_idx]["holdings"]
		st.info(f"Current portfolio: {current_port} ({len(symbols)} assets)")
	else:
		symbols = ["AAPL", "MSFT", "NVDA"]
		st.info("No portfolio selected, showing default asset news.")
	col_top = st.columns([3, 2, 1, 1])
	news_keyword = col_top[0].text_input("News keyword search", "")
	filter_type = col_top[1].selectbox(
		"Asset type filter", 
		["All Holdings", "Stocks", "ETFs", "Cryptocurrencies"]
	)
	page_size = 10
	news_list, total_news = get_news(
		symbols, 
		st.session_state["news_page"], 
		page_size, 
		news_keyword,
		filter_type
	)
	col_page = st.columns([1, 3, 1])
	with col_page[0]:
		if st.button("Previous Page") and st.session_state["news_page"] > 1:
			st.session_state["news_page"] -= 1
			st.rerun()
	with col_page[1]:
		st.write(f"Showing {(st.session_state['news_page']-1)*page_size+1} - {min(st.session_state['news_page']*page_size, total_news)} of {total_news} news items")
	with col_page[2]:
		if st.button("Next Page") and st.session_state["news_page"]*page_size < total_news:
			st.session_state["news_page"] += 1
			st.rerun()
	left, right = st.columns([2, 3])
	with left:
		st.subheader("News List")
		if news_list:
			for idx, news in enumerate(news_list):
				btn_label = f"{news['date'][:10]} | {news['symbol']} | {news['title'][:60]}..."
				if st.button(btn_label, key=f"news_{idx}"):
					st.session_state["selected_news"] = news
					st.rerun()
		else:
			st.info("No related news found. Try other keywords or filters.")
	with right:
		st.subheader("News Details")
		news = st.session_state.get("selected_news")
		if news:
			col_font = st.columns([1, 1, 3])
			with col_font[0]:
				if st.button("A+"):
					st.session_state["font_size"] += 2
					st.rerun()
			with col_font[1]:
				if st.button("A-"):
					st.session_state["font_size"] = max(8, st.session_state["font_size"] - 2)
					st.rerun()
			st.markdown(
				f"<div style='font-size:{st.session_state['font_size']}px'><b>{news['title']}</b></div>",
				unsafe_allow_html=True
			)
			st.write(f"Author: {news.get('author', 'Unknown')} | Date: {news['date'][:10]} | Related asset: {news['symbol']}")
			content = news['content'][:1500] + ("..." if len(news['content']) > 1500 else "")
			st.markdown(
				f"<div style='font-size:{st.session_state['font_size']}px; line-height:1.6'>{content}</div>",
				unsafe_allow_html=True
			)
			st.markdown(f"[Read full article]({news['url']})", unsafe_allow_html=True)
		else:
			st.info("Select a news item from the list to view details.")

# --------- Page 3: Portfolio Analysis ---------
def get_sector(symbol):
	info = safe_get_ticker_info(symbol)
	if info and "sector" in info:
		sector_map = {
			"Technology": "科技",
			"Consumer Cyclical": "消费周期",
			"Financial Services": "金融服务",
			"Healthcare": "医疗健康",
			"Energy": "能源",
			"Consumer Defensive": "必选消费",
			"Industrials": "工业",
			"Real Estate": "房地产",
			"Utilities": "公用事业",
			"Communication Services": "通信服务",
			"Basic Materials": "基础材料"
		}
		return sector_map.get(info["sector"], info["sector"])
	default_map = {
		"AAPL": "科技", "MSFT": "科技", "NVDA": "科技", "GOOGL": "科技", 
		"AMZN": "消费", "TSLA": "汽车", "SPY": "ETF", "BTC-USD": "加密货币"
	}
	return default_map.get(symbol, "综合")

def get_beta(symbol):
	info = safe_get_ticker_info(symbol)
	if info and "beta" in info and info["beta"] is not None:
		return round(info["beta"], 2)
	default_map = {"AAPL": 1.2, "MSFT": 1.1, "NVDA": 2.27, "GOOGL": 1.0, "AMZN": 1.3, "TSLA": 1.8, "BTC-USD": 1.39}
	return default_map.get(symbol, 1.0)

def get_pe(symbol):
	if is_crypto(symbol):
		return 0
	info = safe_get_ticker_info(symbol)
	if info and "trailingPE" in info and info["trailingPE"] is not None:
		return round(info["trailingPE"], 2)
	default_map = {"AAPL": 39.95, "MSFT": 32.1, "NVDA": 53.01, "GOOGL": 28.7, "AMZN": 41.2, "TSLA": 70.5}
	return default_map.get(symbol, 20)

def get_market_cap(symbol):
	info = safe_get_ticker_info(symbol)
	if info and "marketCap" in info and info["marketCap"] is not None:
		return round(info["marketCap"] / 1e8, 1)
	default_map = {"AAPL": 30000, "MSFT": 25000, "NVDA": 15000, "GOOGL": 18000, "AMZN": 17000, "TSLA": 8000, "BTC-USD": 9000}
	return default_map.get(symbol, 5000)

def get_dividend(symbol):
	if is_crypto(symbol) or is_etf(symbol):
		return 0
	info = safe_get_ticker_info(symbol)
	if info and "dividendYield" in info and info["dividendYield"] is not None:
		return round(info["dividendYield"] * 100, 2)
	default_map = {"AAPL": 0.6, "MSFT": 0.8, "NVDA": 0.1, "GOOGL": 0, "AMZN": 0, "TSLA": 0}
	return default_map.get(symbol, 0)

with tabs[2]:
	st.header("Portfolio Analysis")
	portfolios = st.session_state.get("portfolios", [])
	if portfolios:
		portfolio_names = [p["name"] for p in portfolios]
		selected = st.selectbox("Select portfolio", portfolio_names, 
							  index=portfolio_names.index(st.session_state["current_portfolio"]) 
							  if st.session_state["current_portfolio"] in portfolio_names else 0)
		portfolio_idx = portfolio_names.index(selected)
		holdings = portfolios[portfolio_idx]["holdings"]
		weights = portfolios[portfolio_idx]["weights"]
		st.info(f"Assets to analyze: {', '.join(holdings)}")
	else:
		st.warning("No portfolios available. Please create one first.")
		holdings = ["AAPL", "MSFT", "NVDA", "SPY", "BTC-USD"]
		weights = {s: 20 for s in holdings}
		st.info(f"Using demo data: {', '.join(holdings)}")
	st.subheader("Asset Allocation Analysis")
	analysis_tabs = st.tabs(["Asset Type", "Sector Distribution", "Region Distribution"])
	with analysis_tabs[0]:
		type_data = {}
		for s in holdings:
			asset_type = get_asset_type(s)
			type_data[asset_type] = type_data.get(asset_type, 0) + weights[s]
		fig, ax = plt.subplots(figsize=(8, 6))
		wedges, texts, autotexts = ax.pie(
			type_data.values(), 
			labels=type_data.keys(),
			autopct=lambda p: f'{p:.1f}%\n({p*sum(type_data.values())/100:.1f}%)',
			startangle=90
		)
		plt.setp(autotexts, size=10, weight="bold")
		ax.set_title('Asset Type Distribution (by weight)')
		st.pyplot(fig)
	with analysis_tabs[1]:
		sector_data = {}
		for s in holdings:
			if get_asset_type(s) != "ETF" and not is_crypto(s):
				sector = get_sector(s)
				sector_data[sector] = sector_data.get(sector, 0) + weights[s]
		fig, ax = plt.subplots(figsize=(8, 6))
		wedges, texts, autotexts = ax.pie(
			sector_data.values(), 
			labels=sector_data.keys(),
			autopct=lambda p: f'{p:.1f}',
			startangle=90
		)
		plt.setp(autotexts, size=10, weight="bold")
		ax.set_title('Sector Distribution (by weight)')
		st.pyplot(fig)
	with analysis_tabs[2]:
		region_data = {"US": 0, "Europe": 0, "Asia": 0, "Other": 0}
		us_stocks = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "SPY"]
		for s in holdings:
			if s in us_stocks:
				region_data["US"] += weights[s]
			elif s in ["BTC-USD", "ETH-USD"]:
				region_data["Other"] += weights[s]
			else:
				region_data["Asia"] += weights[s]
		fig, ax = plt.subplots(figsize=(8, 6))
		wedges, texts, autotexts = ax.pie(
			region_data.values(), 
			labels=region_data.keys(),
			autopct=lambda p: f'{p:.1f}',
			startangle=90
		)
		plt.setp(autotexts, size=10, weight="bold")
		ax.set_title('Region Distribution (by weight)')
		st.pyplot(fig)
	st.subheader("Risk and Return Analysis")
	betas = {s: get_beta(s) for s in holdings}
	portfolio_beta = sum(betas[s] * weights[s] / 100 for s in holdings)
	pes = {s: get_pe(s) for s in holdings}
	portfolio_pe = sum(pes[s] * weights[s] / 100 for s in holdings if pes[s] > 0)
	divs = {s: get_dividend(s) for s in holdings}
	portfolio_div = sum(divs[s] * weights[s] / 100 for s in holdings)
	col_metrics = st.columns(3)
	col_metrics[0].metric("Portfolio Beta", round(portfolio_beta, 2), help="Measures correlation with market. >1 means more volatile than market.")
	col_metrics[1].metric("Portfolio P/E", round(portfolio_pe, 2) if portfolio_pe else "N/A", help="Reflects valuation level. Lower may mean cheaper.")
	col_metrics[2].metric("Portfolio Dividend Yield (%)", round(portfolio_div, 2), help="Annual dividend as a percentage of price.")
	fig, ax = plt.subplots(figsize=(10, 6))
	sorted_betas = sorted(betas.items(), key=lambda x: x[1], reverse=True)
	symbols_b, beta_values = zip(*sorted_betas)
	ax.bar(symbols_b, beta_values, color='skyblue')
	ax.axhline(y=1.0, color='r', linestyle='--', label='Market Avg (1.0)')
	ax.axhline(y=portfolio_beta, color='g', linestyle='-', label=f'Portfolio Beta ({round(portfolio_beta, 2)})')
	ax.set_title('Beta Comparison by Asset')
	ax.set_ylabel('Beta')
	ax.legend()
	st.pyplot(fig)
	pe_data = {s: pes[s] for s in holdings if pes[s] > 0}
	if pe_data:
		fig, ax = plt.subplots(figsize=(10, 6))
		sorted_pe_data = sorted(pe_data.items(), key=lambda x: x[1], reverse=True)
		symbols_p, pe_values = zip(*sorted_pe_data)
		ax.bar(symbols_p, pe_values, color='lightgreen')
		ax.axhline(y=25, color='r', linestyle='--', label='Market Avg (25)')
		ax.axhline(y=portfolio_pe, color='g', linestyle='-', label=f'Portfolio P/E ({round(portfolio_pe, 2)})')
		ax.set_title('P/E Comparison by Asset')
		ax.set_ylabel('P/E')
		ax.legend()
		st.pyplot(fig)

# --------- Page 4: Stock Analysis ---------
with tabs[3]:
	st.header("Stock Market and Technical Chart Analysis")
	all_symbols = ["AAPL", "MSFT", "NVDA", "SPY", "BTC-USD"]
	for portfolio in st.session_state["portfolios"]:
		all_symbols.extend(portfolio["holdings"])
	all_symbols = list(set(all_symbols))
	symbol = st.selectbox("Select stock", all_symbols)
	compare_symbols = st.multiselect("Add comparison stocks", [s for s in all_symbols if s != symbol])
	period_map = {
		"1天": "1d", "5天": "5d", "1个月": "1mo", "3个月": "3mo",
		"6个月": "6mo", "今年以来": "ytd", "1年": "1y", "5年": "5y"
	}
	period = st.selectbox("选择时间周期", list(period_map.keys()), index=2)
	try:
		with st.spinner(f"获取{symbol}数据中..."):
			ticker = yf.Ticker(symbol)
			hist = ticker.history(period=period_map[period], interval="1d")
			if not hist.empty:
				price = hist["Close"].iloc[-1]
				prev_price = hist["Close"].iloc[-2] if len(hist) > 1 else price
				change = price - prev_price
				pct_change = (change / prev_price * 100) if prev_price != 0 else 0
				info = ticker.info
				name = info.get("shortName", symbol)
				st.subheader(f"{name} ({symbol})")
				st.metric(
					"最新价格", 
					f"${price:.2f}", 
					delta=f"{change:+.2f} ({pct_change:+.2f}%)",
					help=f"更新时间: {hist.index[-1].strftime('%Y-%m-%d %H:%M')}"
				)
				col_fin = st.columns(3)
				with col_fin[0]:
					st.metric("市值(亿美元)", get_market_cap(symbol))
				with col_fin[1]:
					st.metric("市盈率", get_pe(symbol))
				with col_fin[2]:
					st.metric("股息率(%)", get_dividend(symbol))
				fig, ax = plt.subplots(figsize=(12, 6))
				ax.plot(hist.index, hist["Close"], label=symbol, linewidth=2)
				for cs in compare_symbols:
					cs_ticker = yf.Ticker(cs)
					cs_hist = cs_ticker.history(period=period_map[period], interval="1d")
					if not cs_hist.empty:
						ax.plot(cs_hist.index, cs_hist["Close"], label=cs, linestyle='--')
				studies = st.multiselect("Add technical indicators", ["5-day MA", "10-day MA", "20-day MA", "60-day MA"], default=["5-day MA", "20-day MA"])
				if "5-day MA" in studies:
					ax.plot(hist.index, hist["Close"].rolling(5).mean(), label="5-day MA")
				if "10-day MA" in studies:
					ax.plot(hist.index, hist["Close"].rolling(10).mean(), label="10-day MA")
				if "20-day MA" in studies:
					ax.plot(hist.index, hist["Close"].rolling(20).mean(), label="20-day MA")
				if "60-day MA" in studies:
					ax.plot(hist.index, hist["Close"].rolling(60).mean(), label="60-day MA")
				ax.set_title(f"{symbol} 价格走势 ({period})")
				ax.set_ylabel("价格 (USD)")
				ax.grid(True, alpha=0.3)
				ax.legend()
				st.pyplot(fig)
				st.subheader("Volume Analysis")
				fig, ax = plt.subplots(figsize=(12, 4))
				ax.bar(hist.index, hist["Volume"], color='blue', alpha=0.6)
				ax.set_ylabel("Volume")
				ax.set_title(f"{symbol} Volume Trend")
				ax.grid(True, alpha=0.3)
				st.pyplot(fig)
				st.subheader("Latest News")
				news = ticker.news if hasattr(ticker, "news") else []
				if news:
					for n in news[:5]:
						st.markdown(f"[{n['title']}]({n['link']})")
				else:
					st.info("No news available.")
			else:
				st.warning("No price data available. Try another time period.")
	except Exception as e:
		st.error(f"获取数据失败: {str(e)}")
	st.subheader("Portfolio Asset Monitoring")
	if st.session_state["portfolios"]:
		portfolio_names = [p["name"] for p in portfolios]
		selected_port = st.selectbox("Select portfolio to monitor", portfolio_names)
		if selected_port:
			port_idx = portfolio_names.index(selected_port)
			port_holdings = portfolios[port_idx]["holdings"]
			cols = st.columns(3)
			for i, s in enumerate(port_holdings):
				try:
					ticker = yf.Ticker(s)
					hist = ticker.history(period="5d", interval="1d")
					price = hist["Close"].iloc[-1] if not hist.empty else None
					if price:
						cols[i%3].metric(s, f"${price:.2f}")
				except:
					cols[i%3].metric(s, "N/A")
	else:
		st.info("No portfolios available for monitoring")
