import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter.ttk import Progressbar
from tqdm import tqdm

headers = {"User-Agent": "Mozilla/5.0"}

def get_soup(url):
    r = requests.get(url, headers=headers)
    r.encoding = r.apparent_encoding
    return BeautifulSoup(r.text, "html.parser")

def download_images(base_url, save_dir, log_widget, progress_bar):
    try:
        # Step 1: 获取所有子页面链接
        soup = get_soup(base_url)
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.endswith(".html") or "NO." in href:  # 筛选目标子页面
                links.append(urljoin(base_url, href))
        
        log_widget.insert(tk.END, f"找到 {len(links)} 个子页面\n")
        log_widget.see(tk.END)

        total_links = len(links)
        progress_bar["maximum"] = total_links

        # Step 2: 遍历子页面，下载其中的图片
        for idx, link in enumerate(links, 1):
            log_widget.insert(tk.END, f"\n正在处理子页面: {link}\n")
            log_widget.see(tk.END)
            subsoup = get_soup(link)

            # 以页面标题/文件名作为子文件夹
            folder_name = re.sub(r'[\\/*?:"<>|]', "_", link.split("/")[-1])
            save_path = os.path.join(save_dir, folder_name)
            os.makedirs(save_path, exist_ok=True)

            # 找到所有图片
            imgs = subsoup.find_all("img")
            img_urls = [urljoin(link, img["src"]) for img in imgs if img.get("src")]

            log_widget.insert(tk.END, f"  共找到 {len(img_urls)} 张图片\n")
            log_widget.see(tk.END)

            for i, img_url in enumerate(img_urls, 1):
                try:
                    resp = requests.get(img_url, headers=headers, stream=True, timeout=10)
                    resp.raise_for_status()
                    ext = os.path.splitext(img_url)[-1]
                    filename = os.path.join(save_path, f"{i:03d}{ext}")
                    with open(filename, "wb") as f:
                        for chunk in resp.iter_content(1024):
                            f.write(chunk)
                except Exception as e:
                    log_widget.insert(tk.END, f"下载失败 {img_url}: {e}\n")
                    log_widget.see(tk.END)

            progress_bar["value"] = idx
            progress_bar.update()

        messagebox.showinfo("完成", "所有图片下载完成！")
    except Exception as e:
        messagebox.showerror("错误", str(e))

# GUI 主界面
def start_gui():
    root = tk.Tk()
    root.title("批量图片下载器")
    root.geometry("700x500")

    tk.Label(root, text="请输入主页面 URL:").pack(anchor="w", padx=10, pady=5)
    url_entry = tk.Entry(root, width=80)
    url_entry.pack(padx=10, pady=5)

    tk.Label(root, text="选择保存目录:").pack(anchor="w", padx=10, pady=5)
    save_dir_var = tk.StringVar()

    def choose_dir():
        folder = filedialog.askdirectory()
        if folder:
            save_dir_var.set(folder)

    tk.Entry(root, textvariable=save_dir_var, width=60).pack(side="left", padx=10)
    tk.Button(root, text="浏览", command=choose_dir).pack(side="left")

    # 进度条
    progress_bar = Progressbar(root, length=600, mode="determinate")
    progress_bar.pack(pady=15)

    # 日志窗口
    log_widget = scrolledtext.ScrolledText(root, width=85, height=20)
    log_widget.pack(padx=10, pady=10)

    def start_download():
        url = url_entry.get().strip()
        save_dir = save_dir_var.get().strip()
        if not url or not save_dir:
            messagebox.showwarning("提示", "请填写 URL 并选择保存目录")
            return
        threading.Thread(target=download_images, args=(url, save_dir, log_widget, progress_bar), daemon=True).start()

    tk.Button(root, text="开始下载", command=start_download).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    start_gui()
