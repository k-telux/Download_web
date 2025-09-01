import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter.ttk import Progressbar, Style

headers = {"User-Agent": "Mozilla/5.0"}

def get_soup(url):
    r = requests.get(url, headers=headers)
    r.encoding = r.apparent_encoding
    return BeautifulSoup(r.text, "html.parser")

def download_images(base_url, save_dir, log_widget, overall_bar, page_bar, root):
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
        overall_bar["maximum"] = total_links

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

            # 单页进度条设置
            page_bar["maximum"] = len(img_urls)
            page_bar["value"] = 0

            for i, img_url in enumerate(img_urls, 1):
                try:
                    resp = requests.get(img_url, headers=headers, stream=True, timeout=10)
                    resp.raise_for_status()
                    ext = os.path.splitext(img_url)[-1]
                    filename = os.path.join(save_path, f"{i:03d}{ext}")
                    with open(filename, "wb") as f:
                        for chunk in resp.iter_content(1024):
                            f.write(chunk)

                    # 更新单图进度
                    page_bar["value"] = i
                    root.update_idletasks()
                except Exception as e:
                    log_widget.insert(tk.END, f"下载失败 {img_url}: {e}\n")
                    log_widget.see(tk.END)

            # 更新总进度
            overall_bar["value"] = idx
            root.update_idletasks()

        messagebox.showinfo("完成", "所有图片下载完成！")
    except Exception as e:
        messagebox.showerror("错误", str(e))

# GUI 主界面
def start_gui():
    root = tk.Tk()
    root.title("📸 图片批量下载器")
    root.geometry("720x580")
    root.configure(bg="#F5F5F7")  # Apple 浅灰背景

    # macOS 风格
    style = Style()
    style.theme_use("clam")
    style.configure("TButton", font=("Helvetica", 12), padding=6, background="#E0E0E0", relief="flat")
    style.map("TButton", background=[("active", "#D0D0D0")])
    style.configure("TLabel", background="#F5F5F7", font=("Helvetica", 12))
    style.configure("TEntry", font=("Helvetica", 12))
    style.configure("Horizontal.TProgressbar", troughcolor="#E0E0E0", bordercolor="#E0E0E0", background="#007AFF", thickness=20)

    # 输入 URL
    tk.Label(root, text="🔗 主页面 URL:").pack(anchor="w", padx=15, pady=8)
    url_entry = tk.Entry(root, width=80, font=("Helvetica", 12))
    url_entry.pack(padx=15, pady=5)

    # 保存目录
    tk.Label(root, text="💾 保存目录:").pack(anchor="w", padx=15, pady=8)
    save_dir_var = tk.StringVar()

    frame_dir = tk.Frame(root, bg="#F5F5F7")
    frame_dir.pack(padx=15, pady=5, fill="x")
    tk.Entry(frame_dir, textvariable=save_dir_var, width=60, font=("Helvetica", 12)).pack(side="left", padx=5)
    tk.Button(frame_dir, text="选择", command=lambda: save_dir_var.set(filedialog.askdirectory())).pack(side="left")

    # 总体进度条
    tk.Label(root, text="📊 总体进度:").pack(anchor="w", padx=15, pady=5)
    overall_bar = Progressbar(root, length=650, mode="determinate", style="Horizontal.TProgressbar")
    overall_bar.pack(pady=5)

    # 单页进度条
    tk.Label(root, text="🖼 当前子页面进度:").pack(anchor="w", padx=15, pady=5)
    page_bar = Progressbar(root, length=650, mode="determinate", style="Horizontal.TProgressbar")
    page_bar.pack(pady=5)

    # 日志窗口
    tk.Label(root, text="📜 日志:").pack(anchor="w", padx=15, pady=5)
    log_widget = scrolledtext.ScrolledText(root, width=90, height=15, font=("Menlo", 10), bg="#FFFFFF", relief="flat")
    log_widget.pack(padx=15, pady=10)

    def start_download():
        url = url_entry.get().strip()
        save_dir = save_dir_var.get().strip()
        if not url or not save_dir:
            messagebox.showwarning("提示", "请填写 URL 并选择保存目录")
            return
        threading.Thread(
            target=download_images,
            args=(url, save_dir, log_widget, overall_bar, page_bar, root),
            daemon=True
        ).start()

    tk.Button(root, text="🚀 开始下载", command=start_download).pack(pady=15)

    root.mainloop()

if __name__ == "__main__":
    start_gui()
