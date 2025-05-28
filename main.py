import os
import feedparser
import requests
import logging
import time
import re
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# โหลด environment variables
load_dotenv()
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not WEBHOOK_URL:
    raise ValueError("❌ ไม่พบ DISCORD_WEBHOOK_URL ใน .env")

# ตั้งค่าการ log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ตั้งค่าการ retry สำหรับ requests
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

# RSS Feed URLs
RSS_FEEDS = [
    
    "https://www.thairath.co.th/rss/news", # Thairath
    "https://www.matichon.co.th/feed", # Matichon
    "https://doh.go.th/rss/newsum", # กรมทางหลวง (Department of Highways)
    "https://rss.app/feeds/AZuuiVkf1deAllDc.xml", # Dailynews
    # "https://www.tmd.go.th/api/xml/region-daily-forecast?regionid=7", # กรมอุตุนิยมวิทยา กระทรวงดิจิทัลเพื่อเศรษฐกิจและสังคม


    # "https://www.dailynews.co.th/rss/feed/dn/feed.xml", # ไม่ได้ใช้งาน
    # "https://www.khaosod.co.th/rss.xml", # ไม่ได้ใช้งาน
    # "https://www.naewna.com/rss", # ไม่ได้ใช้งาน
    # "https://www.nationthailand.com/rss", # ไม่ได้ใช้งาน
    # "https://www.bangkokpost.com/rss/", # ไม่ได้ใช้งาน


    # "https://news.sanook.com/rss/",
    "https://rssfeeds.sanook.com/rss/feeds/sanook/news.index.xml",
    "https://rssfeeds.sanook.com/rss/feeds/sanook/news.politic.xml",
    "https://rssfeeds.sanook.com/rss/feeds/sanook/news.crime.xml",
    "https://rssfeeds.sanook.com/rss/feeds/sanook/hot.news.xml",


    # "https://www.prachachat.net/news-rss",
    "https://www.prachachat.net/feed",


    # "https://workpointnews.com/rss",
    "https://workpointnews.com/rss.crime.xml",
    "https://workpointnews.com/rss.politics.xml",
    "https://workpointnews.com/rss.society.xml",
    "https://workpointnews.com/rss.scoop.xml",
    "https://workpointnews.com/rss.disaster.xml",


    "https://news.thaipbs.or.th/rss/breakingnews.xml",
    "https://news.thaipbs.or.th/rss/politic.xml",
    "http://news.thaipbs.or.th/rss/economic.xml",
    "http://news.thaipbs.or.th/rss/social.xml",
    "https://news.thaipbs.or.th/rss/crime.xml",


    "https://news.google.com/rss/search?q=ถนนพระราม2&hl=th&gl=TH&ceid=TH:th",
    "https://news.google.com/rss/search?q=อัมรินทร์ทีวี&hl=th&gl=TH&ceid=TH:th",
    "https://news.google.com/rss/search?q=จราจร+พระราม2&hl=th&gl=TH&ceid=TH:th",
    "https://news.google.com/rss/search?q=js100+พระราม2&hl=th&gl=TH&ceid=TH:th",
    "https://news.google.com/rss/search?q=JS100Radio+พระราม2&hl=th&gl=TH&ceid=TH:th",
    "https://news.google.com/rss/search?q=อุบัติเหตุ+พระราม2&hl=th&gl=TH&ceid=TH:th",
    "https://news.google.com/rss/search?q=น้ำท่วม+พระราม2&hl=th&gl=TH&ceid=TH:th",

 
    "https://rss.xcancel.com/iWZRamaII/rss", #ศูนย์จัดการจราจรระหว่างก่อสร้าง พระราม 2 โครงการก่อสร้างทางหลวงพิเศษหมายเลข 82 ช่วงเอกชัย-บ้านแพ้ว
    "https://rss.xcancel.com/search/rss?f=tweets&q=JS100Radio",
    "https://rss.xcancel.com/fm91trafficpro/rss",
    "https://rss.xcancel.com/VoiceTVOfficial/rss",
    "https://rss.xcancel.com/thaich8news/rss",
    "https://rss.xcancel.com/3Plusnews/rss",
    "https://rss.xcancel.com/thestandardth/rss",
    "https://rss.xcancel.com/amarintvhd/rss",
    "https://rss.xcancel.com/PPTVHD36/rss",
    "https://rss.xcancel.com/MatichonOnline/rss",
    "https://rss.xcancel.com/MorningNewsTV3/rss",
    "https://rss.xcancel.com/KhaosodOnline/rss",
    "https://rss.xcancel.com/nationweekend/rss",
    "https://rss.xcancel.com/withyu_h/rss",
    "https://rss.xcancel.com/ThaiPBS/rss",
    "https://rss.xcancel.com/BangkokInsight/rss",
    "https://rss.xcancel.com/ThaiPBSNews/rss",
    "https://rss.xcancel.com/JKN18news/rss",
    "https://rss.xcancel.com/EJanNews/rss",
    "https://rss.xcancel.com/onenews31/rss",
    "https://rss.xcancel.com/MGROnlineLive/rss",
    "https://rss.xcancel.com/TNAMCOT/rss",
    "https://rss.xcancel.com/kcltv/rss",
    "https://rss.xcancel.com/SPRiNGNEWS_TH/rss",
    "https://rss.xcancel.com/tnnthailand/rss",
    "https://rss.xcancel.com/PostToday/rss",
    "https://rss.xcancel.com/thaipost/rss",
    "https://rss.xcancel.com/prachatai/rss",
    "https://rss.xcancel.com/kapookdotcom/rss",
    "https://rss.xcancel.com/wpnews23/rss",
    "https://rss.xcancel.com/DDPMNews/rss",
    "https://rss.xcancel.com/todayth/rss",
    "https://rss.xcancel.com/mthai/rss",
    "https://rss.xcancel.com/nnthotnews/rss",
    "https://rss.xcancel.com/nationstoryTH/rss",
    "https://rss.xcancel.com/INNNEWS/rss",
    "https://rss.xcancel.com/Traffic_1197V2/rss",

]

# คำค้นหาที่ใช้ regex เพิ่มความยืดหยุ่นขึ้นในการค้นหา
KEYWORDS_REGEX = [
    re.compile(r'พระราม\s*2'),
    re.compile(r'ถนน\s*พระราม\s*2'),
    re.compile(r'สะพาน\s*พระราม\s*2'),
    re.compile(r'จราจร\s*พระราม\s*2'),
    re.compile(r'ฝนตก\s*พระราม\s*2'),
    re.compile(r'อุบัติเหตุ\s*พระราม\s*2'),
    re.compile(r'น้ำท่วม\s*พระราม\s*2'),
    re.compile(r'รถติด\s*พระราม\s*2'),
    re.compile(r'อันตราย\s*พระราม\s*2'),

    # re.compile(r'น้ำท่วม'), #test
    # re.compile(r'อุบัติเหตุ'), #test
    # re.compile(r'ฝนตก') #test
]

SEEN_LINKS_FILE = "seen_links.txt"

# -------------------- Utility Functions --------------------
def load_seen_links():
    if not os.path.exists(SEEN_LINKS_FILE):
        return set()
    with open(SEEN_LINKS_FILE, "r", encoding="utf-8") as file:
        return set(line.strip() for line in file.readlines())

def save_seen_links(seen_links):
    MAX_LINKS = 1000
    trimmed_links = list(sorted(seen_links))[-MAX_LINKS:]
    with open(SEEN_LINKS_FILE, "w", encoding="utf-8") as file:
        file.write("\n".join(trimmed_links))

def escape_discord_markdown(text):
    return re.sub(r'([*_~`[\\]])', r'\\\\\1', text)

def extract_source(url):
    return urlparse(url).netloc.replace("www.", "")

def extract_image_url(entry):
    if "media_content" in entry and entry.media_content:
        return entry.media_content[0].get("url")
    if "image" in entry:
        return entry.image.get("href")
    return None

def hash_entry(entry):
    content = f"{entry.title}{entry.get('description', '')}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

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

    # payload = {"embeds": [embed]}

    try:
        response = session.post(WEBHOOK_URL, json={"embeds": [embed]})
        response.raise_for_status()
        logging.info(f"✅ ส่งแจ้งเตือนแล้ว: {title}")
    except requests.RequestException as e:
        logging.error(f"❌ ส่ง webhook ไม่สำเร็จ: {e}")

# -------------------- Main Logic --------------------
def main():
    logging.info(f"✅✅✅ Start-Time : {datetime.now()} ✅✅✅")
    seen_links = load_seen_links()
    updated_links = set()
    cutoff_time = datetime.now() - timedelta(days=5) # ใช้ค้นหาข่าวในช่วงเวลาที่ต้องการ EX. timedelta(days=5), timedelta(hours=24)
    # logging.info(f"✅ Date-Time ✅ = {datetime.now()}")

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            # logging.info(f"feed : {feed}")
            if feed.bozo:
                logging.warning(f"⚠️ Feed format error: {url} - {feed.bozo_exception}")
                continue

            for entry in feed.entries:
                title = entry.title
                description = entry.get("description", "")
                content = f"{title} {description}".lower()
                entry_link = entry.link
                entry_hash = hash_entry(entry)

                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    published_dt = datetime.fromtimestamp(time.mktime(published))
                    if published_dt < cutoff_time:
                        continue # ข้ามข่าวที่เก่าเกินไป

                if entry_link in seen_links or entry_hash in seen_links:
                    continue

                if any(regex.search(content) for regex in KEYWORDS_REGEX):
                    image_url = extract_image_url(entry)
                    send_discord_notification(title, entry_link, image_url)
                    updated_links.add(entry_link)
                    updated_links.add(entry_hash)

        except Exception as e:
            logging.error(f"⚠️ เกิดข้อผิดพลาดกับ RSS feed: {url} - {e}")

    if updated_links:
        seen_links.update(updated_links)
        save_seen_links(seen_links)
        logging.info(f"📝 บันทึกลิงก์ใหม่จำนวน {len(updated_links)} รายการแล้ว")

    else:
        logging.info("📭 ไม่พบข่าวใหม่ที่เกี่ยวข้อง")

    logging.info(f"✅✅✅ End-Process : {datetime.now()} ✅✅✅")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception(f"‼️ เกิดข้อผิดพลาดใน main(): {e}")
