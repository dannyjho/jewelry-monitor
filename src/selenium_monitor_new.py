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

class NewAPIJewelryMonitor:
    """使用新 API 端點的金工珠寶監控工具"""
    
    def __init__(self):
        self.keywords = self.load_keywords()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.results_dir = os.path.join(self.base_dir, "results")
        self.ensure_results_dir()
        
        # Telegram 設定
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        # 論壇配置 - 從你提供的 URL 分析
        self.forum_configs = {
            'marriage': {
                'name': '結婚版',
                'listKey': 'f_popular_v3_f11e8d02-6756-4376-9db3-e1cca4d2a66c',
                'immersiveKey': 'v_popular_f11e8d02-6756-4376-9db3-e1cca4d2a66c'
            },
            'jewelry': {
                'name': '珠寶版',
                'listKey': 'f_popular_v3_jewelry',  # 需要實際獲取
                'immersiveKey': 'v_popular_jewelry'
            },
            'girl': {
                'name': '女孩版',
                'listKey': 'f_popular_v3_girl',
                'immersiveKey': 'v_popular_girl'
            }
        }
        
        print("🔧 初始化新 API 金工珠寶監控器")
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
            print("🚀 正在啟動 Chromium 瀏覽器...")
            
            chrome_options = Options()
            
            # GitHub Actions 環境設定
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
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
            
            service = Service('/usr/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 設定超時
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            # 反檢測腳本
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['zh-TW', 'zh', 'en']})")
            
            print("✅ Chromium 瀏覽器啟動成功")
            return driver
            
        except Exception as e:
            print(f"❌ 創建瀏覽器失敗: {e}")
            traceback.print_exc()
            return None
    
    def extract_api_keys_from_page(self, driver, forum):
        """從頁面中提取真實的 API 參數"""
        try:
            print(f"🔍 從 {forum} 版頁面提取 API 參數...")
            
            # 訪問論壇頁面
            url = f"https://www.dcard.tw/f/{forum}"
            driver.get(url)
            
            # 等待頁面載入
            time.sleep(5)
            
            # 監聽網路請求來獲取真實的 API 參數
            logs = driver.get_log('performance')
            
            api_params = {}
            
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    url = message['message']['params']['response']['url']
                    
                    # 尋找 globalPaging API 請求
                    if 'globalPaging/page' in url:
                        print(f"✅ 找到 API 請求: {url}")
                        
                        # 解析 URL 參數
                        from urllib.parse import urlparse, parse_qs
                        parsed = urlparse(url)
                        params = parse_qs(parsed.query)
                        
                        api_params = {
                            'listKey': params.get('listKey', [''])[0],
                            'immersiveVideoListKey': params.get('immersiveVideoListKey', [''])[0],
                            'pageKey': params.get('pageKey', [''])[0]
                        }
                        
                        print(f"📋 提取到的參數: {api_params}")
                        break
            
            return api_params
            
        except Exception as e:
            print(f"❌ 提取 API 參數失敗: {e}")
            return None
    
    def get_article_content(self, session, article_id, forum_url):
        """獲取文章的完整內容"""
        try:
            print(f"📄 獲取文章 {article_id} 的完整內容...")
            
            # 文章詳情 API
            article_api_url = f"https://www.dcard.tw/service/api/v2/posts/{article_id}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': forum_url,
                'Origin': 'https://www.dcard.tw',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            }
            
            response = session.get(article_api_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                try:
                    article_data = response.json()
                    content = article_data.get('content', '')
                    title = article_data.get('title', '')
                    excerpt = article_data.get('excerpt', '')
                    
                    print(f"✅ 成功獲取文章內容 (長度: {len(content)} 字元)")
                    
                    return {
                        'id': article_id,
                        'title': title,
                        'content': content,
                        'excerpt': excerpt,
                        'full_text': f"{title} {content}",  # 用於關鍵字搜尋
                        'likeCount': article_data.get('likeCount', 0),
                        'commentCount': article_data.get('commentCount', 0),
                        'createdAt': article_data.get('createdAt', ''),
                        'school': article_data.get('school', ''),
                        'department': article_data.get('department', '')
                    }
                    
                except json.JSONDecodeError as e:
                    print(f"❌ 文章內容 JSON 解析失敗: {e}")
                    return None
            else:
                print(f"⚠️ 獲取文章內容失敗: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 獲取文章內容時發生錯誤: {e}")
            return None
    
    def get_posts_via_new_api(self, driver, forum, forum_name):
        """使用新的 API 端點獲取文章"""
        try:
            print(f"\n{'='*50}")
            print(f"🌐 使用新 API 獲取 {forum_name} 文章")
            print(f"{'='*50}")
            
            # 先訪問論壇頁面建立 session
            print("🏠 先訪問論壇頁面...")
            forum_url = f"https://www.dcard.tw/f/{forum}"
            driver.get(forum_url)
            
            # 等待頁面載入
            time.sleep(random.uniform(3, 6))
            
            # 滾動頁面觸發 API 請求
            print("📜 滾動頁面觸發 API...")
            for i in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))
            
            # 獲取 cookies 用於 API 請求
            cookies = driver.get_cookies()
            session_cookies = {}
            for cookie in cookies:
                session_cookies[cookie['name']] = cookie['value']
            
            # 構建 API 請求
            if forum in self.forum_configs:
                config = self.forum_configs[forum]
                listKey = config['listKey']
                immersiveKey = config['immersiveKey']
            else:
                print(f"⚠️ 未找到 {forum} 的配置，使用通用配置")
                listKey = f"f_popular_v3_{forum}"
                immersiveKey = f"v_popular_{forum}"
            
            # API 端點
            api_url = "https://www.dcard.tw/service/api/v2/globalPaging/page"
            
            # API 參數
            params = {
                'enrich': 'true',
                'forumLogo': 'true',
                'pinnedPosts': 'widget',
                'country': 'TW',
                'platform': 'web',
                'listKey': listKey,
                'immersiveVideoListKey': immersiveKey,
                'pageKey': f"{forum}_page_{int(time.time())}",  # 生成唯一的 pageKey
                'offset': '0'
            }
            
            # 設定 headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': forum_url,
                'Origin': 'https://www.dcard.tw',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            }
            
            print(f"📡 請求 API: {api_url}")
            print(f"📋 參數: {params}")
            
            # 發送 API 請求
            session = requests.Session()
            session.cookies.update(session_cookies)
            
            response = session.get(api_url, params=params, headers=headers, timeout=30)
            
            print(f"📊 API 回應狀態: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # 解析回應中的文章 ID
                    basic_posts = self.parse_api_response(data, forum)
                    print(f"✅ 找到 {len(basic_posts)} 篇文章，開始獲取完整內容...")
                    
                    # 獲取每篇文章的完整內容
                    detailed_posts = []
                    for i, post in enumerate(basic_posts[:15], 1):  # 限制處理數量避免過載
                        print(f"📖 處理第 {i} 篇文章 (ID: {post['id']})...")
                        
                        article_detail = self.get_article_content(session, post['id'], forum_url)
                        
                        if article_detail:
                            # 合併基本資訊和詳細內容
                            detailed_post = {
                                **post,  # 基本資訊
                                **article_detail,  # 詳細內容
                                'url': f"https://www.dcard.tw/f/{forum}/p/{post['id']}"
                            }
                            detailed_posts.append(detailed_post)
                        else:
                            # 如果無法獲取詳細內容，使用基本資訊
                            detailed_posts.append(post)
                        
                        # 避免請求過快
                        time.sleep(random.uniform(0.5, 1.5))
                    
                    print(f"✅ 成功獲取 {len(detailed_posts)} 篇文章的詳細內容")
                    return detailed_posts
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 解析失敗: {e}")
                    print(f"回應內容: {response.text[:200]}...")
                    return []
            else:
                print(f"❌ API 請求失敗: {response.status_code}")
                print(f"回應內容: {response.text[:200]}...")
                return []
                
        except Exception as e:
            print(f"❌ 新 API 請求失敗: {e}")
            traceback.print_exc()
            return []
    
    def parse_api_response(self, data, forum):
        """解析 API 回應中的文章"""
        posts = []
        
        try:
            print("🔍 分析新版 API 回應結構...")
            
            # 方法 1: 直接尋找 posts 或類似的陣列
            post_arrays = []
            
            def find_post_arrays(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(value, list) and len(value) > 0:
                            # 檢查是否為文章陣列
                            first_item = value[0]
                            if isinstance(first_item, dict) and 'id' in first_item:
                                print(f"✅ 找到文章陣列於: {path}.{key} (包含 {len(value)} 個項目)")
                                post_arrays.append(value)
                        elif isinstance(value, (dict, list)):
                            find_post_arrays(value, f"{path}.{key}" if path else key)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        if isinstance(item, (dict, list)):
                            find_post_arrays(item, f"{path}[{i}]")
            
            find_post_arrays(data)
            
            # 方法 2: 如果找不到明顯的文章陣列，遞歸搜尋所有 ID
            if not post_arrays:
                print("🔍 未找到明顯的文章陣列，搜尋所有文章 ID...")
                
                def find_article_ids(obj, collected_ids=None):
                    if collected_ids is None:
                        collected_ids = []
                    
                    if isinstance(obj, dict):
                        # 尋找文章 ID（通常是數字且在合理範圍內）
                        if 'id' in obj:
                            article_id = obj['id']
                            if isinstance(article_id, (int, str)) and str(article_id).isdigit():
                                id_num = int(article_id)
                                if 100000000 <= id_num <= 999999999:  # Dcard 文章 ID 範圍
                                    collected_ids.append({
                                        'id': str(article_id),
                                        'title': obj.get('title', f'文章 {article_id}'),
                                        'excerpt': obj.get('excerpt', ''),
                                        'url': f"https://www.dcard.tw/f/{forum}/p/{article_id}",
                                        'forum': forum,
                                        'source': 'new_api_id_search'
                                    })
                                    print(f"📝 找到文章 ID: {article_id}")
                        
                        for value in obj.values():
                            find_article_ids(value, collected_ids)
                            
                    elif isinstance(obj, list):
                        for item in obj:
                            find_article_ids(item, collected_ids)
                    
                    return collected_ids
                
                posts = find_article_ids(data)
            else:
                # 處理找到的文章陣列
                for post_array in post_arrays:
                    for post_item in post_array:
                        if isinstance(post_item, dict) and 'id' in post_item:
                            posts.append({
                                'id': str(post_item.get('id', '')),
                                'title': post_item.get('title', f"文章 {post_item.get('id', '')}"),
                                'excerpt': post_item.get('excerpt', ''),
                                'url': f"https://www.dcard.tw/f/{forum}/p/{post_item.get('id', '')}",
                                'forum': forum,
                                'source': 'new_api_array'
                            })
                            print(f"📝 處理文章: {post_item.get('title', '')[:40]}...")
            
            # 去重（基於 ID）
            seen_ids = set()
            unique_posts = []
            for post in posts:
                if post['id'] not in seen_ids:
                    seen_ids.add(post['id'])
                    unique_posts.append(post)
            
            print(f"✅ 解析完成，找到 {len(unique_posts)} 篇唯一文章")
            return unique_posts
            
        except Exception as e:
            print(f"❌ 解析 API 回應失敗: {e}")
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
            'content_preview': post.get('content', '')[:300],  # 前300字內容預覽
            'like_count': post.get('likeCount', 0),
            'comment_count': post.get('commentCount', 0),
            'author': f"{post.get('school', '')} {post.get('department', '')}".strip(),
            'created_at': post.get('createdAt', ''),
            'source': 'new_api_with_content',
            'found_at': taiwan_time.strftime('%Y-%m-%d %H:%M:%S'),
            'found_at_utc': now.strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        # 保存到 JSON 檔案
        today = taiwan_time.strftime('%Y-%m-%d')
        json_file = os.path.join(self.results_dir, f"new_api_matches_{today}.json")
        
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
        summary_file = os.path.join(self.base_dir, "new_api_matches.txt")
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"發現時間: {match_data['found_at']} (台灣時間)\n")
            f.write(f"平台: Dcard {forum_name}\n")
            f.write(f"標題: {match_data['title']}\n")
            f.write(f"網址: {match_data['url']}\n")
            f.write(f"匹配關鍵字: {', '.join(keywords)}\n")
            f.write(f"來源: 新版 API\n")
        
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
            message = f"🎯 新版 API 金工珠寶監控報告 ({taiwan_time})\n"
            message += f"發現 {len(matches)} 篇相關文章！\n\n"
            
            for i, match in enumerate(matches[:3], 1):  # 最多顯示 3 篇
                message += f"{i}. {match['title'][:40]}...\n"
                message += f"   📍 {match['forum_name']}\n"
                message += f"   🔗 {match['url']}\n"
                message += f"   🏷️ {', '.join(match['matched_keywords'][:3])}\n"
                message += f"   🆕 來源: 新版 API\n\n"
            
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
    
    def run_new_api_monitoring(self):
        """執行新版 API 監控任務"""
        start_time = datetime.now()
        print("🚀 開始新版 API 金工珠寶監控任務")
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
                'marriage': '結婚版',
                'jewelry': '珠寶版',
                'girl': '女孩版'
            }
            
            all_matches = []
            successful_forums = 0
            
            for forum_key, forum_name in forums.items():
                try:
                    # 使用新版 API 獲取文章
                    posts = self.get_posts_via_new_api(driver, forum_key, forum_name)
                    
                    if posts:
                        successful_forums += 1
                        matches = []
                        
                        for post in posts:
                            title = post.get('title', '')
                            content = post.get('content', '')
                            excerpt = post.get('excerpt', '')
                            
                            # 使用完整內容進行關鍵字匹配
                            full_text = f"{title} {content} {excerpt}"
                            matched_keywords = self.check_keywords(full_text)
                            
                            if matched_keywords:
                                match_data = self.save_match(post, forum_key, forum_name, matched_keywords)
                                matches.append(match_data)
                                print(f"🎯 匹配文章: {title[:40]}... (關鍵字: {', '.join(matched_keywords[:3])})")
                        
                        all_matches.extend(matches)
                        print(f"✅ {forum_name} 完成，發現 {len(matches)} 篇匹配")
                    else:
                        print(f"❌ {forum_name} 無法獲取文章")
                    
                except Exception as e:
                    print(f"❌ 處理 {forum_name} 時發生錯誤: {e}")
                    traceback.print_exc()
                
                # 論壇間等待
                if forum_key != list(forums.keys())[-1]:
                    wait_time = random.uniform(5, 10)
                    print(f"⏳ 等待 {wait_time:.1f} 秒後處理下一個論壇...")
                    time.sleep(wait_time)
            
            # 生成摘要報告
            summary = {
                'execution_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'method': 'new_api',
                'successful_forums': successful_forums,
                'total_forums': len(forums),
                'total_matches': len(all_matches),
                'matches': all_matches
            }
            
            summary_file = os.path.join(self.base_dir, "new_api_summary.json")
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            # 發送通知
            if all_matches:
                self.send_telegram_notification(all_matches)
            
            # 輸出結果
            end_time = datetime.now()
            duration = (end_time - start_time).seconds
            
            print(f"\n🎉 新版 API 監控任務完成!")
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
        monitor = NewAPIJewelryMonitor()
        monitor.run_new_api_monitoring()
    except Exception as e:
        print(f"❌ 程式執行失敗: {e}")
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()