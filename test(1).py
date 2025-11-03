import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import yfinance as yf
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import requests  # 新增：用于调用真实API

# Set font for international support
plt.rcParams["font.family"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
plt.rcParams['axes.unicode_minus'] = False  # Solve the problem of negative sign display

# Configure real news API (use your API Key)
WORLD_NEWS_API_KEY = "6d6d5f5d55b64eab94814259cb0a0841"
WORLD_NEWS_API_URL = "https://api.worldnewsapi.com/search-news"


class InvestmentPortfolioApp:
    def __init__(self, root):
        self.root = root
    self.root.title("Investment Portfolio Management System")
        self.root.geometry("1200x800")
        
    # Data storage
    self.portfolios = {}  # All portfolios
    self.current_portfolio = None  # Currently selected portfolio
    self.your_picks = []  # Selected assets
    self.news_data = []  # News data from real API (replaces mock)
    self.current_news_page = 1
    self.news_per_page = 12
    self.selected_stock = "AAPL"  # Default selected stock
        
    # Create notebook container
    self.notebook = ttk.Notebook(root)
    self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Create four pages
    self.page1 = ttk.Frame(self.notebook)
    self.page2 = ttk.Frame(self.notebook)
    self.page3 = ttk.Frame(self.notebook)
    self.page4 = ttk.Frame(self.notebook)

    # Add pages to notebook
    self.notebook.add(self.page1, text="Create Portfolio")
    self.notebook.add(self.page2, text="News Aggregation")
    self.notebook.add(self.page3, text="Portfolio Analysis")
    self.notebook.add(self.page4, text="Stock Analysis")
        
    # Initialize each page
    self.init_page1()
    self.init_page2()
    self.init_page3()
    self.init_page4()

    # Bind tab change event (auto-load news on news tab)
    self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def on_tab_changed(self, event):
        """Update data on tab change (load real news on news tab)"""
        current_tab = self.notebook.select()
        if current_tab == str(self.page2):
            self.load_real_news()  # 切换到新闻页时加载真实新闻
        elif current_tab == str(self.page3):
            self.update_portfolio_analysis()
        elif current_tab == str(self.page4):
            self.update_stock_chart()
    
    # -------------------------- Page 1: Create Portfolio (no logic change) --------------------------
    def init_page1(self):
        # 创建左右分栏
        left_frame = ttk.Frame(self.page1, width=600)
        right_frame = ttk.Frame(self.page1, width=600)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧：手动创建投资组合
    manual_frame = ttk.LabelFrame(left_frame, text="Manual Create Portfolio")
        manual_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 搜索框
        search_frame = ttk.Frame(manual_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
    ttk.Label(search_frame, text="Search Stock, Crypto or ETF:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    ttk.Button(search_frame, text="Add", command=self.add_from_search).pack(side=tk.LEFT, padx=5)
        
        # 热门股票快捷入口
    ttk.Label(manual_frame, text="Popular Stocks:").pack(anchor=tk.W, padx=5, pady=5)
        popular_frame = ttk.Frame(manual_frame)
        popular_frame.pack(fill=tk.X, padx=5, pady=5)
        
        popular_stocks = [
            ("AAPL", "苹果"), ("NVDA", "英伟达"), 
            ("MSFT", "微软"), ("SPY", "标普500ETF"),
            ("GOOGL", "谷歌"), ("AMZN", "亚马逊"),
            ("TSLA", "特斯拉"), ("BTC-USD", "比特币")
        ]
        
        for symbol, name in popular_stocks:
            ttk.Button(
                popular_frame, 
                text=f"{symbol} ({name})",
                command=lambda s=symbol: self.add_popular_stock(s)
            ).pack(side=tk.LEFT, padx=2, pady=2)
        
        # Your Picks区域
    picks_frame = ttk.LabelFrame(manual_frame, text="Your Picks")
        picks_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=10)
        
        self.picks_listbox = tk.Listbox(picks_frame)
        self.picks_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(picks_frame, orient=tk.VERTICAL, command=self.picks_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        self.picks_listbox.config(yscrollcommand=scrollbar.set)
        
        # 移除选中项按钮
        ttk.Button(
            picks_frame, 
            text="Remove Selected", 
            command=self.remove_selected_pick
        ).pack(side=tk.BOTTOM, pady=5)
        
        # 创建投资组合按钮
        ttk.Button(
            manual_frame, 
            text="Create Portfolio", 
            command=self.create_portfolio
        ).pack(pady=10)
        
        # 右侧：连接经纪商同步投资组合
    broker_frame = ttk.LabelFrame(right_frame, text="Sync Portfolio from Broker")
        broker_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    ttk.Label(broker_frame, text="Select Broker:").pack(anchor=tk.W, padx=5, pady=5)
        
        brokers = [
            "ally", "robinhood", "Fidelity", "Interactive Brokers",
            "Vanguard", "Bank of America", "Charles Schwab"
        ]
        
        self.broker_var = tk.StringVar()
        broker_combo = ttk.Combobox(broker_frame, textvariable=self.broker_var, values=brokers, state="readonly")
        broker_combo.pack(fill=tk.X, padx=5, pady=5)
        if brokers:
            broker_combo.current(0)
        
        # 同步按钮
        ttk.Button(
            broker_frame, 
            text="Sync Portfolio", 
            command=self.sync_portfolio
        ).pack(fill=tk.X, padx=5, pady=5)
        
        # 上传CSV按钮
        ttk.Button(
            broker_frame, 
            text="Upload CSV", 
            command=self.upload_csv
        ).pack(fill=tk.X, padx=5, pady=5)
        
        # 更多经纪商链接
        more_brokers_frame = ttk.Frame(broker_frame)
        more_brokers_frame.pack(fill=tk.X, padx=5, pady=20)
        
    ttk.Label(more_brokers_frame, text="Can't find your broker?").pack(side=tk.LEFT)
        ttk.Button(
            more_brokers_frame, 
            text="More Brokers", 
            command=self.show_more_brokers,
            style="Link.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        # 创建链接样式
        style = ttk.Style()
    style.configure("Link.TButton", foreground="blue", background="transparent", borderwidth=0)
    
    def add_from_search(self):
        """Add asset from search box"""
        symbol = self.search_entry.get().strip().upper()
        if symbol and symbol not in self.your_picks:
            try:
                # 尝试获取股票信息验证有效性
                stock = yf.Ticker(symbol)
                info = stock.info
                name = info.get('shortName', symbol)
                self.your_picks.append(symbol)
                self.picks_listbox.insert(tk.END, f"{symbol} - {name}")
                self.search_entry.delete(0, tk.END)
            except:
                messagebox.showerror("Error", f"Asset not found: {symbol}")
    
    def add_popular_stock(self, symbol):
        """Add popular stock"""
        if symbol not in self.your_picks:
            try:
                stock = yf.Ticker(symbol)
                info = stock.info
                name = info.get('shortName', symbol)
                self.your_picks.append(symbol)
                self.picks_listbox.insert(tk.END, f"{symbol} - {name}")
            except:
                self.your_picks.append(symbol)
                self.picks_listbox.insert(tk.END, symbol)
    
    def remove_selected_pick(self):
        """Remove selected asset"""
        selected_indices = self.picks_listbox.curselection()
        if not selected_indices:
            return
            
        # 从后往前删除，避免索引变化问题
        for i in sorted(selected_indices, reverse=True):
            self.picks_listbox.delete(i)
            del self.your_picks[i]
    
    def create_portfolio(self):
        """Create portfolio"""
        if not self.your_picks:
            messagebox.showwarning("Warning", "Please add at least one asset first")
            return
            
        # 创建一个简单的对话框获取投资组合名称
        dialog = tk.Toplevel(self.root)
    dialog.title("Create Portfolio")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
    ttk.Label(dialog, text="Enter portfolio name:").pack(padx=10, pady=10)
        name_entry = ttk.Entry(dialog)
        name_entry.pack(fill=tk.X, padx=10, pady=5)
    name_entry.insert(0, f"My Portfolio {len(self.portfolios) + 1}")
        
        def save_portfolio():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Warning", "Please enter portfolio name")
                return
                
            # 为每个标的分配随机比例（总和为100%）
            weights = np.random.random(len(self.your_picks))
            weights = weights / weights.sum() * 100
            
            portfolio = {
                "name": name,
                "holdings": {
                    symbol: {"weight": round(weight, 2)} 
                    for symbol, weight in zip(self.your_picks, weights)
                }
            }
            
            self.portfolios[name] = portfolio
            self.current_portfolio = name
            
            # 清空选择
            self.your_picks.clear()
            self.picks_listbox.delete(0, tk.END)
            
            messagebox.showinfo("Success", f"Portfolio '{name}' created successfully")
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
    ttk.Button(button_frame, text="Create", command=save_portfolio).pack(side=tk.RIGHT, padx=5)
    ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        name_entry.focus()
        self.root.wait_window(dialog)
    
    def sync_portfolio(self):
        """Sync broker portfolio (mock)"""
        broker = self.broker_var.get()
        if not broker:
            messagebox.showwarning("Warning", "Please select a broker")
            return
            
    messagebox.showinfo("Sync", f"Syncing portfolio from {broker}...\n(Mock)")
        
        # 模拟同步结果
        sample_portfolio = {
            "name": f"{broker} 同步组合",
            "holdings": {
                "AAPL": {"weight": 30},
                "MSFT": {"weight": 25},
                "GOOGL": {"weight": 20},
                "AMZN": {"weight": 15},
                "TSLA": {"weight": 10}
            }
        }
        
    self.portfolios[sample_portfolio["name"]] = sample_portfolio
    self.current_portfolio = sample_portfolio["name"]
    messagebox.showinfo("Success", f"Portfolio from {broker} synced")
    
    def upload_csv(self):
        """Upload CSV file (mock)"""
        file_path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV file", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            # 模拟CSV导入
            messagebox.showinfo("Import", f"Portfolio data imported from {file_path}\n(Mock)")
            
            # 创建一个示例投资组合
            sample_portfolio = {
                "name": "CSV导入组合",
                "holdings": {
                    "NVDA": {"weight": 40},
                    "SPY": {"weight": 30},
                    "BTC-USD": {"weight": 20},
                    "MSFT": {"weight": 10}
                }
            }
            
            self.portfolios[sample_portfolio["name"]] = sample_portfolio
            self.current_portfolio = sample_portfolio["name"]
    
    def show_more_brokers(self):
        """Show more brokers (mock)"""
        messagebox.showinfo("More Brokers", "Loading more brokers...\n(Mock)")
    
    # -------------------------- 第二页：新闻聚合（核心修改：真实API调用） --------------------------
    def init_page2(self):
        # 顶部按钮区域
        top_frame = ttk.Frame(self.page2)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(top_frame, text="Add Portfolio", command=self.add_portfolio).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Add Holdings", command=self.add_holdings).pack(side=tk.RIGHT, padx=5)
        
        # 搜索和筛选区域
        search_frame = ttk.Frame(self.page2)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="搜索新闻:").pack(side=tk.LEFT, padx=5)
        self.news_search_entry = ttk.Entry(search_frame)
        self.news_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_news).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(search_frame, text="筛选:").pack(side=tk.LEFT, padx=5)
        self.news_filter = ttk.Combobox(
            search_frame, 
            values=["All Holdings", "Stocks", "ETFs", "Cryptocurrencies"],
            state="readonly"
        )
        self.news_filter.current(0)
        self.news_filter.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="应用", command=self.filter_news).pack(side=tk.LEFT, padx=5)
        
        # 新闻列表和详情区域
        content_frame = ttk.Frame(self.page2)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧新闻列表
        self.news_listbox = tk.Listbox(content_frame, width=50, height=25)
        self.news_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.news_listbox.bind('<<ListboxSelect>>', self.show_news_details)
        
        scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=self.news_listbox.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y, pady=5)
        self.news_listbox.config(yscrollcommand=scrollbar.set)
        
        # 右侧新闻详情
        self.news_details_frame = ttk.LabelFrame(content_frame, text="新闻详情")
        self.news_details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 字体大小调整
        font_frame = ttk.Frame(self.news_details_frame)
        font_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(font_frame, text="A+", command=lambda: self.change_font_size(1)).pack(side=tk.RIGHT, padx=5)
        ttk.Button(font_frame, text="A-", command=lambda: self.change_font_size(-1)).pack(side=tk.RIGHT)
        
        # 新闻内容
        self.news_text = scrolledtext.ScrolledText(
            self.news_details_frame, 
            wrap=tk.WORD,
            font=("SimHei", 12)
        )
        self.news_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.news_text.config(state=tk.DISABLED)
        
        # 继续阅读按钮（跳转到新闻原链接）
        self.continue_reading_btn = ttk.Button(
            self.news_details_frame, 
            text="Continue Reading (跳转原链接)", 
            command=self.open_news_link
        )
        self.continue_reading_btn.pack(pady=10)
        self.continue_reading_btn.pack_forget()  # 初始隐藏
        
        # 分页控制
        pagination_frame = ttk.Frame(self.page2)
        pagination_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.page_info_label = ttk.Label(pagination_frame, text="")
        self.page_info_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(pagination_frame, text="上一页", command=self.prev_news_page).pack(side=tk.RIGHT, padx=5)
        ttk.Button(pagination_frame, text="下一页", command=self.next_news_page).pack(side=tk.RIGHT, padx=5)
        
        # 初始化时加载真实新闻
        self.load_real_news()

    def load_real_news(self):
        """调用worldnewsapi获取真实新闻（核心修改）"""
        # 清空现有新闻数据
        self.news_data.clear()
        self.news_listbox.delete(0, tk.END)
        
        # 1. 确定搜索关键词（优先用当前投资组合的标的，无则用热门标的）
        if self.current_portfolio and self.portfolios.get(self.current_portfolio):
            # 从当前投资组合提取标的（如AAPL、NVDA）
            symbols = list(self.portfolios[self.current_portfolio]["holdings"].keys())
        else:
            # 无投资组合时，用热门标的作为默认关键词
            symbols = ["AAPL", "NVDA", "MSFT", "SPY", "BTC-USD"]
        
        # 处理加密货币标的格式（如BTC-USD → Bitcoin）
        keyword_map = {
            "BTC-USD": "Bitcoin",
            "ETH-USD": "Ethereum"
        }
        # 生成关键词（用OR连接多个标的，扩大搜索范围）
        keywords = " OR ".join([keyword_map.get(s, s) for s in symbols])
        
        # 2. 构造API请求参数（参考worldnewsapi文档）
        params = {
            "api-key": WORLD_NEWS_API_KEY,
            "q": keywords,  # 搜索关键词（投资组合标的）
            "language": "en",  # 财经新闻以英文为主
            "sort": "date",  # 按日期排序（最新优先）
            "page": self.current_news_page,  # 当前页码
            "page-size": self.news_per_page,  # 每页新闻数量
            "earliest-publish-date": (datetime.now() - timedelta(days=30)).isoformat()  # 只获取30天内的新闻
        }
        
        try:
            # 3. 发送API请求
            response = requests.get(WORLD_NEWS_API_URL, params=params, timeout=10)
            response.raise_for_status()  # 触发HTTP错误（如401密钥无效、429请求超限）
            api_data = response.json()
            
            # 4. 解析API响应，适配原有新闻数据结构
            if api_data.get("news"):
                for idx, news_item in enumerate(api_data["news"]):
                    # 提取核心字段（标题、日期、内容、链接、关联标的）
                    related_symbol = self._match_news_to_symbol(news_item["title"], symbols)
                    self.news_data.append({
                        "id": idx,
                        "symbol": related_symbol,  # 匹配的投资组合标的
                        "date": news_item["publish-date"].split("T")[0],  # 格式：2024-05-20
                        "title": news_item["title"],
                        "content": news_item.get("text", "无详细内容"),  # 新闻摘要
                        "full_content": news_item.get("text", "无详细内容"),  # 真实新闻无"更多内容"，复用摘要
                        "url": news_item.get("url", "")  # 新闻原链接（用于跳转）
                    })
            
            # 5. 更新新闻列表和分页信息
            self.filtered_news = self.news_data
            self.update_news_list()
            
            # 提示用户新闻加载结果
            total_news = api_data.get("total-results", 0)
            messagebox.showinfo("新闻加载成功", f"共获取到 {total_news} 条相关新闻（30天内）")
        
        except requests.exceptions.HTTPError as e:
            # 处理HTTP错误（如密钥无效、请求超限）
            error_msg = f"API请求失败: {e}\n"
            if response.status_code == 401:
                error_msg += "可能原因：API密钥无效或已过期"
            elif response.status_code == 429:
                error_msg += "可能原因：API请求次数超限（请检查worldnewsapi账户配额）"
            messagebox.showerror("新闻加载失败", error_msg)
        except requests.exceptions.Timeout:
            messagebox.showerror("新闻加载失败", "API请求超时，请检查网络连接")
        except Exception as e:
            messagebox.showerror("新闻加载失败", f"未知错误: {str(e)}")

    def _match_news_to_symbol(self, news_title, symbols):
        """辅助方法：将新闻标题与投资组合标的匹配（如标题含AAPL则关联AAPL）"""
        title_lower = news_title.lower()
        for symbol in symbols:
            # 处理加密货币（如BTC-USD → BTC）
            symbol_simple = symbol.replace("-USD", "")
            if symbol.lower() in title_lower or symbol_simple.lower() in title_lower:
                return symbol
        return "OTHER"  # 无匹配标的时标记为OTHER

    def open_news_link(self):
        """打开新闻原链接（替换原"继续阅读"功能，真实新闻需跳转原网站）"""
        selected_indices = self.news_listbox.curselection()
        if not selected_indices:
            return
        
        idx = selected_indices[0]
        start_idx = (self.current_news_page - 1) * self.news_per_page
        news = self.filtered_news[start_idx + idx]
        
        if news.get("url"):
            import webbrowser
            webbrowser.open(news["url"])  # 调用默认浏览器打开链接
        else:
            messagebox.showwarning("无链接", "该新闻无可用原链接")

    def update_news_list(self):
        """更新新闻列表（无修改，适配真实数据）"""
        self.news_listbox.delete(0, tk.END)
        
        total_news = len(self.filtered_news)
        start_idx = (self.current_news_page - 1) * self.news_per_page
        end_idx = min(start_idx + self.news_per_page, total_news)
        
        # 更新页面信息
        self.page_info_label.config(text=f"{start_idx + 1} - {end_idx} of {total_news}")
        
        # 添加当前页的新闻
        for news in self.filtered_news[start_idx:end_idx]:
            self.news_listbox.insert(tk.END, f"{news['date']} | {news['symbol']} | {news['title'][:50]}...")
    
    def show_news_details(self, event):
        """显示新闻详情（适配真实数据，添加链接跳转按钮）"""
        selected_indices = self.news_listbox.curselection()
        if not selected_indices:
            return
            
        idx = selected_indices[0]
        start_idx = (self.current_news_page - 1) * self.news_per_page
        news = self.filtered_news[start_idx + idx]
        
        # 显示新闻详情
        self.news_text.config(state=tk.NORMAL)
        self.news_text.delete(1.0, tk.END)
        self.news_text.insert(tk.END, f"{news['title']}\n\n")
        self.news_text.insert(tk.END, f"日期: {news['date']} | 关联标的: {news['symbol']}\n\n")
        self.news_text.insert(tk.END, f"{news['content'][:500]}..." if len(news['content']) > 500 else news['content'])
        self.news_text.config(state=tk.DISABLED)
        
        # 显示"跳转原链接"按钮（如果有链接）
        if news.get("url"):
            self.continue_reading_btn.pack(pady=10)
        else:
            self.continue_reading_btn.pack_forget()
    
    def change_font_size(self, delta):
        """调整字体大小（无修改）"""
        current_font = self.news_text["font"].split()
        current_size = int(current_font[-1])
        new_size = max(8, min(24, current_size + delta))  # 限制在8-24之间
        
        new_font = " ".join(current_font[:-1] + [str(new_size)])
        self.news_text.configure(font=new_font)
    
    def search_news(self):
        """搜索新闻（适配真实数据，按关键词过滤）"""
        keyword = self.news_search_entry.get().strip().lower()
        if not keyword:
            self.filtered_news = self.news_data
        else:
            self.filtered_news = [
                news for news in self.news_data 
                if keyword in news["title"].lower() or 
                   keyword in news["content"].lower() or
                   keyword in news["symbol"].lower()
            ]
        
        self.current_news_page = 1
        self.update_news_list()
    
    def filter_news(self):
        """筛选新闻（按标的类型：股票/ETF/加密货币，无修改）"""
        filter_type = self.news_filter.get()
        
        if filter_type == "All Holdings":
            self.filtered_news = self.news_data
        elif filter_type == "Stocks":
            # 筛选股票（排除ETF和加密货币）
            self.filtered_news = [
                news for news in self.news_data 
                if "-" not in news["symbol"] and news["symbol"] not in ["SPY"]
            ]
        elif filter_type == "ETFs":
            self.filtered_news = [news for news in self.news_data if news["symbol"] in ["SPY"]]
        elif filter_type == "Cryptocurrencies":
            self.filtered_news = [news for news in self.news_data if "-USD" in news["symbol"]]
        
        self.current_news_page = 1
        self.update_news_list()
    
    def prev_news_page(self):
        """Previous page (no change)"""
        if self.current_news_page > 1:
            self.current_news_page -= 1
            self.load_real_news()  # 分页时重新调用API获取对应页数据
    
    def next_news_page(self):
        """Next page (no change)"""
        # 直接调用API加载下一页（worldnewsapi支持分页）
        self.current_news_page += 1
        self.load_real_news()
    
    def add_portfolio(self):
        """Add new portfolio (reuse page 1 function)"""
        self.notebook.select(self.page1)
        messagebox.showinfo("Info", "Please create a new portfolio on page 1.")
    
    def add_holdings(self):
        """Add new holding (reuse page 1 function)"""
        self.notebook.select(self.page1)
        messagebox.showinfo("Info", "Please add new holdings on page 1.")
    
    # -------------------------- Page 3: Portfolio Analysis (no change) --------------------------
    def init_page3(self):
        # 顶部选择投资组合
        top_frame = ttk.Frame(self.page3)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
    ttk.Label(top_frame, text="Select Portfolio:").pack(side=tk.LEFT, padx=5)
        self.portfolio_combobox = ttk.Combobox(top_frame, state="readonly")
        self.portfolio_combobox.pack(side=tk.LEFT, padx=5)
        self.portfolio_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_portfolio_analysis())
        
        # 创建四个分析区域的标签页
        self.analysis_notebook = ttk.Notebook(self.page3)
        self.analysis_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 资产配置分析
        self.asset_allocation_frame = ttk.Frame(self.analysis_notebook)
    self.analysis_notebook.add(self.asset_allocation_frame, text="Asset Allocation Analysis")
        
        # 持仓分布分析
        self.holdings_distribution_frame = ttk.Frame(self.analysis_notebook)
    self.analysis_notebook.add(self.holdings_distribution_frame, text="Holdings Distribution Analysis")
        
        # 波动率分析
        self.volatility_frame = ttk.Frame(self.analysis_notebook)
    self.analysis_notebook.add(self.volatility_frame, text="Volatility Analysis")
        
        # 市盈率分析
        self.pe_ratio_frame = ttk.Frame(self.analysis_notebook)
    self.analysis_notebook.add(self.pe_ratio_frame, text="P/E Ratio Analysis")
        
        # 初始化资产配置分析的标签
        self.asset_tabs = ttk.Notebook(self.asset_allocation_frame)
        self.asset_tabs.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.asset_type_frame = ttk.Frame(self.asset_tabs)
        self.top_stocks_frame = ttk.Frame(self.asset_tabs)
        self.geo_allocation_frame = ttk.Frame(self.asset_tabs)
        
    self.asset_tabs.add(self.asset_type_frame, text="Asset Type")
    self.asset_tabs.add(self.top_stocks_frame, text="Top Stocks")
    self.asset_tabs.add(self.geo_allocation_frame, text="Geographic Allocation")
        
        # 初始化持仓分布分析的筛选器
        self.holdings_filter_frame = ttk.Frame(self.holdings_distribution_frame)
        self.holdings_filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
    ttk.Label(self.holdings_filter_frame, text="Filter by:").pack(side=tk.LEFT, padx=5)
        self.holdings_filter = ttk.Combobox(
            self.holdings_filter_frame,
            values=["By Sector", "By Market Cap", "By Dividend", "By Beta", "By P/E Ratio"],
            state="readonly"
        )
        self.holdings_filter.current(0)
        self.holdings_filter.pack(side=tk.LEFT, padx=5)
        self.holdings_filter.bind("<<ComboboxSelected>>", lambda e: self.update_holdings_distribution())
    
    def update_portfolio_combobox(self):
    """Update portfolio dropdown"""
        portfolio_names = list(self.portfolios.keys())
        self.portfolio_combobox['values'] = portfolio_names
        if portfolio_names and not self.portfolio_combobox.get() and self.current_portfolio:
            self.portfolio_combobox.set(self.current_portfolio)
    
    def update_portfolio_analysis(self):
    """Update portfolio analysis data"""
        self.update_portfolio_combobox()
        
        selected_portfolio = self.portfolio_combobox.get()
        if not selected_portfolio or selected_portfolio not in self.portfolios:
            return
            
        self.current_portfolio = selected_portfolio
        portfolio = self.portfolios[selected_portfolio]
        
        # 更新各分析页面
        self.update_asset_allocation(portfolio)
        self.update_holdings_distribution(portfolio)
        self.update_volatility_analysis(portfolio)
        self.update_pe_analysis(portfolio)
    
    def update_asset_allocation(self, portfolio):
    """Update asset allocation analysis"""
        # 清空现有图表
        for widget in self.asset_type_frame.winfo_children():
            widget.destroy()
        for widget in self.top_stocks_frame.winfo_children():
            widget.destroy()
        for widget in self.geo_allocation_frame.winfo_children():
            widget.destroy()
        
        # 资产类型分析
    asset_types = {"Stock": 0, "ETF": 0, "Crypto": 0, "Fund": 0, "Cash": 0}
        
        for symbol, data in portfolio["holdings"].items():
            weight = data["weight"]
            if "-USD" in symbol:  # Crypto
                asset_types["Crypto"] += weight
            elif symbol in ["SPY", "QQQ", "DIA"]:  # ETF
                asset_types["ETF"] += weight
            else:  # Stock
                asset_types["Stock"] += weight
        
        # 过滤掉0值
        asset_types = {k: v for k, v in asset_types.items() if v > 0}
        
        # 创建饼图
        fig = Figure(figsize=(6, 5), dpi=100)
        ax = fig.add_subplot(111)
        ax.pie(asset_types.values(), labels=asset_types.keys(), autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
    ax.set_title('Asset Type Distribution')
        
        canvas = FigureCanvasTkAgg(fig, master=self.asset_type_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 顶级股票分析
        top_stocks = {k: v["weight"] for k, v in portfolio["holdings"].items() if "-USD" not in k and k not in ["SPY", "QQQ", "DIA"]}
        top_stocks = dict(sorted(top_stocks.items(), key=lambda x: x[1], reverse=True)[:5])
        
        fig = Figure(figsize=(6, 5), dpi=100)
        ax = fig.add_subplot(111)
        ax.bar(top_stocks.keys(), top_stocks.values())
    ax.set_title('Top Stocks Weight')
    ax.set_ylabel('Weight (%)')
        
        canvas = FigureCanvasTkAgg(fig, master=self.top_stocks_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 地域配置分析（模拟数据）
    regions = {"USA": 0, "Europe": 0, "Asia": 0, "Other": 0}
    us_stocks = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "SPY"]
        
        for symbol, data in portfolio["holdings"].items():
            weight = data["weight"]
            if symbol in us_stocks:
                regions["USA"] += weight
            else:
                # Randomly assign other regions
                region = random.choice(["Europe", "Asia", "Other"])
                regions[region] += weight
        
        fig = Figure(figsize=(6, 5), dpi=100)
        ax = fig.add_subplot(111)
        ax.pie(regions.values(), labels=regions.keys(), autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
    ax.set_title('Geographic Allocation Distribution')
        
        canvas = FigureCanvasTkAgg(fig, master=self.geo_allocation_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_holdings_distribution(self, portfolio=None):
        """更新持仓分布分析"""
        if not portfolio:
            selected_portfolio = self.portfolio_combobox.get()
            if not selected_portfolio or selected_portfolio not in self.portfolios:
                return
            portfolio = self.portfolios[selected_portfolio]
        
        # 清空现有图表
        for widget in self.holdings_distribution_frame.winfo_children():
            if widget != self.holdings_filter_frame:
                widget.destroy()
        
        filter_type = self.holdings_filter.get()
        
        # 根据筛选类型生成数据
        if filter_type == "行业（By Sector）":
            sectors = {}
            for symbol, data in portfolio["holdings"].items():
                # 模拟行业数据
                if symbol in ["AAPL", "MSFT", "NVDA", "GOOGL", "AMD"]:
                    sector = "科技"
                elif symbol in ["AMZN", "TSLA"]:
                    sector = "消费"
                elif "-USD" in symbol:
                    sector = "加密货币"
                else:
                    sector = "综合"
                
                if sector not in sectors:
                    sectors[sector] = 0
                sectors[sector] += data["weight"]
            
            # 创建饼图
            fig = Figure(figsize=(8, 6), dpi=100)
            ax = fig.add_subplot(111)
            ax.pie(sectors.values(), labels=sectors.keys(), autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            ax.set_title('按行业分布')
            
            canvas = FigureCanvasTkAgg(fig, master=self.holdings_distribution_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # 列出主要持仓
            ttk.Label(self.holdings_distribution_frame, text="主要持仓:").pack(anchor=tk.W, padx=5, pady=5)
            holdings_frame = ttk.Frame(self.holdings_distribution_frame)
            holdings_frame.pack(fill=tk.X, padx=5, pady=5)
            
            for i, (symbol, data) in enumerate(portfolio["holdings"].items()):
                ttk.Label(holdings_frame, text=f"{symbol}: {data['weight']}%").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
        
        elif filter_type == "市值（By Market Cap）":
            # 模拟市值数据
            market_caps = {"大盘": 0, "中盘": 0, "小盘": 0}
            large_cap = ["AAPL", "MSFT", "GOOGL", "AMZN", "SPY"]
            
            for symbol, data in portfolio["holdings"].items():
                if symbol in large_cap:
                    market_caps["大盘"] += data["weight"]
                elif symbol in ["NVDA", "TSLA"]:
                    market_caps["中盘"] += data["weight"]
                else:
                    market_caps["小盘"] += data["weight"]
            
            fig = Figure(figsize=(8, 6), dpi=100)
            ax = fig.add_subplot(111)
            ax.bar(market_caps.keys(), market_caps.values())
            ax.set_title('按市值分布')
            ax.set_ylabel('占比 (%)')
            
            canvas = FigureCanvasTkAgg(fig, master=self.holdings_distribution_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        else:  # 其他筛选类型，简化处理
            fig = Figure(figsize=(8, 6), dpi=100)
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, f"{filter_type} 分析", ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title(filter_type)
            
            canvas = FigureCanvasTkAgg(fig, master=self.holdings_distribution_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_volatility_analysis(self, portfolio):
        """更新波动率分析"""
        # 清空现有内容
        for widget in self.volatility_frame.winfo_children():
            widget.destroy()
        
        # 模拟贝塔值数据
        beta_values = {}
        for symbol in portfolio["holdings"].keys():
            if symbol == "NVDA":
                beta = 2.27
            elif "-USD" in symbol:
                beta = 1.39
            elif symbol in ["AAPL", "MSFT"]:
                beta = round(random.uniform(1.1, 1.3), 2)
            else:
                beta = round(random.uniform(0.8, 1.5), 2)
            beta_values[symbol] = beta
        
        # 计算组合贝塔值（加权平均）
        portfolio_beta = 0
        for symbol, data in portfolio["holdings"].items():
            portfolio_beta += beta_values[symbol] * (data["weight"] / 100)
        portfolio_beta = round(portfolio_beta, 2)
        
        # 平均组合贝塔值（模拟）
        avg_beta = 1.0
        
        # 显示组合贝塔值
        beta_frame = ttk.Frame(self.volatility_frame)
        beta_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(beta_frame, text="组合贝塔值:").pack(side=tk.LEFT, padx=5)
        ttk.Label(
            beta_frame, 
            text=f"{portfolio_beta}", 
            font=("SimHei", 14, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(beta_frame, text="平均组合贝塔值:").pack(side=tk.LEFT, padx=20)
        ttk.Label(
            beta_frame, 
            text=f"{avg_beta}", 
            font=("SimHei", 12)
        ).pack(side=tk.LEFT, padx=5)
        
        # 风险等级
        risk_level = "低风险" if portfolio_beta < 0.8 else "中风险" if portfolio_beta < 1.2 else "中高风险"
        ttk.Label(
            self.volatility_frame, 
            text=f"风险等级: {risk_level}", 
            font=("SimHei", 12)
        ).pack(anchor=tk.W, padx=5, pady=5)
        
        # 风险最高的股票
        ttk.Label(
            self.volatility_frame, 
            text="组合内风险最高的股票及其贝塔值:", 
            font=("SimHei", 12, "bold")
        ).pack(anchor=tk.W, padx=5, pady=10)
        
        # 排序并显示
        sorted_betas = sorted(beta_values.items(), key=lambda x: x[1], reverse=True)
        
        for symbol, beta in sorted_betas[:5]:  # 显示前5名
            frame = ttk.Frame(self.volatility_frame)
            frame.pack(fill=tk.X, padx=15, pady=2)
            
            ttk.Label(frame, text=symbol, width=10).pack(side=tk.LEFT)
            ttk.Label(frame, text=f"贝塔值: {beta}").pack(side=tk.LEFT)
    
    def update_pe_analysis(self, portfolio):
        """更新市盈率分析"""
        # 清空现有内容
        for widget in self.pe_ratio_frame.winfo_children():
            widget.destroy()
        
        # 模拟市盈率数据
        pe_values = {}
        for symbol in portfolio["holdings"].keys():
            if symbol == "NVDA":
                pe = 53.01
            elif symbol == "AAPL":
                pe = 39.95
            elif symbol == "MSFT":
                pe = 35.78
            elif "-USD" in symbol:
                pe = "N/A"  # 加密货币没有市盈率
            else:
                pe = round(random.uniform(15, 45), 2)
            pe_values[symbol] = pe
        
        # 计算组合市盈率（加权平均，忽略N/A值）
        portfolio_pe = 0
        total_weight = 0
        
        for symbol, data in portfolio["holdings"].items():
            pe = pe_values[symbol]
            if pe != "N/A":
                portfolio_pe += pe * (data["weight"] / 100)
                total_weight += data["weight"]
        
        if total_weight > 0:
            portfolio_pe = round(portfolio_pe / (total_weight / 100), 1)
        else:
            portfolio_pe = "N/A"
        
        # 平均组合市盈率（模拟）
        avg_pe = 25.5
        
        # 显示组合市盈率
        pe_frame = ttk.Frame(self.pe_ratio_frame)
        pe_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(pe_frame, text="组合市盈率:").pack(side=tk.LEFT, padx=5)
        ttk.Label(
            pe_frame, 
            text=f"{portfolio_pe}", 
            font=("SimHei", 14, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(pe_frame, text="平均组合市盈率:").pack(side=tk.LEFT, padx=20)
        ttk.Label(
            pe_frame, 
            text=f"{avg_pe}", 
            font=("SimHei", 12)
        ).pack(side=tk.LEFT, padx=5)
        
        # 市盈率最高的股票
        ttk.Label(
            self.pe_ratio_frame, 
            text="组合内市盈率最高的股票:", 
            font=("SimHei", 12, "bold")
        ).pack(anchor=tk.W, padx=5, pady=10)
        
        # 排序并显示（只包含有市盈率的）
        numeric_pes = [(s, pe) for s, pe in pe_values.items() if pe != "N/A"]
        sorted_pes = sorted(numeric_pes, key=lambda x: x[1], reverse=True)
        
        for symbol, pe in sorted_pes[:5]:  # 显示前5名
            frame = ttk.Frame(self.pe_ratio_frame)
            frame.pack(fill=tk.X, padx=15, pady=2)
            
            ttk.Label(frame, text=symbol, width=10).pack(side=tk.LEFT)
            ttk.Label(frame, text=f"市盈率: {pe}").pack(side=tk.LEFT)
        
        # 标记没有市盈率的资产
        non_pe = [s for s, pe in pe_values.items() if pe == "N/A"]
        if non_pe:
            ttk.Label(
                self.pe_ratio_frame, 
                text="无市盈率数据的资产: " + ", ".join(non_pe), 
                font=("SimHei", 10)
            ).pack(anchor=tk.W, padx=15, pady=10)
    
    # -------------------------- 第四页：个股分析（无修改） --------------------------
    def init_page4(self):
        # 顶部股票选择和时间周期选择
        top_frame = ttk.Frame(self.page4)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 股票选择
        ttk.Label(top_frame, text="选择股票:").pack(side=tk.LEFT, padx=5)
        self.stock_combobox = ttk.Combobox(top_frame, state="readonly")
        self.stock_combobox.pack(side=tk.LEFT, padx=5)
        self.stock_combobox.bind("<<ComboboxSelected>>", lambda e: self.change_selected_stock())
        
        # 时间周期选择
        ttk.Label(top_frame, text="时间周期:").pack(side=tk.LEFT, padx=15)
        self.time_period = ttk.Combobox(
            top_frame,
            values=["1D", "5D", "1M", "3M", "6M", "YTD", "1Y", "5Y"],
            state="readonly"
        )
        self.time_period.current(6)  # 默认1年
        self.time_period.pack(side=tk.LEFT, padx=5)
        self.time_period.bind("<<ComboboxSelected>>", lambda e: self.update_stock_chart())
        
        # 技术指标按钮
        ttk.Button(top_frame, text="Studies", command=self.show_technical_indicators).pack(side=tk.LEFT, padx=15)
        
        # 对比按钮
        ttk.Button(top_frame, text="+ Compare", command=self.add_comparison).pack(side=tk.LEFT, padx=5)
        
        # 事件按钮
        ttk.Button(top_frame, text="Events", command=self.show_events).pack(side=tk.LEFT, padx=5)
        
        # 主要内容区域（图表和股票信息）
        content_frame = ttk.Frame(self.page4)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧K线图
        self.chart_frame = ttk.LabelFrame(content_frame, text="价格图表")
        self.chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 右侧投资组合标的监控
        self.monitor_frame = ttk.LabelFrame(content_frame, text="Choose Stocks")
        self.monitor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5, ipady=5)
        
        # 添加持仓按钮
        ttk.Button(
            self.monitor_frame, 
            text="+ Add Holdings", 
            command=self.add_holding_to_portfolio
        ).pack(fill=tk.X, padx=5, pady=5)
        
        # 投资组合选择
        ttk.Label(self.monitor_frame, text="选择投资组合:").pack(anchor=tk.W, padx=5, pady=5)
        self.monitor_portfolio = ttk.Combobox(self.monitor_frame, state="readonly")
        self.monitor_portfolio.pack(fill=tk.X, padx=5, pady=5)
        self.monitor_portfolio.bind("<<ComboboxSelected>>", lambda e: self.update_monitor())
        
        # 监控列表
        self.monitor_tree = ttk.Treeview(
            self.monitor_frame, 
            columns=("symbol", "price", "change", "change_pct"),
            show="headings",
            height=15
        )
        
        # 设置列标题
        self.monitor_tree.heading("symbol", text="标的")
        self.monitor_tree.heading("price", text="价格")
        self.monitor_tree.heading("change", text="涨跌额")
        self.monitor_tree.heading("change_pct", text="涨跌幅(%)")
        
        # 设置列宽
        self.monitor_tree.column("symbol", width=80)
        self.monitor_tree.column("price", width=80, anchor=tk.RIGHT)
        self.monitor_tree.column("change", width=80, anchor=tk.RIGHT)
        self.monitor_tree.column("change_pct", width=90, anchor=tk.RIGHT)
        
        # 双击选择股票
        self.monitor_tree.bind("<Double-1>", self.on_monitor_item_double_click)
        
        self.monitor_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 初始化股票列表
        self.init_stock_list()
    
    def init_stock_list(self):
        """初始化股票列表"""
        stocks = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "SPY", "BTC-USD", "AMD"]
        self.stock_combobox['values'] = stocks
        self.stock_combobox.set(self.selected_stock)
    
    def change_selected_stock(self):
        """更改选中的股票"""
        self.selected_stock = self.stock_combobox.get()
        self.update_stock_chart()
    
    def update_stock_chart(self):
        """更新股票图表"""
        # 清空现有图表
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        symbol = self.selected_stock
        period = self.time_period.get()
        
        try:
            # 获取股票数据
            if period == "1D":
                df = yf.download(symbol, period="1d", interval="5m")
            elif period == "5D":
                df = yf.download(symbol, period="5d", interval="30m")
            elif period == "1M":
                df = yf.download(symbol, period="1mo", interval="1d")
            elif period == "3M":
                df = yf.download(symbol, period="3mo", interval="1d")
            elif period == "6M":
                df = yf.download(symbol, period="6mo", interval="1d")
            elif period == "YTD":
                df = yf.download(symbol, period="ytd", interval="1d")
            elif period == "1Y":
                df = yf.download(symbol, period="1y", interval="1d")
            elif period == "5Y":
                df = yf.download(symbol, period="5y", interval="1wk")
            
            if df.empty:
                raise Exception("没有数据")
            
            # 获取最新价格和涨跌幅
            last_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2] if len(df) > 1 else last_price
            change = last_price - prev_price
            change_pct = (change / prev_price) * 100 if prev_price != 0 else 0
            
            # 显示价格信息
            price_frame = ttk.Frame(self.chart_frame)
            price_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Label(price_frame, text=f"{symbol}", font=("SimHei", 14, "bold")).pack(side=tk.LEFT, padx=5)
            ttk.Label(price_frame, text=f"${last_price:.2f}", font=("SimHei", 14)).pack(side=tk.LEFT, padx=10)
            
            # 涨跌额和涨跌幅（红色表示上涨，绿色表示下跌）
            color = "red" if change >= 0 else "green"
            ttk.Label(
                price_frame, 
                text=f"{change:+.2f}", 
                foreground=color,
                font=("SimHei", 12)
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Label(
                price_frame, 
                text=f"({change_pct:+.2f}%)", 
                foreground=color,
                font=("SimHei", 12)
            ).pack(side=tk.LEFT)
            
            ttk.Label(price_frame, text="Real Time", font=("SimHei", 10, "italic")).pack(side=tk.LEFT, padx=10)
            
            # 创建K线图
            fig = Figure(figsize=(8, 5), dpi=100)
            ax = fig.add_subplot(111)
            
            ax.plot(df.index, df['Close'], 'b-', linewidth=2)
            ax.set_title(f"{symbol} 价格走势 ({period})")
            ax.set_ylabel("价格 (USD)")
            
            # 设置x轴日期格式
            fig.autofmt_xdate()
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            
            # 添加网格
            ax.grid(True, linestyle='--', alpha=0.7)
            
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=5)
            
        except Exception as e:
            ttk.Label(
                self.chart_frame, 
                text=f"无法获取 {symbol} 的数据: {str(e)}", 
                foreground="red"
            ).pack(padx=5, pady=5)
        
        # 更新监控列表
        self.update_monitor_portfolio_combobox()
        self.update_monitor()
    
    def update_monitor_portfolio_combobox(self):
        """更新监控列表的投资组合下拉框"""
        portfolio_names = ["所有标的"] + list(self.portfolios.keys())
        self.monitor_portfolio['values'] = portfolio_names
        if portfolio_names:
            self.monitor_portfolio.current(0)
    
    def update_monitor(self):
        """更新监控列表"""
        # 清空现有内容
        for item in self.monitor_tree.get_children():
            self.monitor_tree.delete(item)
        
        selected_portfolio = self.monitor_portfolio.get()
        
        # 确定要显示的标的
        if selected_portfolio == "所有标的" or not self.portfolios:
            # 显示预设的标的列表
            symbols = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "SPY", "BTC-USD", "AMD"]
        else:
            # 显示选中投资组合的标的
            symbols = list(self.portfolios[selected_portfolio]["holdings"].keys())
        
        # 获取并显示每个标的的信息
        for symbol in symbols:
            try:
                # 获取最新数据
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                
                if hist.empty:
                    # 如果没有当日数据，尝试获取最新信息
                    info = ticker.info
                    last_price = info.get('regularMarketPrice', 0)
                    prev_close = info.get('regularMarketPreviousClose', last_price)
                else:
                    last_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[0] if len(hist) > 1 else last_price
                
                change = last_price - prev_close
                change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
                
                # 添加到表格
                self.monitor_tree.insert(
                    "", 
                    tk.END, 
                    values=(
                        symbol, 
                        f"${last_price:.2f}", 
                        f"{change:+.2f}", 
                        f"{change_pct:+.2f}%"
                    )
                )
            except:
                # 如果获取失败，显示占位符
                self.monitor_tree.insert(
                    "", 
                    tk.END, 
                    values=(symbol, "N/A", "N/A", "N/A")
                )
    
    def on_monitor_item_double_click(self, event):
        """双击监控列表中的项目，切换到该股票"""
        selected_item = self.monitor_tree.selection()
        if selected_item:
            symbol = self.monitor_tree.item(selected_item[0])['values'][0]
            self.selected_stock = symbol
            self.stock_combobox.set(symbol)
            self.update_stock_chart()
    
    def show_technical_indicators(self):
        """显示技术指标选择对话框（模拟）"""
        messagebox.showinfo("技术指标", "技术指标功能：移动平均线、RSI、MACD等（模拟）")
    
    def add_comparison(self):
        """添加对比资产（模拟）"""
        messagebox.showinfo("添加对比", "请选择要对比的资产（模拟）")
    
    def show_events(self):
        """显示事件（模拟）"""
        events = [
            f"{self.selected_stock} 将于3月15日发布财报",
            f"{self.selected_stock} 宣布新产品发布计划",
            f"{self.selected_stock} 获得重要合作伙伴"
        ]
        messagebox.showinfo("关键事件", "\n".join(events))
    
    def add_holding_to_portfolio(self):
        """添加持仓到投资组合"""
        if not self.portfolios:
            messagebox.showwarning("警告", "请先创建一个投资组合")
            self.notebook.select(self.page1)
            return
            
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("添加持仓")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="选择投资组合:").pack(anchor=tk.W, padx=10, pady=5)
        portfolio_combo = ttk.Combobox(dialog, values=list(self.portfolios.keys()), state="readonly")
        portfolio_combo.pack(fill=tk.X, padx=10, pady=5)
        if self.portfolios:
            portfolio_combo.current(0)
        
        ttk.Label(dialog, text="输入标的代码:").pack(anchor=tk.W, padx=10, pady=5)
        symbol_entry = ttk.Entry(dialog)
        symbol_entry.pack(fill=tk.X, padx=10, pady=5)
        symbol_entry.insert(0, self.selected_stock)  # 默认当前选中的股票
        
        ttk.Label(dialog, text="权重 (%):").pack(anchor=tk.W, padx=10, pady=5)
        weight_entry = ttk.Entry(dialog)
        weight_entry.pack(fill=tk.X, padx=10, pady=5)
        weight_entry.insert(0, "10")
        
        def add_holding():
            portfolio_name = portfolio_combo.get()
            symbol = symbol_entry.get().strip().upper()
            try:
                weight = float(weight_entry.get().strip())
                if weight <= 0 or weight > 100:
                    raise ValueError
            except:
                messagebox.showwarning("警告", "请输入有效的权重（1-100）")
                return
            
            if not portfolio_name or not symbol:
                messagebox.showwarning("警告", "请填写所有字段")
                return
            
            # 添加到投资组合
            portfolio = self.portfolios[portfolio_name]
            
            # 调整现有持仓权重，确保总和不超过100
            current_total = sum(data["weight"] for data in portfolio["holdings"].values())
            remaining = 100 - current_total
            
            if weight > remaining:
                weight = remaining
                messagebox.showinfo("提示", f"权重已调整为最大可能值: {weight}%")
            
            portfolio["holdings"][symbol] = {"weight": weight}
            
            # 更新监控列表
            self.update_monitor()
            
            dialog.destroy()
            messagebox.showinfo("成功", f"已添加 {symbol} 到 {portfolio_name}")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="添加", command=add_holding).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        symbol_entry.focus()
        self.root.wait_window(dialog)

if __name__ == "__main__":
    # 提示用户安装依赖
    try:
        import requests
    except ImportError:
        print("请先安装requests库：pip install requests")
        exit()
    
    root = tk.Tk()
    app = InvestmentPortfolioApp(root)
    root.mainloop()