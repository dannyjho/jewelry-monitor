import time
import json
import os
import re
import requests
from datetime import datetime, timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import traceback
import random

class SeleniumJewelryMonitor:
    """使用 Selenium 的金工珠寶監控工具"""
    
    def __init__(self):
        self.keywords = self.load_keywords()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.results_dir = os.path.join(self.base_dir, "results")
        self.ensure_results_dir()
        
        # Telegram 設定
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        print("🔧 初始化 Selenium 金工珠寶監控器")
        print(f"📁 結果目錄: {self.results_dir}")
        print(f"📝 關鍵字數量: {len(self.keywords)}")
        
    def load_keywords(self):
        """載入監控關鍵字"""
        return [
            # 核心金工珠寶關鍵字
            "金工", "銀工", "手作金工", "金工教學", "金工課程", "金工工作室",
            "珠寶", "珠寶設計", "珠寶製作", "首飾", "首飾設計", "手作首飾",
            
            # 技術工藝
            "鑲嵌", "寶石鑲嵌", "維修", "珠寶維修", "首飾維修", "改圍",
            "拋光", "電鍍", "焊接", "雕蠟", "鑄造",
            
            # 材料
            "K金", "18K", "14K", "白金", "黃金", "玫瑰金", "純銀", "925銀",
            "鑽石", "寶石", "翡翠", "珍珠", "紅寶石", "藍寶石", "祖母綠",
            
            # 產品
            "戒指", "項鍊", "手鍊", "耳環", "婚戒", "對戒", "求婚戒指", "情侶戒",
            
            # 服務
            "訂做", "客製", "訂製", "推薦", "分享", "評價", "開箱"
        ]
    
    def ensure_results_dir(self):
        """確保結果目錄存在"""
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            print(f"📁 創建結果目錄: {self.results_dir}")
    
    def create_driver(self):
        """創建 Chrome 瀏覽器實例"""
        try:
            print("🚀 正在啟動 Chrome 瀏覽器...")
            
            chrome_options = Options()
            
            # GitHub Actions 環境設定
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')  # 加快載入速度
            
            # 反檢測設定
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 模擬真實用戶
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 在 GitHub Actions 中使用系統 Chrome
            chrome_options.binary_location = '/usr/bin/chromium-browser'
            
            # 使用系統的 chromedriver
            driver = webdriver.Chrome(
                executable_path='/usr/bin/chromedriver',
                options=chrome_options
            )
            
            # 設定頁面載入超時
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            # 執行反檢測腳本
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['zh-TW', 'zh', 'en']})")
            
            print("✅ Chrome 瀏覽器啟動成功")
            return driver
            
        except Exception as e:
            print(f"❌ 創建瀏覽器失敗: {e}")
            traceback.print_exc()
            return None
    
    def simulate_human_behavior(self, driver):
        """模擬人類瀏覽行為"""
        try:
            # 隨機滾動
            scroll_to = random.randint(100, 800)
            driver.execute_script(f"window.scrollTo(0, {scroll_to});")
            
            # 隨機等待
            wait_time = random.uniform(1, 3)
            time.sleep(wait_time)
            
            # 再次滾動
            scroll_to = random.randint(500, 1200)
            driver.execute_script(f"window.scrollTo(0, {scroll_to});")
            
            time.sleep(random.uniform(0.5, 2))
            
        except Exception as e:
            print(f"⚠️ 模擬人類行為時發生錯誤: {e}")
    
    def wait_for_page_load(self, driver, timeout=20):
        """等待頁面完全載入"""
        try:
            # 等待頁面基本元素載入
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 等待 JavaScript 執行完成
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            print("✅ 頁面載入完成")
            return True
            
        except TimeoutException:
            print("⚠️ 頁面載入超時")
            return False
    
    def extract_articles_from_page(self, driver, forum):
        """從頁面中提取文章資訊"""
        articles = []
        
        try:
            print("🔍 開始提取文章資訊...")
            
            # 等待內容載入
            time.sleep(3)
            
            # 嘗試多種文章選擇器
            article_selectors = [
                'article',
                '[data-testid*="post"]',
                '[class*="Post"]',
                '[class*="post"]',
                'a[href*="/p/"]',
                '.PostEntry_container',
                '.post-item'
            ]
            
            found_elements = []
            for selector in article_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"✅ 使用選擇器 '{selector}' 找到 {len(elements)} 個元素")
                        found_elements = elements
                        break
                except Exception as e:
                    continue
            
            if not found_elements:
                print("⚠️ 使用標準選擇器找不到文章，嘗試通用方法...")
                # 尋找包含連結的元素
                found_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/f/' + forum + '/p/"]')
            
            if not found_elements:
                print("⚠️ 仍然找不到文章元素，嘗試從頁面源碼提取...")
                return self.extract_from_page_source(driver, forum)
            
            print(f"📄 找到 {len(found_elements)} 個潛在文章元素")
            
            # 提取文章資訊
            processed_urls = set()
            
            for i, element in enumerate(found_elements[:30]):  # 限制處理數量
                try:
                    article_data = {}
                    
                    # 嘗試獲取標題
                    title = ""
                    title_selectors = ['h3', 'h2', '.title', '[class*="title"]', '[class*="Title"]']
                    
                    for title_selector in title_selectors:
                        try:
                            title_element = element.find_element(By.CSS_SELECTOR, title_selector)
                            title = title_element.text.strip()
                            if title:
                                break
                        except:
                            continue
                    
                    # 如果在元素內找不到標題，嘗試元素本身的文字
                    if not title:
                        title = element.text.strip()
                    
                    # 獲取連結
                    url = ""
                    try:
                        if element.tag_name == 'a':
                            url = element.get_attribute("href")
                        else:
                            link_element = element.find_element(By.TAG_NAME, "a")
                            url = link_element.get_attribute("href")
                    except:
                        pass
                    
                    # 驗證是否為有效的文章連結
                    if url and f"/f/{forum}/p/" in url and url not in processed_urls:
                        # 提取文章 ID
                        post_id = re.search(r'/p/(\d+)', url)
                        if post_id:
                            article_data = {
                                'id': post_id.group(1),
                                'title': title,
                                'url': url,
                                'excerpt': title,  # 暫時用標題當摘要
                                'forum': forum,
                                'source': 'selenium'
                            }
                            articles.append(article_data)
                            processed_urls.add(url)
                            
                            print(f"📝 提取文章 {len(articles)}: {title[:40]}...")
                
                except Exception as e:
                    continue
            
            print(f"✅ 成功提取 {len(articles)} 篇文章")
            return articles
            
        except Exception as e:
            print(f"❌ 提取文章時發生錯誤: {e}")
            traceback.print_exc()
            return []
    
    def extract_from_page_source(self, driver, forum):
        """從頁面源碼提取文章"""
        try:
            print("🔍 從頁面源碼提取文章...")
            
            page_source = driver.page_source
            articles = []
            
            # 使用正則表達式尋找文章連結和標題
            # 尋找文章連結
            link_pattern = rf'href="(/f/{forum}/p/\d+)"'
            links = re.findall(link_pattern, page_source)
            
            # 尋找可能的標題（在文章連結附近）
            for link in links[:20]:  # 限制數量
                try:
                    # 構建完整 URL
                    full_url = f"https://www.dcard.tw{link}"
                    
                    # 提取文章 ID
                    post_id = re.search(r'/p/(\d+)', link)
                    if post_id:
                        # 嘗試在頁面源碼中找到對應的標題
                        # 這是簡化版本，實際可能需要更複雜的解析
                        article_data = {
                            'id': post_id.group(1),
                            'title': f"文章 {post_id.group(1)}",  # 暫時的標題
                            'url': full_url,
                            'excerpt': '',
                            'forum': forum,
                            'source': 'selenium_source'
                        }
                        articles.append(article_data)
                        
                except Exception as e:
                    continue
            
            print(f"✅ 從源碼提取到 {len(articles)} 篇文章")
            return articles
            
        except Exception as e:
            print(f"❌ 從源碼提取失敗: {e}")
            return []
    
    def get_forum_posts_selenium(self, driver, forum, forum_name):
        """使用 Selenium 獲取論壇文章"""