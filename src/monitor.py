import requests
import json
import os
from datetime import datetime, timezone
import cloudscraper
import time
import traceback
import random
from urllib.parse import urlencode

class CloudflareBypasser:
    def __init__(self):
        # 嘗試多種不同的 cloudscraper 配置
        self.scrapers = []
        
        # 配置 1: Chrome + Windows
        scraper1 = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            },
            debug=False,
            delay=random.uniform(5, 10)
        )
        self.scrapers.append(('Chrome-Windows', scraper1))
        
        # 配置 2: Firefox + Linux
        scraper2 = cloudscraper.create_scraper(
            browser={
                'browser': 'firefox',
                'platform': 'linux',
                'mobile': False
            },
            debug=False
        )
        self.scrapers.append(('Firefox-Linux', scraper2))
        
        # 配置 3: Chrome + Mac
        scraper3 = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'darwin',
                'mobile': False
            },
            debug=False
        )
        self.scrapers.append(('Chrome-Mac', scraper3))
        
        # 配置 4: 手動設定 headers
        scraper4 = requests.Session()
        scraper4.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        self.scrapers.append(('Manual-Headers', scraper4))
        
        self.keywords = self.load_keywords()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.results_dir = os.path.join(self.base_dir, "results")
        self.ensure_results_dir()
        
        # Telegram 設定
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        print(f"🔧 初始化完成，準備了 {len(self.scrapers)} 種繞過方法")
        
    def load_keywords(self):
        return [
            "金工", "銀工", "手作金工", "金工教學", "金工課程", "金工工作室",
            "珠寶", "珠寶設計", "珠寶製作", "首飾", "首飾設計", "手作首飾",
            "鑲嵌", "寶石鑲嵌", "維修", "珠寶維修", "首飾維修", "改圍",
            "拋光", "電鍍", "焊接", "雕蠟", "鑄造",
            "K金", "18K", "14K", "白金", "黃金", "玫瑰金", "純銀", "925銀",
            "鑽石", "寶石", "翡翠", "珍珠", "紅寶石", "藍寶石", "祖母綠",
            "戒指", "項鍊", "手鍊", "耳環", "婚戒", "對戒", "求婚戒指", "情侶戒",
            "訂做", "客製", "訂製", "推薦", "分享", "評價", "開箱"
        ]
    
    def ensure_results_dir(self):
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
    
    def try_alternative_endpoints(self, forum):
        """嘗試不同的 API 端點"""
        endpoints = [
            f"https://www.dcard.tw/service/api/v2/forums/{forum}/posts",
            f"https://www.dcard.tw/_api/forums/{forum}/posts",  # 舊版 API
            f"https://dcard.tw/service/api/v2/forums/{forum}/posts"  # 無 www
        ]
        
        return endpoints
    
    def get_dcard_posts_with_multiple_methods(self, forum, limit=20):
        """使用多種方法嘗試獲取文章"""
        endpoints = self.try_alternative_endpoints(forum)
        
        for scraper_name, scraper in self.scrapers:
            print(f"🔄 使用 {scraper_name} 方法...")
            
            for endpoint in endpoints:
                try:
                    print(f"📡 嘗試端點: {endpoint}")
                    
                    # 隨機延遲
                    delay = random.uniform(3, 8)
                    print(f"⏳ 等待 {delay:.1f} 秒...")
                    time.sleep(delay)
                    
                    params = {
                        'limit': limit,
                        'popular': 'false'
                    }
                    
                    # 設定特定的 headers
                    if hasattr(scraper, 'headers'):
                        scraper.headers.update({
                            'Referer': f'https://www.dcard.tw/f/{forum}',
                            'Origin': 'https://www.dcard.tw',
                        })
                    
                    response = scraper.get(
                        endpoint,
                        params=params,
                        timeout=30,
                        allow_redirects=True
                    )
                    
                    print(f"📊 狀態碼: {response.status_code}")
                    print(f"📄 回應長度: {len(response.text)} 字元")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if isinstance(data, list) and len(data) > 0:
                                print(f"✅ 成功! 獲取 {len(data)} 篇文章")
                                return data
                            else:
                                print("⚠️ 回應格式不正確或為空")
                        except json.JSONDecodeError as e:
                            print(f"📄 JSON 解析失敗: {e}")
                            print(f"回應內容前 200 字元: {response.text[:200]}")
                    
                    elif response.status_code == 403:
                        print("🚫 403 Forbidden - 繼續嘗試其他方法")
                    else:
                        print(f"⚠️ 狀態碼 {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"🌐 網路錯誤: {e}")
                except Exception as e:
                    print(f"❌ 未知錯誤: {e}")
                
                # 每次嘗試後等待
                time.sleep(random.uniform(2, 5))
            
            # 每個 scraper 之間等待更長時間
            if scraper_name != self.scrapers[-1][0]:  # 不是最後一個
                wait_time = random.uniform(10, 15)
                print(f"⏳ 切換方法前等待 {wait_time:.1f} 秒...")
                time.sleep(wait_time)
        
        print(f"❌ 所有方法都失敗了，無法獲取 {forum} 版文章")
        return []
    
    def check_keywords(self, text):
        if not text:
            return []
        text_lower = text.lower()
        matched = []
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)
        return matched
    
    def save_match(self, post, forum, forum_name, keywords):
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
            'found_at': taiwan_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 保存到檔案
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
        
        summary_file = os.path.join(self.base_dir, "latest_matches.txt")
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"發現時間: {match_data['found_at']} (台灣時間)\n")
            f.write(f"平台: Dcard {forum_name}\n")
            f.write(f"標題: {match_data['title']}\n")
            f.write(f"網址: {url}\n")
            f.write(f"匹配關鍵字: {', '.join(keywords)}\n")
        
        print(f"✅ 保存匹配: {post.get('title', '')[:50]}...")
        return match_data
    
    def run_monitoring(self):
        start_time = datetime.now()
        print("🚀 開始多方法 Cloudflare 繞過監控")
        print(f"⏰ 開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        forums = {
            'jewelry': '珠寶版',
            'marriage': '結婚版',
            'girl': '女孩版'
        }
        
        all_matches = []
        successful_forums = 0
        
        for forum_key, forum_name in forums.items():
            print(f"\n{'='*60}")
            print(f"📱 開始處理 {forum_name}")
            print(f"{'='*60}")
            
            try:
                posts = self.get_dcard_posts_with_multiple_methods(forum_key, limit=20)
                
                if posts:
                    successful_forums += 1
                    print(f"🎉 {forum_name} 成功獲取 {len(posts)} 篇文章")
                    
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
                    print(f"✅ {forum_name} 處理完成，發現 {len(matches)} 篇匹配")
                else:
                    print(f"❌ {forum_name} 無法獲取文章")
                
            except Exception as e:
                print(f"❌ 處理 {forum_name} 時發生錯誤: {e}")
            
            # 論壇間等待
            if forum_key != list(forums.keys())[-1]:  # 不是最後一個論壇
                wait_time = random.uniform(15, 25)
                print(f"⏳ 等待 {wait_time:.1f} 秒後處理下一個論壇...")
                time.sleep(wait_time)
        
        # 結果摘要
        end_time = datetime.now()
        duration = (end_time - start_time).seconds
        
        print(f"\n{'='*60}")
        print(f"🎉 監控任務完成!")
        print(f"⏱️ 執行時間: {duration} 秒")
        print(f"📊 成功論壇: {successful_forums}/{len(forums)}")
        print(f"🎯 總匹配文章: {len(all_matches)} 篇")
        
        if all_matches:
            print(f"\n🏆 匹配結果:")
            for match in all_matches:
                print(f"• {match['forum_name']}: {match['title'][:40]}...")
        else:
            print("✅ 本次未發現匹配文章（或無法獲取文章）")
        
        # 保存摘要
        summary = {
            'execution_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'successful_forums': successful_forums,
            'total_forums': len(forums),
            'total_matches': len(all_matches),
            'matches': all_matches
        }
        
        summary_file = os.path.join(self.base_dir, "monitoring_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

def main():
    try:
        bypasser = CloudflareBypasser()
        bypasser.run_monitoring()
    except Exception as e:
        print(f"❌ 程式執行失敗: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()