import os
import feedparser
import requests
import logging
import time
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from urllib.parse import urlparse

# โหลด environment variables
load_dotenv()
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not WEBHOOK_URL:
    raise ValueError("❌ ไม่พบ DISCORD_WEBHOOK_URL ใน .env")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RSS_FEEDS = [
    "https://www.thairath.co.th/rss/news",
    "https://www.dailynews.co.th/rss/feed/dn/feed.xml",
    "https://www.khaosod.co.th/rss.xml",
    "https://www.matichon.co.th/feed",
    "https://www.naewna.com/rss",
    "https://news.sanook.com/rss/",
    "https://www.prachachat.net/news-rss",
    "https://workpointnews.com/rss",
    "https://www.bangkokpost.com/rss/",
    "https://doh.go.th/rss/newsum",
    "https://www.nationthailand.com/rss",
    "https://rss.app/feeds/AZuuiVkf1deAllDc.xml",
    "https://www.tmd.go.th/api/xml/region-daily-forecast?regionid=7",
    "https://news.google.com/rss/search?q=ถนนพระราม2&hl=th&gl=TH&ceid=TH:th",
    "https://news.google.com/rss/search?q=อัมรินทร์ทีวี&hl=th&gl=TH&ceid=TH:th",
    "https://news.google.com/rss/search?q=จราจร+พระราม2&hl=th&gl=TH&ceid=TH:th",
    "https://news.google.com/rss/search?q=js100+พระราม2&hl=th&gl=TH&ceid=TH:th",
    "https://news.google.com/rss/search?q=อุบัติเหตุ+พระราม2&hl=th&gl=TH&ceid=TH:th",
    "https://news.google.com/rss/search?q=น้ำท่วม+พระราม2&hl=th&gl=TH&ceid=TH:th",
]

# คำค้นหาที่ใช้ regex ยืดหยุ่นขึ้น
KEYWORDS_REGEX = [
    re.compile(r'พระราม\s*2'),
    re.compile(r'ถนน\s*พระราม\s*2'),
    re.compile(r'น้ำท่วม\s*พระราม\s*2'),
    re.compile(r'ฝนตก\s*พระราม\s*2'),
    re.compile(r'อุบัติเหตุ\s*พระราม\s*2'),
    
    re.compile(r'น้ำท่วม'), #test
    re.compile(r'อุบัติเหตุ'), #test
    re.compile(r'ฝนตก') #test
]

SEEN_LINKS_FILE = "seen_links.txt"

def load_seen_links():
    if not os.path.exists(SEEN_LINKS_FILE):
        return set()
    with open(SEEN_LINKS_FILE, "r", encoding="utf-8") as file:
        return set(line.strip() for line in file.readlines())

def save_seen_links(seen_links):
    MAX_LINKS = 1000
    trimmed_links = list(seen_links)[-MAX_LINKS:]
    with open(SEEN_LINKS_FILE, "w", encoding="utf-8") as file:
        file.write("\n".join(trimmed_links))

def escape_discord_markdown(text):
    return re.sub(r'([*_~`[\]])', r'\\\1', text)

def extract_source(url):
    return urlparse(url).netloc.replace("www.", "")

def extract_image_url(entry):
    if "media_content" in entry and entry.media_content:
        return entry.media_content[0].get("url")
    elif "image" in entry:
        return entry.image.get("href")
    return None

def send_discord_notification(title, link, image_url=None):
    source = extract_source(link)
    safe_title = escape_discord_markdown(title)

    embed = {
        "title": safe_title,
        "url": link,
        "color": 0x00b0f4,
        "description": f"**แหล่งข่าว**: {source}",
        "footer": {"text": "แจ้งเตือนจากระบบ RSS"},
        "timestamp": datetime.utcnow().isoformat()
    }

    if image_url:
        embed["image"] = {"url": image_url}

    payload = {"embeds": [embed]}

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        logging.info(f"✅ ส่งแจ้งเตือนแล้ว: {title}")
    except requests.RequestException as e:
        logging.error(f"❌ ส่ง webhook ไม่สำเร็จ: {e}")

def main():
    logging.info(f"✅✅✅ Start-Time : {datetime.now()}")
    seen_links = load_seen_links()
    updated_links = set()
    cutoff_time = datetime.now() - timedelta(days=10)
    # logging.info(f"✅⏱️⏱️ Time : {datetime.now()}")


    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                description = entry.get("description", "")
                content = f"{title} {description}".lower()
                entry_link = entry.link

                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    published_dt = datetime.fromtimestamp(time.mktime(published))
                    if published_dt < cutoff_time:
                        continue

                if entry_link in seen_links:
                    continue

                if any(regex.search(content) for regex in KEYWORDS_REGEX):
                    image_url = extract_image_url(entry)
                    send_discord_notification(title, entry_link, image_url)
                    updated_links.add(entry_link)

        except Exception as e:
            logging.error(f"⚠️ เกิดข้อผิดพลาดกับ RSS feed: {url} - {e}")

    if updated_links:
        seen_links.update(updated_links)
        save_seen_links(seen_links)
        logging.info(f"📝 บันทึกลิงก์ใหม่จำนวน {len(updated_links)} รายการแล้ว")
        logging.info(f"✅✅✅ End-Process : {datetime.now()}")

    else:
        logging.info("📭 ไม่พบข่าวใหม่ที่เกี่ยวข้อง")
        logging.info(f"✅✅✅ End-Process : {datetime.now()}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception(f"‼️ เกิดข้อผิดพลาดใน main(): {e}")
