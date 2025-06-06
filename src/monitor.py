import requests
import json
import os
from datetime import datetime, timezone
import cloudscraper
import time
import traceback
import random

class JewelryMonitor:
    def __init__(self):
        # 使用 cloudscraper 來繞過 Cloudflare
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        # 設置更真實的 headers
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        })
        
        self.keywords = self.load_keywords()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.results_dir = os.path.join(self.base_dir, "results")
        self.ensure_results_dir()
        
        # Telegram 設定
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        print(f"🔧 初始化完成")
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
    
    def get_processed_posts(self):
        """獲取已處理的文章列表"""
        processed_file = os.path.join(self.results_dir, "processed_posts.txt")
        processed_posts = set()
        
        if os.path.exists(processed_file):
            with open(processed_file, 'r', encoding='utf-8') as f:
                processed_posts = set(line.strip() for line in f if line.strip())
        
        return processed_posts
    
    def save_processed_post(self, post_id):
        """記錄已處理的文章"""
        processed_file = os.path.join(self.results_dir, "processed_posts.txt")
        
        with open(processed_file, 'a', encoding='utf-8') as f:
            f.write(f"{post_id}\n")
    
    def get_dcard_posts(self, forum, limit=30):
        """獲取 Dcard 文章 - 增強版反爬蟲"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 嘗試第 {attempt + 1} 次獲取 {forum} 版文章...")
                
                # 隨機延遲避免被檢測
                delay = random.uniform(2, 5)
                print(f"⏳ 等待 {delay:.1f} 秒...")
                time.sleep(delay)
                
                # 構建 URL
                url = f"https://www.dcard.tw/service/api/v2/forums/{forum}/posts"
                params = {
                    'limit': limit,
                    'popular': 'false'  # 使用字串而不是 Boolean
                }
                
                # 更新 Referer 讓請求更真實
                self.scraper.headers.update({
                    'Referer': f'https://www.dcard.tw/f/{forum}',
                    'X-Requested-With': 'XMLHttpRequest'
                })
                
                print(f"📡 正在請求: {url}")
                response = self.scraper.get(
                    url, 
                    params=params, 
                    timeout=30,
                    allow_redirects=True
                )
                
                print(f"📊 回應狀態碼: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 成功獲取 {len(data)} 篇文章")
                    return data
                elif response.status_code == 403:
                    print(f"🚫 403 錯誤，等待更長時間後重試...")
                    time.sleep(10 + attempt * 5)
                else:
                    print(f"⚠️ 未預期的狀態碼: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"🌐 網路錯誤: {e}")
            except json.JSONDecodeError as e:
                print(f"📄 JSON 解析錯誤: {e}")
            except Exception as e:
                print(f"❌ 未知錯誤: {e}")
                traceback.print_exc()
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"⏳ 等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)
        
        print(f"❌ 獲取 {forum} 版文章失敗，已重試 {max_retries} 次")
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
        
        url = f"https://www.dcard.tw/f/{forum}/p/{post['id']}"
        
        match_data = {
            'id': post['id'],
            'forum': forum,
            'forum_name': forum_name,
            'title': post.get('title', ''),
            'url': url,
            'author': f"{post.get('school', '')} {post.get('department', '')}".strip(),
            'matched_keywords': keywords,
            'excerpt': post.get('excerpt', '')[:200],
            'like_count': post.get('likeCount', 0),
            'comment_count': post.get('commentCount', 0),
            'created_at': post.get('createdAt', ''),
            'found_at': taiwan_time.strftime('%Y-%m-%d %H:%M:%S'),
            'found_at_utc': now.strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        # 保存到 JSON 檔案
        today = taiwan_time.strftime('%Y-%m-%d')
        json_file = os.path.join(self.results_dir, f"matches_{today}.json")
        
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
        summary_file = os.path.join(self.base_dir, "latest_matches.txt")
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"發現時間: {match_data['found_at']} (台灣時間)\n")
            f.write(f"平台: Dcard {forum_name}\n")
            f.write(f"標題: {match_data['title']}\n")
            f.write(f"作者: {match_data['author']}\n")
            f.write(f"網址: {url}\n")
            f.write(f"匹配關鍵字: {', '.join(keywords)}\n")
            f.write(f"愛心/留言: {match_data['like_count']}/{match_data['comment_count']}\n")
            f.write(f"摘要: {match_data['excerpt']}\n")
        
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
            message = f"🎯 金工珠寶監控報告 ({taiwan_time})\n"
            message += f"發現 {len(matches)} 篇相關文章！\n\n"
            
            for i, match in enumerate(matches[:3], 1):  # 最多顯示 3 篇
                message += f"{i}. {match['title'][:40]}...\n"
                message += f"   📍 {match['forum_name']}\n"
                message += f"   🔗 {match['url']}\n"
                message += f"   🏷️ {', '.join(match['matched_keywords'][:3])}\n"
                message += f"   ❤️ {match['like_count']} 💬 {match['comment_count']}\n\n"
            
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
    
    def monitor_forum(self, forum, forum_name):
        """監控單個論壇"""
        print(f"\n📱 正在檢查 Dcard {forum_name}...")
        
        try:
            posts = self.get_dcard_posts(forum, limit=30)  # 減少請求量
            
            if not posts:
                print(f"⚠️ {forum_name} 沒有獲取到文章，跳過處理")
                return []
                
            processed_posts = self.get_processed_posts()
            matches = []
            
            print(f"📄 獲取到 {len(posts)} 篇文章，開始處理...")
            
            for post in posts:
                post_id = f"dcard_{forum}_{post['id']}"
                
                if post_id in processed_posts:
                    continue
                
                title = post.get('title', '')
                excerpt = post.get('excerpt', '')
                text = f"{title} {excerpt}"
                
                matched_keywords = self.check_keywords(text)
                
                if matched_keywords:
                    match_data = self.save_match(post, forum, forum_name, matched_keywords)
                    matches.append(match_data)
                
                self.save_processed_post(post_id)
                time.sleep(0.5)  # 避免請求過快
            
            print(f"✅ {forum_name} 完成，發現 {len(matches)} 篇匹配")
            return matches
            
        except Exception as e:
            print(f"❌ 監控 {forum_name} 失敗: {e}")
            traceback.print_exc()
            return []
    
    def generate_summary(self, all_matches):
        """生成執行摘要"""
        taiwan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        summary = {
            'execution_time': taiwan_time,
            'total_matches': len(all_matches),
            'matches_by_forum': {},
            'top_keywords': {},
            'matches': all_matches
        }
        
        # 統計各論壇
        for match in all_matches:
            forum = match['forum_name']
            summary['matches_by_forum'][forum] = summary['matches_by_forum'].get(forum, 0) + 1
        
        # 統計關鍵字
        for match in all_matches:
            for keyword in match['matched_keywords']:
                summary['top_keywords'][keyword] = summary['top_keywords'].get(keyword, 0) + 1
        
        # 保存摘要
        summary_file = os.path.join(self.results_dir, "latest_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # 也保存到根目錄方便查看
        root_summary = os.path.join(self.base_dir, "monitoring_summary.json")
        with open(root_summary, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"📊 摘要已保存: {summary_file}")
        return summary
    
    def run_monitoring(self):
        """執行監控任務"""
        start_time = datetime.now()
        print("🚀 開始金工珠寶監控任務")
        print(f"⏰ 開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 監控關鍵字: {len(self.keywords)} 個")
        
        forums = {
            'jewelry': '珠寶版',
            'marriage': '結婚版', 
            'girl': '女孩版'
        }
        
        all_matches = []
        
        for forum_key, forum_name in forums.items():
            try:
                matches = self.monitor_forum(forum_key, forum_name)
                all_matches.extend(matches)
                
                # 論壇間較長的間隔
                wait_time = random.uniform(5, 10)
                print(f"⏳ 等待 {wait_time:.1f} 秒後檢查下一個論壇...")
                time.sleep(wait_time)
                
            except Exception as e:
                print(f"❌ 處理 {forum_name} 時發生錯誤: {e}")
        
        # 生成摘要報告
        summary = self.generate_summary(all_matches)
        
        # 發送通知
        if all_matches:
            self.send_telegram_notification(all_matches)
        
        # 輸出結果
        end_time = datetime.now()
        duration = (end_time - start_time).seconds
        
        print(f"\n🎉 監控任務完成!")
        print(f"⏱️ 執行時間: {duration} 秒")
        print(f"📊 總計發現: {len(all_matches)} 篇匹配文章")
        
        if all_matches:
            print(f"🏆 各論壇匹配數:")
            for forum, count in summary['matches_by_forum'].items():
                print(f"   • {forum}: {count} 篇")
        else:
            print("✅ 本次未發現新的匹配文章")

def main():
    try:
        monitor = JewelryMonitor()
        monitor.run_monitoring()
    except Exception as e:
        print(f"❌ 程式執行失敗: {e}")
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()