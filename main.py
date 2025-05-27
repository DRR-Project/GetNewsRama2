import os
import feedparser
import requests
import logging
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# โหลด environment variables
load_dotenv()
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# ตรวจสอบว่า Webhook URL ถูกตั้งไว้
if not WEBHOOK_URL:
    raise ValueError("❌ ไม่พบ DISCORD_WEBHOOK_URL ใน .env")

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# RSS feeds หลายแหล่งข่าว
RSS_FEEDS = [
    # สำนักข่าวใหญ่
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
    
    # Google News
    # "https://news.google.com/rss?hl=th&gl=TH&ceid=TH:th", Google News กว้างเกินไป
    "https://news.google.com/rss/search?q=%E0%B8%96%E0%B8%99%E0%B8%99%E0%B8%9E%E0%B8%A3%E0%B8%B0%E0%B8%A3%E0%B8%B2%E0%B8%A1?2&hl=th&gl=TH&ceid=TH:th",
    "https://news.google.com/rss/search?q=%E0%B8%AD%E0%B8%A1%E0%B8%A3%E0%B8%B4%E0%B8%99%E0%B8%97%E0%B8%A3%E0%B9%8C%E0%B8%97%E0%B8%B5%E0%B8%A7%E0%B8%B5&hl=th&gl=TH&ceid=TH:th", #อมรินทร์ทีวี 
    "https://news.google.com/rss/search?q=%E0%B8%88%E0%B8%A3%E0%B8%B2%E0%B8%88%E0%B8%A3+%E0%B8%9E%E0%B8%A3%E0%B8%B0%E0%B8%A3%E0%B8%B2%E0%B8%A1?2&hl=th&gl=TH&ceid=TH:th", #จราจร+พระราม 2
    "https://news.google.com/rss/search?q=js100+%E0%B8%9E%E0%B8%A3%E0%B8%B0%E0%B8%A3%E0%B8%B2%E0%B8%A1?2&hl=th&gl=TH&ceid=TH:th", #js100+พระราม 2
    "https://news.google.com/rss/search?q=%E0%B8%AD%E0%B8%B8%E0%B8%9A%E0%B8%B1%E0%B8%95%E0%B8%B4%E0%B9%80%E0%B8%AB%E0%B8%95%E0%B8%B8+%E0%B8%9E%E0%B8%A3%E0%B8%B0%E0%B8%A3%E0%B8%B2%E0%B8%A1?2&hl=th&gl=TH&ceid=TH:th", #อุบัติเหตุ+พระราม 2
    "https://news.google.com/rss/search?q=%E0%B8%AD%E0%B8%B8%E0%B8%9A%E0%B8%B1%E0%B8%95%E0%B8%B4%E0%B9%80%E0%B8%AB%E0%B8%95%E0%B8%B8%E0%B8%9E%E0%B8%A3%E0%B8%B0%E0%B8%A3%E0%B8%B2%E0%B8%A1?2&hl=th&gl=TH&ceid=TH:th", #อุบัติเหตุพระราม 2
    "https://news.google.com/rss/search?q=%E0%B8%99%E0%B9%89%E0%B8%B3%E0%B8%97%E0%B9%88%E0%B8%A7%E0%B8%A1+%E0%B8%9E%E0%B8%A3%E0%B8%B0%E0%B8%A3%E0%B8%B2%E0%B8%A1?2&hl=th&gl=TH&ceid=TH:th", #น้ำท่วม+พระราม 2


   
]

# คำค้นหา
# KEYWORDS = ["พระราม 2", "พระราม 2 น้ำท่วม", "พระราม 2 อุบัติเหตุ", "น้ำท่วม พระราม 2", "อุบัติเหตุ พระราม 2", "ถนนพระราม 2"]
KEYWORDS = ["พระราม 2", "ถนนพระราม 2", "น้ำท่วม", "ฝนตก", "อุบัติเหตุ"]

# ไฟล์เก็บลิงก์ที่เคยแจ้งแล้ว
SEEN_LINKS_FILE = "seen_links.txt"


def load_seen_links():
    if not os.path.exists(SEEN_LINKS_FILE):
        return set()
    with open(SEEN_LINKS_FILE, "r", encoding="utf-8") as file:
        return set(line.strip() for line in file.readlines())


def save_seen_links(seen_links):
    MAX_LINKS = 1000  # ปรับได้ตามขนาดที่เหมาะสม
    trimmed_links = list(seen_links)[-MAX_LINKS:]
    with open(SEEN_LINKS_FILE, "w", encoding="utf-8") as file:
        file.write("\n".join(trimmed_links))


def send_discord_notification(title, link):
    # message = f"🛣️ พบข่าวเกี่ยวกับถนนพระราม 2:\n**{title}**\n{link}"
    # try:
    #     response = requests.post(WEBHOOK_URL, json={"content": message})
    #     response.raise_for_status()
    #     logging.info(f"✅ ส่งแจ้งเตือนแล้ว: {title}")
    # except requests.RequestException as e:
    #     logging.error(f"❌ ส่ง webhook ไม่สำเร็จ: {e}")
    
    embed = {
        "title": title,
        "url": link,
        "color": 0x00b0f4,
        "description": f"พบข่าวเกี่ยวกับถนนพระราม 2",
        "footer": {"text": "แจ้งเตือนอัตโนมัติจากระบบ"},
        "timestamp": datetime.utcnow().isoformat()
    }
    payload = {"embeds": [embed]}
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        logging.info(f"✅ ส่งแจ้งเตือนแล้ว: {title}")
    except requests.RequestException as e:
        logging.error(f"❌ ส่ง webhook ไม่สำเร็จ: {e}")


def main():
    seen_links = load_seen_links()
    updated_links = set()

    cutoff_time = datetime.utcnow() - timedelta(hours=48)  # ✅ ช่วงเวลาย้อนหลัง

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                description = entry.get("description", "")
                content = f"{title} {description}".lower()
                entry_link = entry.link

                # ✅ ตรวจสอบวันเวลาข่าว
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    published_dt = datetime.fromtimestamp(time.mktime(published))
                    if published_dt < cutoff_time:
                        logging.debug(f"⏱️ ข้ามข่าวเก่า: {title} ({published_dt.isoformat()})")
                        continue

                if entry_link in seen_links:
                    continue

                if any(keyword.lower() in content for keyword in KEYWORDS):
                    send_discord_notification(title, entry_link)
                    updated_links.add(entry_link)

        except Exception as e:
            logging.error(f"⚠️ เกิดข้อผิดพลาดกับ RSS feed: {url} - {e}")

    # รวมและบันทึกลิงก์ใหม่
    if updated_links:
        seen_links.update(updated_links)
        save_seen_links(seen_links)
        logging.info(f"📝 บันทึกลิงก์ใหม่จำนวน {len(updated_links)} รายการแล้ว")
    else:
        logging.info("📭 ไม่พบข่าวใหม่ที่เกี่ยวข้อง")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception(f"‼️ เกิดข้อผิดพลาดใน main(): {e}")
