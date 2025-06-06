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
        """創建 Chrome 瀏覽器實例 - 系統套件版"""
        try:
            print("🚀 正在啟動 Chromium 瀏覽器...")
            
            chrome_options = Options()
            
            # GitHub Actions 環境必要設定
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            
            # 反檢測設定
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 設定用戶代理
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 使用系統安裝的 Chromium
            chrome_options.binary_location = '/usr/bin/chromium-browser'
            
            # 使用新版 Selenium 語法
            from selenium.webdriver.chrome.service import Service
            
            print("📍 使用系統套件安裝的 ChromeDriver...")
            
            # 使用系統安裝的 ChromeDriver
            service = Service('/usr/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 設定超時
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            # 反檢測腳本
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['zh-TW', 'zh', 'en']})")
            
            # 測試瀏覽器基本功能
            print("🧪 測試瀏覽器基本功能...")
            test_html = "data:text/html,<html><body><h1>Selenium Test</h1><p>瀏覽器測試成功</p></body></html>"
            driver.get(test_html)
            
            # 檢查頁面是否載入成功
            if "Selenium Test" in driver.page_source:
                print("✅ Chromium 瀏覽器啟動並測試成功")
                return driver
            else:
                print("❌ 瀏覽器測試失敗")
                driver.quit()
                return None
            
        except Exception as e:
            print(f"❌ 創建瀏覽器失敗: {e}")
            print("🔍 錯誤詳細資訊:")
            traceback.print_exc()
            
            # 嘗試診斷問題
            print("\n🔧 診斷環境:")
            try:
                import os
                print(f"Chromium 是否存在: {os.path.exists('/usr/bin/chromium-browser')}")
                print(f"ChromeDriver 是否存在: {os.path.exists('/usr/bin/chromedriver')}")
                
                if os.path.exists('/usr/bin/chromium-browser'):
                    os.system('ls -la /usr/bin/chromium-browser')
                if os.path.exists('/usr/bin/chromedriver'):
                    os.system('ls -la /usr/bin/chromedriver')
                    
            except Exception as diag_e:
                print(f"診斷失敗: {diag_e}")
            
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
        try:
            print(f"\n{'='*50}")
            print(f"🌐 使用 Selenium 訪問 {forum_name}")
            print(f"{'='*50}")
            
            # 構建 URL
            url = f"https://www.dcard.tw/f/{forum}"
            print(f"📡 訪問 URL: {url}")
            
            # 訪問頁面
            driver.get(url)
            
            # 等待頁面載入
            if not self.wait_for_page_load(driver):
                print(f"❌ {forum_name} 頁面載入失敗")
                return []
            
            print(f"✅ {forum_name} 頁面載入成功")
            
            # 模擬人類瀏覽行為
            self.simulate_human_behavior(driver)
            
            # 等待動態內容載入
            print("⏳ 等待動態內容載入...")
            time.sleep(random.uniform(3, 6))
            
            # 滾動載入更多內容
            print("📜 滾動載入更多內容...")
            for i in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))
            
            # 提取文章
            articles = self.extract_articles_from_page(driver, forum)
            
            if articles:
                print(f"🎉 {forum_name} 成功獲取 {len(articles)} 篇文章")
            else:
                print(f"⚠️ {forum_name} 沒有獲取到文章")
            
            return articles
            
        except Exception as e:
            print(f"❌ 獲取 {forum_name} 文章失敗: {e}")
            traceback.print_exc()
            return []
    
    def check_keywords(self, text):
        """檢查關鍵字匹配"""
        if not text:
            return []
            
        text_lower = text.lower()
        matched = []
        
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)
        
        return matched
    
    def save_match(self, post, forum, forum_name, keywords):
        """保存匹配結果"""
        now = datetime.now(timezone.utc)
        taiwan_time = now.replace(tzinfo=timezone.utc).astimezone(tz=None)
        
        match_data = {
            'id': post['id'],
            'forum': forum,
            'forum_name': forum_name,
            'title': post.get('title', ''),
            'url': post.get('url', ''),
            'matched_keywords': keywords,
            'excerpt': post.get('excerpt', '')[:200],
            'source': 'selenium',
            'found_at': taiwan_time.strftime('%Y-%m-%d %H:%M:%S'),
            'found_at_utc': now.strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        # 保存到 JSON 檔案
        today = taiwan_time.strftime('%Y-%m-%d')
        json_file = os.path.join(self.results_dir, f"selenium_matches_{today}.json")
        
        matches = []
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    matches = json.load(f)
            except:
                matches = []
        
        matches.append(match_data)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)
        
        # 保存到總結果檔案
        summary_file = os.path.join(self.base_dir, "selenium_matches.txt")
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"發現時間: {match_data['found_at']} (台灣時間)\n")
            f.write(f"平台: Dcard {forum_name}\n")
            f.write(f"標題: {match_data['title']}\n")
            f.write(f"網址: {match_data['url']}\n")
            f.write(f"匹配關鍵字: {', '.join(keywords)}\n")
            f.write(f"來源: Selenium 瀏覽器\n")
        
        print(f"✅ 保存匹配: {post.get('title', '')[:50]}...")
        return match_data
    
    def send_telegram_notification(self, matches):
        """發送 Telegram 通知"""
        if not self.telegram_token or not self.telegram_chat_id:
            print("⚠️ 未設定 Telegram，跳過通知")
            return
            
        if not matches:
            return
        
        try:
            taiwan_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            message = f"🎯 Selenium 金工珠寶監控報告 ({taiwan_time})\n"
            message += f"發現 {len(matches)} 篇相關文章！\n\n"
            
            for i, match in enumerate(matches[:3], 1):  # 最多顯示 3 篇
                message += f"{i}. {match['title'][:40]}...\n"
                message += f"   📍 {match['forum_name']}\n"
                message += f"   🔗 {match['url']}\n"
                message += f"   🏷️ {', '.join(match['matched_keywords'][:3])}\n"
                message += f"   🤖 來源: Selenium\n\n"
            
            if len(matches) > 3:
                message += f"... 還有 {len(matches) - 3} 篇文章\n"
            
            message += "📊 完整結果請查看 GitHub 儲存庫"
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print("✅ Telegram 通知發送成功")
            else:
                print(f"❌ Telegram 通知發送失敗: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Telegram 通知錯誤: {e}")
    
    def run_selenium_monitoring(self):
        """執行 Selenium 監控任務"""
        start_time = datetime.now()
        print("🚀 開始 Selenium 金工珠寶監控任務")
        print(f"⏰ 開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 監控關鍵字: {len(self.keywords)} 個")
        
        driver = None
        try:
            # 創建瀏覽器
            driver = self.create_driver()
            if not driver:
                print("❌ 無法創建瀏覽器，監控中止")
                return
            
            forums = {
                'jewelry': '珠寶版',
                'marriage': '結婚版', 
                'girl': '女孩版'
            }
            
            all_matches = []
            successful_forums = 0
            
            for forum_key, forum_name in forums.items():
                try:
                    # 使用 Selenium 獲取文章
                    posts = self.get_forum_posts_selenium(driver, forum_key, forum_name)
                    
                    if posts:
                        successful_forums += 1
                        matches = []
                        
                        for post in posts:
                            title = post.get('title', '')
                            excerpt = post.get('excerpt', '')
                            text = f"{title} {excerpt}"
                            
                            matched_keywords = self.check_keywords(text)
                            
                            if matched_keywords:
                                match_data = self.save_match(post, forum_key, forum_name, matched_keywords)
                                matches.append(match_data)
                        
                        all_matches.extend(matches)
                        print(f"✅ {forum_name} 完成，發現 {len(matches)} 篇匹配")
                    
                except Exception as e:
                    print(f"❌ 處理 {forum_name} 時發生錯誤: {e}")
                
                # 論壇間等待
                if forum_key != list(forums.keys())[-1]:
                    wait_time = random.uniform(5, 10)
                    print(f"⏳ 等待 {wait_time:.1f} 秒後處理下一個論壇...")
                    time.sleep(wait_time)
            
            # 生成摘要報告
            summary = {
                'execution_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'method': 'selenium',
                'successful_forums': successful_forums,
                'total_forums': len(forums),
                'total_matches': len(all_matches),
                'matches': all_matches
            }
            
            summary_file = os.path.join(self.base_dir, "selenium_summary.json")
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            # 發送通知
            if all_matches:
                self.send_telegram_notification(all_matches)
            
            # 輸出結果
            end_time = datetime.now()
            duration = (end_time - start_time).seconds
            
            print(f"\n🎉 Selenium 監控任務完成!")
            print(f"⏱️ 執行時間: {duration} 秒")
            print(f"📊 成功論壇: {successful_forums}/{len(forums)}")
            print(f"🎯 總計發現: {len(all_matches)} 篇匹配文章")
            
            if all_matches:
                print(f"🏆 各論壇匹配數:")
                forum_stats = {}
                for match in all_matches:
                    forum_name = match['forum_name']
                    forum_stats[forum_name] = forum_stats.get(forum_name, 0) + 1
                
                for forum, count in forum_stats.items():
                    print(f"   • {forum}: {count} 篇")
            else:
                print("✅ 本次未發現新的匹配文章")
        
        finally:
            # 確保關閉瀏覽器
            if driver:
                try:
                    driver.quit()
                    print("✅ 瀏覽器已關閉")
                except Exception as e:
                    print(f"⚠️ 關閉瀏覽器時發生錯誤: {e}")

def main():
    try:
        monitor = SeleniumJewelryMonitor()
        monitor.run_selenium_monitoring()
    except Exception as e:
        print(f"❌ 程式執行失敗: {e}")
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()