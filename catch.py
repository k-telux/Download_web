import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm

# 主页面地址
BASE_URL = "https://yanxiangrong.github.io/chunmomo/%E8%A0%A2%E6%B2%AB%E6%B2%AB"

# 设置保存目录
SAVE_DIR = "chunmomo_downloads"
os.makedirs(SAVE_DIR, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0"
}

def get_soup(url):
    r = requests.get(url, headers=headers)
    r.encoding = r.apparent_encoding
    return BeautifulSoup(r.text, "html.parser")

# Step 1: 获取所有子页面链接
soup = get_soup(BASE_URL)
links = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if href.endswith(".html") or "NO." in href:  # 筛选目标子页面
        links.append(urljoin(BASE_URL, href))

print(f"找到 {len(links)} 个子页面")

# Step 2: 遍历子页面，下载其中的图片
for link in links:
    print(f"\n正在处理子页面: {link}")
    subsoup = get_soup(link)
    
    # 以页面标题/文件名作为子文件夹
    folder_name = re.sub(r'[\\/*?:"<>|]', "_", link.split("/")[-1])
    save_path = os.path.join(SAVE_DIR, folder_name)
    os.makedirs(save_path, exist_ok=True)
    
    # 找到所有图片
    imgs = subsoup.find_all("img")
    img_urls = [urljoin(link, img["src"]) for img in imgs if img.get("src")]
    
    # 下载
    for i, img_url in enumerate(tqdm(img_urls, desc="下载中", unit="图")):
        try:
            resp = requests.get(img_url, headers=headers, stream=True)
            resp.raise_for_status()
            ext = os.path.splitext(img_url)[-1]
            filename = os.path.join(save_path, f"{i+1:03d}{ext}")
            with open(filename, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
        except Exception as e:
            print(f"下载失败 {img_url}: {e}")
