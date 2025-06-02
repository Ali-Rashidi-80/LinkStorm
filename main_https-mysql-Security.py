import sys, os, json, asyncio, aiohttp, requests, re, logging, time, ssl
from urllib.parse import unquote
from PySide6 import QtCore, QtWidgets, QtGui, QtWebEngineWidgets
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QLineSeries, QValueAxis
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ============================
# API Data Fetching for App Info
# ============================
API_URL = 'https://rash32.ir/python/micropython/mysql_proxy_LinkStorm_app.php'
QUERY = "SELECT * FROM LinkStorm_app"

def fetch_data(url, query):
    payload = {'query': query}
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        response_data = response.json()
        if response_data.get('error'):
            raise ValueError(f"Server error: {response_data['error']}")
        return response_data['data']
    except (requests.RequestException, ValueError) as e:
        print(f"Error fetching data: {e}")
        return None

app_info_data = fetch_data(API_URL, QUERY)
if not app_info_data:
    print("Error fetching app information. Please check your internet connection and settings. The application will now exit.")
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.information(None, "Notification", "Error fetching app information. Please check your internet connection and settings. The application will now exit.")
    sys.exit(0)
# فیلتر کردن بر اساس state == '1'
filtered_info = [item for item in app_info_data if item.get('state') == '1']
if not filtered_info:
    print("The application state is inactive. You do not have permission to run this application. The application will now exit.")
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.information(None, "Notification", "The application state is inactive. You do not have permission to run this application. The application will now exit.")
    sys.exit(0)
app_info = filtered_info[0]  # استفاده از اولین رکورد با state == '1'
print("App info:", app_info)

# ============================
# Configuration and Logging
# ============================
LOG_FILE = "download_app.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()]
)

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "concurrent_downloads": 5,
    "chunk_size": 8192,
    "resume_downloads": True,
    "allowed_extensions": [".mp3", ".mp4", ".pdf", ".zip", ".rar", ".exe", ".msi"],
    "min_bitrate": "none",
    "max_retries": 7,
    "initial_backoff": 1,
    "download_folder": "",
    "language": "fa",
    "theme": "light",
    "multi_connection_parts": 8,
    "adaptive_threshold": 0.05
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            logging.info("Configuration loaded from config.json.")
            return config
        except Exception as e:
            logging.error(f"Error reading configuration: {e}")
    logging.info("Using default configuration.")
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        logging.info("Configuration saved to config.json.")
    except Exception as e:
        logging.error(f"Error saving configuration: {e}")

# ============================
# Translation (Bilingual)
# ============================
translations = {
    "fa": {
        "app_title": "دانلود یار",
        "download_tab": "دانلود",
        "settings_tab": "تنظیمات",
        "report_tab": "گزارش‌ها",
        "about_tab": "درباره",
        "add_url_placeholder": "یک یا چند آدرس (با جداکننده خط یا ,)",
        "add_btn": "افزودن",
        "reset_btn": "ریست",
        "remove_selected": "حذف",
        "clear_queue": "پاکسازی صف",
        "move_up": "بالا بردن",
        "move_down": "پایین بردن",
        "select_folder": "انتخاب پوشه",
        "start_download": "شروع دانلود",
        "stop_download": "توقف دانلود",
        "save_settings": "ذخیره تنظیمات",
        "update_cache": "بروزرسانی کش",
        "concurrent_downloads": "تعداد دانلودهای همزمان:",
        "chunk_size": "اندازه بسته (بایت):",
        "resume_downloads": "ادامه دانلود",
        "allowed_extensions": "پسوندهای مجاز (با , جدا شوند):",
        "min_bitrate": "بیت‌ریت (برای mp3):",
        "download_folder": "پوشه دانلود:",
        "language": "زبان:",
        "theme": "تم:",
        "day": "روز",
        "night": "شب",
        "report_title": "گزارش دانلود و آنالیتیکس",
        "duration": "مدت زمان (ثانیه)",
        "errors": "خطاها",
        "net_usage": "مصرف نت (MB)",
        "status": "وضعیت",
        "connection_status": "وضعیت اتصال",
        "pause": "توقف",
        "resume": "ادامه",
        "about_details": "جزئیات برنامه",
        "update_available": "نسخه جدید موجود است",
        "update_btn": "دانلود و بروزرسانی"
    },
    "en": {
        "app_title": "Link_Storm",
        "download_tab": "Downloads",
        "settings_tab": "Settings",
        "report_tab": "Reports",
        "about_tab": "About",
        "add_url_placeholder": "Enter one or more URLs (separated by newline or comma)",
        "add_btn": "Add",
        "reset_btn": "Reset",
        "remove_selected": "Remove",
        "clear_queue": "Clear Queue",
        "move_up": "Move Up",
        "move_down": "Move Down",
        "select_folder": "Select Folder",
        "start_download": "Start Download",
        "stop_download": "Stop Download",
        "save_settings": "Save Settings",
        "update_cache": "Update Cache",
        "concurrent_downloads": "Concurrent Downloads:",
        "chunk_size": "Chunk Size (bytes):",
        "resume_downloads": "Resume Downloads",
        "allowed_extensions": "Allowed Extensions (separated by ,):",
        "min_bitrate": "Minimum Bitrate (for mp3):",
        "download_folder": "Download Folder:",
        "language": "Language:",
        "theme": "Theme:",
        "day": "Day",
        "night": "Night",
        "report_title": "Download Reports and Analytics",
        "duration": "Duration (sec)",
        "errors": "Errors",
        "net_usage": "Net Usage (MB)",
        "status": "Status",
        "connection_status": "Connection Status",
        "pause": "Pause",
        "resume": "Resume",
        "about_details": "App Details",
        "update_available": "New version available",
        "update_btn": "Download & Update"
    }
}

def tr(key, lang):
    return translations.get(lang, translations["en"]).get(key, key)

# ============================
# Link Extraction Functions
# ============================
def advanced_filter_links(page_content, base_url, allowed_extensions, min_bitrate=None):
    pattern = r'href=[\'"]?([^\'" >]+)'
    raw_links = re.findall(pattern, page_content, re.IGNORECASE)
    valid_links = []
    for link in raw_links:
        full_link = requests.compat.urljoin(base_url, link)
        if not any(full_link.lower().endswith(ext) for ext in allowed_extensions):
            continue
        if full_link.lower().endswith(".mp3") and min_bitrate and min_bitrate != "none":
            if str(min_bitrate) not in full_link:
                continue
        valid_links.append(full_link)
    return valid_links

def extract_dynamic_links(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(3)
    page_source = driver.page_source
    driver.quit()
    return page_source

def extract_all_download_links(url, allowed_extensions, min_bitrate=None):
    try:
        page_content = requests.get(url, timeout=10, verify=True).text
    except Exception as e:
        logging.warning(f"Request error: {e}. Using Selenium.")
        page_content = extract_dynamic_links(url)
    return advanced_filter_links(page_content, url, allowed_extensions, min_bitrate)

# ============================
# Cache Management
# ============================
CACHE_FILE = "cache.json"
cache_data = {}

def load_cache_data():
    global cache_data
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            logging.info("Cache loaded from cache.json.")
        except Exception as e:
            logging.error(f"Error loading cache: {e}")
            cache_data = {}
    else:
        cache_data = {}

def save_cache_data():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=4)
        logging.info("Cache saved to cache.json.")
    except Exception as e:
        logging.error(f"Error saving cache: {e}")

def get_cached_page(url, force_update=False):
    if not force_update and url in cache_data:
        logging.info(f"Using cached data for {url}")
        return cache_data[url]
    try:
        resp = requests.get(url, timeout=10, verify=False)
        resp.raise_for_status()
        page_content = resp.text
    except Exception as e:
        logging.warning(f"Error fetching page {url}: {e}. Using Selenium.")
        page_content = extract_dynamic_links(url)
    cache_data[url] = page_content
    save_cache_data()
    return page_content

load_cache_data()

# ============================
# Multi-connection Download and Adaptive Chunking
# ============================
async def download_part(session, url, headers, file_path, start, end, adaptive_threshold, base_chunk):
    current_chunk = base_chunk
    downloaded = 0
    with open(file_path, "r+b") as f:
        f.seek(start)
    async with session.get(url, headers=headers, timeout=30) as resp:
        while True:
            t0 = time.time()
            chunk = await resp.content.read(current_chunk)
            t1 = time.time()
            if not chunk:
                break
            with open(file_path, "r+b") as f:
                f.seek(start + downloaded)
                f.write(chunk)
            downloaded += len(chunk)
            elapsed = t1 - t0
            if elapsed < adaptive_threshold:
                current_chunk = min(current_chunk * 2, 65536)
            elif elapsed > adaptive_threshold * 2:
                current_chunk = max(current_chunk // 2, 1024)
    return downloaded

async def multi_connection_download(session, url, file_path, parts, adaptive_threshold, base_chunk):
    try:
        head_resp = requests.head(url, timeout=5)
        head_resp.raise_for_status()
        total_size = int(head_resp.headers.get("Content-Length", 0))
    except Exception as e:
        raise Exception("Cannot get file size for multi-connection download.") from e
    part_size = total_size // parts
    with open(file_path, "wb") as f:
        f.truncate(total_size)
    tasks = []
    for i in range(parts):
        start = i * part_size
        end = total_size - 1 if i == parts - 1 else (start + part_size - 1)
        headers = {"Range": f"bytes={start}-{end}"}
        tasks.append(download_part(session, url, headers, file_path, start, end, adaptive_threshold, base_chunk))
    results = await asyncio.gather(*tasks)
    return sum(results)

# ============================
# DownloadWorker Class with Advanced Techniques and Resource Optimization
# ============================
class DownloadWorker(QtCore.QThread):
    progress_update = QtCore.Signal(str, int)
    file_complete = QtCore.Signal(str)
    file_error = QtCore.Signal(str, str)
    overall_progress = QtCore.Signal(int, int)
    log_message = QtCore.Signal(str)
    download_canceled = QtCore.Signal(str)
    all_downloads_complete = QtCore.Signal()

    def __init__(self, download_list, folder, config):
        super().__init__()
        self.download_list = download_list[:]  
        self.download_folder = folder
        self.config = config
        self.analytics = {}  
        self.cancel_flags = {}
        self.pause_flags = {}

    def cancel_download(self, file_name):
        self.cancel_flags[file_name] = True
        self.log_message.emit(f"Cancel request received for {file_name}.")
        logging.info(f"Cancel download: {file_name}")

    def pause_resume_download(self, file_name):
        current = self.pause_flags.get(file_name, False)
        self.pause_flags[file_name] = not current
        action = tr("pause", self.config.get("language", "en")) if not current else tr("resume", self.config.get("language", "en"))
        self.log_message.emit(f"{action} requested for {file_name}.")
        logging.info(f"{action} download: {file_name}")

    def run(self):
        asyncio.run(self.process_downloads())

    async def process_downloads(self):
        total = len(self.download_list)
        self.overall_progress.emit(0, total)
        ssl_context = ssl.create_default_context()
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            tasks = [self.download_file(session, url, idx, total) for idx, url in enumerate(self.download_list, start=1)]
            await asyncio.gather(*tasks)
        self.log_message.emit("All downloads completed.")
        logging.info("All downloads completed.")
        self.all_downloads_complete.emit()

    async def download_file(self, session, url, idx, total):
        allowed_extensions = self.config.get("allowed_extensions", DEFAULT_CONFIG["allowed_extensions"])
        min_bitrate = self.config.get("min_bitrate", DEFAULT_CONFIG["min_bitrate"])
        max_retries = self.config.get("max_retries", DEFAULT_CONFIG["max_retries"])
        initial_backoff = self.config.get("initial_backoff", DEFAULT_CONFIG["initial_backoff"])
        multi_parts = self.config.get("multi_connection_parts", 4)
        adaptive_threshold = self.config.get("adaptive_threshold", 0.05)
        base_chunk = self.config.get("chunk_size", 8192)

        if not any(url.lower().endswith(ext) for ext in allowed_extensions):
            links = extract_all_download_links(url, allowed_extensions, min_bitrate)
            if links:
                for link in links:
                    file_name = unquote(os.path.basename(link.split("?")[0]))
                    if file_name not in self.parent().added_file_names:
                        self.download_list.append(link)
                        self.parent().queue_list.addItem(link)
                        self.parent().add_progress_row(link)
                        self.parent().added_file_names.add(file_name)
                        self.log_message.emit(f"Added to queue: {link}")
                return
            else:
                self.log_message.emit(f"No downloadable file found on {url}.")
                logging.warning(f"No downloadable file found on {url}.")
                return

        original_file_name = unquote(os.path.basename(url.split("?")[0]))
        self.analytics[original_file_name] = {"start": time.time(), "end": None, "errors": 0, "downloaded_bytes": 0, "status": "Running"}
        file_name = original_file_name
        file_path = os.path.join(self.download_folder, file_name)
        
        use_multi = False
        total_size = None
        try:
            head_resp = requests.head(url, timeout=5)
            head_resp.raise_for_status()
            total_size = int(head_resp.headers.get("Content-Length", 0))
            if total_size and total_size > 10 * 1024 * 1024:
                use_multi = True
        except Exception as e:
            logging.warning(f"HEAD check failed for {file_name}: {e}")
        
        resume_header = {}
        mode = "wb"
        existing_size = 0
        if self.config.get("resume_downloads", True) and os.path.exists(file_path):
            existing_size = os.path.getsize(file_path)
            if total_size and existing_size >= total_size:
                self.log_message.emit(f"File {file_name} already downloaded; skipping.")
                self.analytics[original_file_name]["status"] = "Completed"
                self.analytics[original_file_name]["end"] = time.time()
                self.progress_update.emit(file_name, 100)
                return
            resume_header = {"Range": f"bytes={existing_size}-"}
            mode = "ab"
            self.log_message.emit(f"Resuming download of {file_name} from {existing_size} bytes.")
            logging.info(f"Resuming download of {file_name} from {existing_size} bytes.")
        
        retry_count = 0
        backoff = initial_backoff
        downloaded = existing_size

        if use_multi and total_size:
            try:
                downloaded = await multi_connection_download(session, url, file_path, multi_parts, adaptive_threshold, base_chunk)
                self.progress_update.emit(file_name, 100)
                self.file_complete.emit(file_name)
                self.analytics[original_file_name]["downloaded_bytes"] = downloaded
                self.analytics[original_file_name]["status"] = "Completed"
                self.analytics[original_file_name]["end"] = time.time()
                self.log_message.emit(f"Download completed (multi-connection): {file_name}")
                logging.info(f"Download completed (multi-connection): {file_name}")
                return
            except Exception as e:
                self.log_message.emit(f"Multi-connection download failed for {file_name}: {e}")
                logging.warning(f"Multi-connection download failed for {file_name}: {e}")
        
        while retry_count <= max_retries:
            try:
                ssl_context = ssl.create_default_context()  # Creating an SSL context for secure connections.
                ssl_context.check_hostname = False  # This disables hostname checking if needed, though you can set it to True for security.
                async with session.get(url, headers=resume_header, timeout=30, ssl=ssl_context) as resp:
                    if resp.status not in [200, 206]:
                        raise Exception(f"HTTP response {resp.status}")
                    total_chunk = resp.headers.get("Content-Length")
                    try:
                        total_chunk = int(total_chunk) + existing_size if total_chunk else None
                    except Exception as e:
                        total_chunk = None
                        logging.error(f"Error calculating total_size for {file_name}: {e}")
                    while True:
                        while self.pause_flags.get(file_name, False):
                            await asyncio.sleep(1)
                        if self.cancel_flags.get(file_name, False):
                            self.log_message.emit(f"Download canceled for {file_name}.")
                            logging.info(f"Download canceled: {file_name}")
                            self.analytics[original_file_name]["status"] = "Canceled"
                            self.analytics[original_file_name]["end"] = time.time()
                            self.download_canceled.emit(file_name)
                            return
                        t0 = time.time()
                        chunk = await resp.content.read(base_chunk)
                        t1 = time.time()
                        if not chunk:
                            break
                        try:
                            with open(file_path, mode) as f:
                                f.write(chunk)
                        except PermissionError as pe:
                            self.log_message.emit(f"Permission denied for {file_name}.")
                            logging.error(f"Permission denied for {file_name}: {pe}")
                            raise Exception("Permission denied. Check file access rights.")
                        downloaded += len(chunk)
                        self.analytics[original_file_name]["downloaded_bytes"] = downloaded
                        percent = int((downloaded / total_chunk) * 100) if total_chunk else 0
                        self.progress_update.emit(file_name, percent)
                        elapsed = t1 - t0
                        if elapsed < adaptive_threshold:
                            base_chunk = min(base_chunk * 2, 65536)
                        elif elapsed > adaptive_threshold * 2:
                            base_chunk = max(base_chunk // 2, 1024)
                        mode = "ab"
                self.file_complete.emit(file_name)
                self.analytics[original_file_name]["status"] = "Completed"
                self.analytics[original_file_name]["end"] = time.time()
                self.log_message.emit(f"Download completed: {file_name}")
                logging.info(f"Download completed: {file_name}")
                break
            except Exception as e:
                retry_count += 1
                self.analytics[original_file_name]["errors"] += 1
                error_msg = f"Error downloading {file_name}: {e}"
                if retry_count <= max_retries:
                    msg = f"{error_msg} - Retrying {retry_count} of {max_retries} after {backoff} sec."
                    self.log_message.emit(msg)
                    logging.warning(msg)
                    await asyncio.sleep(backoff)
                    backoff *= 2
                else:
                    self.file_error.emit(file_name, error_msg)
                    self.log_message.emit(error_msg)
                    logging.error(error_msg)
            self.overall_progress.emit(idx, total)

# ============================
# MainWindow Class with About Tab and UI Enhancements
# ============================
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self.language = self.config_data.get("language", "en")
        self.theme = self.config_data.get("theme", "dark")
        self.setWindowTitle(tr("app_title", self.language))
        self.resize(1100, 850)
        self.download_folder = self.config_data.get("download_folder", "")
        self.download_list = []
        self.worker = None
        self.added_file_names = set()
        self.about_data = app_info  # اطلاعات واکشی شده از API
        self.setup_ui()
        self.apply_theme()
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon("icon.png"))
        self.tray_icon.show()

    def show_notification(self, title, message):
        self.tray_icon.showMessage(title, message, QtGui.QIcon("icon.png"), 3000)

    def setup_ui(self):
        self.tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs)
        # Downloads Tab
        self.download_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.download_tab, tr("download_tab", self.language))
        self.setup_download_tab()
        # Settings Tab
        self.settings_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.settings_tab, tr("settings_tab", self.language))
        self.setup_settings_tab()
        # Reports Tab
        self.report_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.report_tab, tr("report_tab", self.language))
        self.setup_report_tab()
        # About Tab
        self.about_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.about_tab, tr("about_tab", self.language))
        self.setup_about_tab()

    def setup_download_tab(self):
        layout = QtWidgets.QVBoxLayout(self.download_tab)
        title = QtWidgets.QLabel(tr("app_title", self.language))
        title.setFont(QtGui.QFont("Segoe UI", 18, QtGui.QFont.Bold))
        layout.addWidget(title)

        # ایجاد لایه برای دکمه‌ها
        input_layout = QtWidgets.QHBoxLayout()
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText(tr("add_url_placeholder", self.language))
        self.url_input.setMinimumHeight(30)
        input_layout.addWidget(self.url_input)

        # دکمه افزودن
        add_btn = QtWidgets.QPushButton(tr("add_btn", self.language))
        add_btn.setMinimumHeight(30)
        add_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        add_btn.clicked.connect(self.add_url)
        input_layout.addWidget(add_btn)

        # دکمه ریست
        reset_btn = QtWidgets.QPushButton(tr("reset_btn", self.language))
        reset_btn.setMinimumHeight(30)
        reset_btn.setStyleSheet("background-color: #F44336; color: white;")
        reset_btn.clicked.connect(self.reset_download_tab)
        input_layout.addWidget(reset_btn)
        # دکمه کپی تمام لینک‌ها
        copy_all_btn = QtWidgets.QPushButton("کپی تمام لینک‌ها")
        copy_all_btn.setMinimumHeight(30)
        copy_all_btn.setStyleSheet("background-color: #2196F3; color: white;")
        copy_all_btn.clicked.connect(self.copy_all_links_to_clipboard)
        input_layout.addWidget(copy_all_btn)


        layout.addLayout(input_layout)

        # لیست صف دانلود
        self.queue_list = QtWidgets.QListWidget()
        self.queue_list.setStyleSheet("font-size: 14px;")
        self.queue_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.queue_list.customContextMenuRequested.connect(self.show_list_context_menu)
        layout.addWidget(self.queue_list)

        # جدول پیشرفت دانلود
        self.progress_table = QtWidgets.QTableWidget(0, 6)
        self.progress_table.setHorizontalHeaderLabels([
            tr("app_title", self.language),
            tr("duration", self.language),
            tr("errors", self.language),
            tr("net_usage", self.language),
            tr("status", self.language),
            "Action"
        ])
        self.progress_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.progress_table.setStyleSheet("font-size: 13px; background-color: #f5f5f5;")
        layout.addWidget(self.progress_table)

        # نوار پیشرفت کلی
        self.overall_progress_bar = QtWidgets.QProgressBar()
        self.overall_progress_bar.setStyleSheet("QProgressBar::chunk {background-color: #2196F3;} QProgressBar {font-size: 14px;}")
        layout.addWidget(self.overall_progress_bar)

        # بخش گزارش
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.log_text)

        # دکمه‌های شروع و توقف دانلود
        btn_layout = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton(tr("start_download", self.language))
        self.start_button.setStyleSheet("background-color: #FF5722; color: white; font-size: 14px;")
        self.start_button.clicked.connect(self.start_download_with_message)
        btn_layout.addWidget(self.start_button)

        self.stop_button = QtWidgets.QPushButton(tr("stop_download", self.language))
        self.stop_button.setStyleSheet("background-color: #9E9E9E; color: white; font-size: 14px;")
        self.stop_button.clicked.connect(self.stop_download)
        btn_layout.addWidget(self.stop_button)

        layout.addLayout(btn_layout)

    def copy_all_links_to_clipboard(self):
        # استخراج تمام لینک‌ها از صف دانلود
        all_links = [self.queue_list.item(i).text() for i in range(self.queue_list.count())]
        
        if all_links:
            # تبدیل لیست لینک‌ها به یک رشته با جداکننده‌ی خط
            links_text = "\n".join(all_links)
            
            # کپی کردن متن به کلیپ‌بورد
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(links_text)
            
            self.log("تمام لینک‌ها به کلیپ‌بورد کپی شدند.")
            QtWidgets.QMessageBox.information(self, "کپی لینک‌ها", "تمام لینک‌ها به کلیپ‌بورد کپی شدند.")
        else:
            QtWidgets.QMessageBox.warning(self, "خطا", "هیچ لینکی برای کپی کردن وجود ندارد.")



    def show_list_context_menu(self, pos):
        menu = QtWidgets.QMenu()
        remove_action = menu.addAction(tr("remove_selected", self.language))
        action = menu.exec_(self.queue_list.mapToGlobal(pos))
        if action == remove_action:
            selected_items = self.queue_list.selectedItems()
            if selected_items:
                for item in selected_items:
                    row = self.queue_list.row(item)
                    file_name = unquote(os.path.basename(item.text().split("?")[0]))
                    if file_name in self.added_file_names:
                        self.added_file_names.remove(file_name)
                    self.download_list.pop(row)
                    self.queue_list.takeItem(row)
                    self.progress_table.removeRow(row)
                    self.log(f"Removed from queue: {item.text()}")

    def setup_settings_tab(self):
        layout = QtWidgets.QFormLayout(self.settings_tab)
        self.concurrent_input = QtWidgets.QLineEdit(str(self.config_data.get("concurrent_downloads", 5)))
        layout.addRow(tr("concurrent_downloads", self.language), self.concurrent_input)
        self.chunk_input = QtWidgets.QLineEdit(str(self.config_data.get("chunk_size", 8192)))
        layout.addRow(tr("chunk_size", self.language), self.chunk_input)
        self.resume_checkbox = QtWidgets.QCheckBox(tr("resume_downloads", self.language))
        self.resume_checkbox.setChecked(self.config_data.get("resume_downloads", True))
        layout.addRow(self.resume_checkbox)
        self.extensions_input = QtWidgets.QLineEdit(", ".join(self.config_data.get("allowed_extensions", DEFAULT_CONFIG["allowed_extensions"])))
        layout.addRow(tr("allowed_extensions", self.language), self.extensions_input)
        self.bitrate_combo = QtWidgets.QComboBox()
        self.bitrate_combo.addItem("none", "none")
        self.bitrate_combo.addItem("128", "128")
        self.bitrate_combo.addItem("320", "320")
        default_bitrate = self.config_data.get("min_bitrate", DEFAULT_CONFIG["min_bitrate"])
        index = self.bitrate_combo.findData(default_bitrate)
        if index >= 0:
            self.bitrate_combo.setCurrentIndex(index)
        allowed_exts = [ext.strip().lower() for ext in self.extensions_input.text().split(",")]
        self.bitrate_combo.setVisible(".mp3" in allowed_exts)
        layout.addRow(tr("min_bitrate", self.language), self.bitrate_combo)
        folder_layout = QtWidgets.QHBoxLayout()
        self.folder_display = QtWidgets.QLineEdit(self.config_data.get("download_folder", ""))
        self.folder_display.setReadOnly(True)
        folder_layout.addWidget(self.folder_display)
        folder_btn = QtWidgets.QPushButton(tr("select_folder", self.language))
        folder_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(folder_btn)
        layout.addRow(tr("download_folder", self.language), folder_layout)
        self.language_combo = QtWidgets.QComboBox()
        self.language_combo.addItem("فارسی", "fa")
        self.language_combo.addItem("English", "en")
        current_lang = self.config_data.get("language", "en")
        index = self.language_combo.findData(current_lang)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        layout.addRow(tr("language", self.language), self.language_combo)
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItem(tr("night", self.language), "dark")
        self.theme_combo.addItem(tr("day", self.language), "light")
        current_theme = self.config_data.get("theme", "dark")
        index = self.theme_combo.findData(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        layout.addRow(tr("theme", self.language), self.theme_combo)
        save_btn = QtWidgets.QPushButton(tr("save_settings", self.language))
        save_btn.setStyleSheet("background-color: #009688; color: white;")
        save_btn.clicked.connect(self.save_settings)
        layout.addRow(save_btn)
        update_cache_btn = QtWidgets.QPushButton(tr("update_cache", self.language))
        update_cache_btn.setStyleSheet("background-color: #607D8B; color: white;")
        update_cache_btn.clicked.connect(self.update_cache)
        layout.addRow(update_cache_btn)

    def setup_report_tab(self):
        layout = QtWidgets.QVBoxLayout(self.report_tab)
        title = QtWidgets.QLabel(tr("report_title", self.language))
        title.setFont(QtGui.QFont("Segoe UI", 16, QtGui.QFont.Bold))
        layout.addWidget(title)
        self.report_table = QtWidgets.QTableWidget(0, 5)
        self.report_table.setHorizontalHeaderLabels([tr("app_title", self.language), tr("duration", self.language), tr("errors", self.language), tr("net_usage", self.language), tr("status", self.language)])
        self.report_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.report_table.setStyleSheet("font-size: 13px; background-color: #ffffff; color: #333333;")
        self.report_table.setMouseTracking(True)
        layout.addWidget(self.report_table)
        refresh_btn = QtWidgets.QPushButton("Refresh Report")
        refresh_btn.setStyleSheet("background-color: #3F51B5; color: white;")
        refresh_btn.clicked.connect(self.update_report)
        layout.addWidget(refresh_btn)

    def setup_about_tab(self):
        layout = QtWidgets.QVBoxLayout(self.about_tab)
        title = QtWidgets.QLabel(tr("about_tab", self.language))
        title.setFont(QtGui.QFont("Segoe UI", 16, QtGui.QFont.Bold))
        layout.addWidget(title)
        self.about_browser = QtWidgets.QTextBrowser()
        about_html = f"""
        <html>
        <head>
        <style>
            body {{ font-family: 'Segoe UI'; font-size: 14px; background-color: transparent; color: inherit; }}
            h2 {{ color: #2196F3; }}
            p {{ margin: 8px 0; }}
            .label {{ font-weight: bold; }}
        </style>
        </head>
        <body>
        <h2>{tr('about_details', self.language)}</h2>
        <p><span class="label">Version:</span> {self.about_data.get('App_version','N/A')}</p>
        <p><span class="label">Update Details:</span> {self.about_data.get('App_update_details','No update details available.')}</p>
        <p><span class="label">Update Link:</span> {self.about_data.get('App_update_link','No update link available.')}</p>
        </body>
        </html>
        """
        self.about_browser.setHtml(about_html)
        layout.addWidget(self.about_browser)
        update_link = self.about_data.get("App_update_link", "").strip()
        if update_link:
            self.update_button = QtWidgets.QPushButton(tr("update_btn", self.language))
            self.update_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
            self.update_button.clicked.connect(self.open_update_link)
            layout.addWidget(self.update_button)

    def open_update_link(self):
        link = self.about_data.get("App_update_link", "").strip()
        if link:
            QDesktopServices.openUrl(QUrl(link))
        else:
            QtWidgets.QMessageBox.information(self, "Info", "No update link available.")

    def select_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, tr("select_folder", self.language))
        if folder:
            self.download_folder = folder
            self.folder_display.setText(folder)
            self.log(f"Download folder selected: {folder}")

    def reset_download_tab(self):
        self.download_list.clear()
        self.queue_list.clear()
        self.progress_table.setRowCount(0)
        self.added_file_names.clear()
        self.log("Download tab has been reset.")

    def add_progress_row(self, url):
        file_name = unquote(os.path.basename(url.split("?")[0]))
        row = self.progress_table.rowCount()
        self.progress_table.insertRow(row)
        name_item = QtWidgets.QTableWidgetItem(file_name)
        name_item.setToolTip(file_name)
        progress_item = QtWidgets.QTableWidgetItem("0%")
        progress_item.setTextAlignment(QtCore.Qt.AlignCenter)
        progress_item.setToolTip("0%")
        self.progress_table.setItem(row, 0, name_item)
        self.progress_table.setItem(row, 1, progress_item)
        net_item = QtWidgets.QTableWidgetItem("0")
        net_item.setTextAlignment(QtCore.Qt.AlignCenter)
        net_item.setToolTip("0")
        self.progress_table.setItem(row, 2, net_item)
        status_item = QtWidgets.QTableWidgetItem("Running")
        status_item.setTextAlignment(QtCore.Qt.AlignCenter)
        status_item.setToolTip("Running")
        self.progress_table.setItem(row, 4, status_item)
        action_widget = QtWidgets.QWidget()
        action_layout = QtWidgets.QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0,0,0,0)
        pause_btn = QtWidgets.QPushButton(tr("pause", self.language))
        pause_btn.setStyleSheet("background-color: #FFC107; color: black;")
        pause_btn.clicked.connect(lambda ch, fn=unquote(os.path.basename(url.split("?")[0])), btn=pause_btn: self.toggle_pause(fn, btn))
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #F44336; color: white;")
        cancel_btn.clicked.connect(lambda ch, fn=unquote(os.path.basename(url.split("?")[0])): self.cancel_download(fn))
        delete_btn = QtWidgets.QPushButton(tr("remove_selected", self.language))
        delete_btn.setStyleSheet("background-color: #9C27B0; color: white;")
        delete_btn.clicked.connect(lambda ch, fn=unquote(os.path.basename(url.split("?")[0])): self.delete_row(fn))
        action_layout.addWidget(pause_btn)
        action_layout.addWidget(cancel_btn)
        action_layout.addWidget(delete_btn)
        self.progress_table.setCellWidget(row, 5, action_widget)

    def delete_row(self, file_name):
        # اگر دانلود در حال انجام است، لغو شود
        if self.worker:
            self.worker.cancel_download(file_name)
        # حذف ردیف از جدول و لیست
        for row in range(self.progress_table.rowCount()):
            if self.progress_table.item(row, 0).text() == file_name:
                self.progress_table.removeRow(row)
                break
        # حذف از لیست دانلود و لیست نمایش
        for i in range(self.queue_list.count()):
            if self.queue_list.item(i).text() == file_name:
                self.queue_list.takeItem(i)
                break
        if file_name in self.added_file_names:
            self.added_file_names.remove(file_name)
        # همچنین از download_list حذف شود (با توجه به ترتیب ممکن است نیاز به تطبیق ایندکس داشته باشد)
        self.download_list = [url for url in self.download_list if unquote(os.path.basename(url.split("?")[0])) != file_name]
        self.log(f"Deleted from queue: {file_name}")

    def toggle_pause(self, file_name, btn):
        if self.worker:
            self.worker.pause_resume_download(file_name)
            current_text = btn.text()
            if current_text == tr("pause", self.language):
                btn.setText(tr("resume", self.language))
                self.log(f"Paused: {file_name}")
                self.show_notification("Paused", f"Download paused: {file_name}")
            else:
                btn.setText(tr("pause", self.language))
                self.log(f"Resumed: {file_name}")
                self.show_notification("Resumed", f"Download resumed: {file_name}")

    def update_progress_row(self, file_name, percent):
        for row in range(self.progress_table.rowCount()):
            if self.progress_table.item(row, 0).text() == file_name:
                self.progress_table.item(row, 1).setText(f"{percent}%")
                self.animate_row(row)
                break

    def animate_row(self, row):
        for col in range(self.progress_table.columnCount()):
            item = self.progress_table.item(row, col)
            if item:
                item.setBackground(QtGui.QColor(144, 238, 144))
        QtCore.QTimer.singleShot(500, lambda: self.clear_row_color(row))

    def clear_row_color(self, row):
        if self.theme == "dark":
            bg_color = QtGui.QColor("#3c3f41")
        else:
            bg_color = QtGui.QColor("#ffffff")
        for col in range(self.progress_table.columnCount()):
            item = self.progress_table.item(row, col)
            if item:
                item.setBackground(bg_color)

    def cancel_download(self, file_name):
        if self.worker:
            self.worker.cancel_download(file_name)
            for row in range(self.progress_table.rowCount()):
                if self.progress_table.item(row, 0).text() == file_name:
                    widget = self.progress_table.cellWidget(row, 5)
                    if widget:
                        for btn in widget.findChildren(QtWidgets.QPushButton):
                            btn.setEnabled(False)
                    break

    def add_url(self):
        urls_text = self.url_input.text().strip()
        if urls_text:
            urls = [u.strip() for u in urls_text.replace(",", "\n").split("\n") if u.strip()]
            for url in urls:
                item = QtWidgets.QListWidgetItem(url)
                item.setToolTip(url)
                if not any(url.lower().endswith(ext) for ext in self.config_data.get("allowed_extensions", DEFAULT_CONFIG["allowed_extensions"])):
                    links = extract_all_download_links(url, self.config_data.get("allowed_extensions", DEFAULT_CONFIG["allowed_extensions"]), self.config_data.get("min_bitrate", DEFAULT_CONFIG["min_bitrate"]))
                    if links:
                        for link in links:
                            file_name = unquote(os.path.basename(link.split("?")[0]))
                            if file_name not in self.added_file_names:
                                self.download_list.append(link)
                                self.queue_list.addItem(QtWidgets.QListWidgetItem(link))
                                self.add_progress_row(link)
                                self.added_file_names.add(file_name)
                                self.log(f"Added to queue: {link}")
                    else:
                        self.log(f"No downloadable file found on {url}.")
                else:
                    file_name = unquote(os.path.basename(url.split("?")[0]))
                    if file_name not in self.added_file_names:
                        self.download_list.append(url)
                        self.queue_list.addItem(item)
                        self.add_progress_row(url)
                        self.added_file_names.add(file_name)
                        self.log(f"Added to queue: {url}")
            self.download_list.sort(key=lambda x: unquote(os.path.basename(x.split("?")[0])).lower())
            items = [self.queue_list.item(i).text() for i in range(self.queue_list.count())]
            items.sort(key=lambda x: unquote(os.path.basename(x.split("?")[0])).lower())
            self.queue_list.clear()
            for text in items:
                list_item = QtWidgets.QListWidgetItem(text)
                list_item.setToolTip(text)
                self.queue_list.addItem(list_item)
            self.url_input.clear()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Input is empty.")

    def remove_selected(self):
        selected = self.queue_list.selectedItems()
        if not selected:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select an item.")
            return
        for item in selected:
            row = self.queue_list.row(item)
            file_name = unquote(os.path.basename(item.text().split("?")[0]))
            if file_name in self.added_file_names:
                self.added_file_names.remove(file_name)
            self.download_list.pop(row)
            self.queue_list.takeItem(row)
            self.progress_table.removeRow(row)
            self.log(f"Removed from queue: {item.text()}")

    def clear_queue(self):
        self.download_list.clear()
        self.queue_list.clear()
        self.progress_table.setRowCount(0)
        self.added_file_names.clear()
        self.log("Download queue cleared.")

    def move_up(self):
        selected = self.queue_list.selectedItems()
        if selected:
            item = selected[0]
            row = self.queue_list.row(item)
            if row > 0:
                self.queue_list.takeItem(row)
                self.queue_list.insertItem(row - 1, item)
                self.queue_list.setCurrentItem(item)
                self.download_list[row], self.download_list[row-1] = self.download_list[row-1], self.download_list[row]
                self.log(f"Moved up: {item.text()}")

    def move_down(self):
        selected = self.queue_list.selectedItems()
        if selected:
            item = selected[0]
            row = self.queue_list.row(item)
            if row < self.queue_list.count() - 1:
                self.queue_list.takeItem(row)
                self.queue_list.insertItem(row + 1, item)
                self.queue_list.setCurrentItem(item)
                self.download_list[row], self.download_list[row+1] = self.download_list[row+1], self.download_list[row]
                self.log(f"Moved down: {item.text()}")

    def start_download_with_message(self):
        QtWidgets.QMessageBox.information(self, "Info", "Download started.")
        self.start_button.setEnabled(False)
        self.start_button.setStyleSheet("background-color: #BDBDBD; color: #757575;")
        self.start_download()

    def stop_download(self):
        # توقف دانلود تمام موارد؛ برای هر فایل موجود در worker، cancel انجام شود
        if self.worker:
            for file_name in list(self.worker.analytics.keys()):
                self.worker.cancel_download(file_name)
            self.log("Stop download requested for all items.")
            self.show_notification("Stopped", "All downloads have been requested to stop.")

    def start_download(self):
        if not self.download_list:
            QtWidgets.QMessageBox.critical(self, "Error", "No URL in download queue.")
            self.start_button.setEnabled(True)
            return
        if not self.download_folder:
            QtWidgets.QMessageBox.critical(self, "Error", "Please select a download folder.")
            self.start_button.setEnabled(True)
            return
        filtered_list = []
        for url in self.download_list:
            file_name = unquote(os.path.basename(url.split("?")[0]))
            file_path = os.path.join(self.download_folder, file_name)
            try:
                head_resp = requests.head(url, timeout=5)
                head_resp.raise_for_status()
                expected_size = int(head_resp.headers.get("Content-Length", 0))
                if os.path.exists(file_path):
                    existing_size = os.path.getsize(file_path)
                    if expected_size != 0 and existing_size >= expected_size:
                        self.log(f"File {file_name} already downloaded; skipping.")
                        continue
            except Exception as e:
                logging.warning(f"HEAD check failed for {file_name}: {e}")
            filtered_list.append(url)
        self.download_list = filtered_list
        self.download_list.sort(key=lambda x: unquote(os.path.basename(x.split("?")[0])).lower())
        items = [self.queue_list.item(i).text() for i in range(self.queue_list.count())]
        items.sort(key=lambda x: unquote(os.path.basename(x.split("?")[0])).lower())
        self.queue_list.clear()
        for text in items:
            list_item = QtWidgets.QListWidgetItem(text)
            list_item.setToolTip(text)
            self.queue_list.addItem(list_item)
        self.overall_progress_bar.setMaximum(len(self.download_list))
        self.overall_progress_bar.setValue(0)
        self.worker = DownloadWorker(self.download_list, self.download_folder, self.config_data)
        self.worker.progress_update.connect(self.handle_progress_update)
        self.worker.file_complete.connect(self.handle_file_complete)
        self.worker.file_error.connect(self.handle_file_error)
        self.worker.overall_progress.connect(self.handle_overall_progress)
        self.worker.log_message.connect(self.log)
        self.worker.download_canceled.connect(self.handle_download_canceled)
        self.worker.all_downloads_complete.connect(self.all_downloads_complete)
        self.worker.start()
        logging.info("Download process started.")

    def handle_progress_update(self, file_name, percent):
        self.update_progress_row(file_name, percent)

    def handle_file_complete(self, file_name):
        for row in range(self.progress_table.rowCount()):
            if self.progress_table.item(row, 0).text() == file_name:
                self.progress_table.item(row, 4).setText("Completed")
                downloaded = self.worker.analytics.get(file_name, {}).get("downloaded_bytes", 0)
                mb = downloaded / (1024*1024)
                self.progress_table.item(row, 2).setText(f"{mb:.2f} MB")
                break
        self.log(f"Download completed: {file_name}")
        self.show_notification("Completed", f"Download completed: {file_name}")

    def handle_file_error(self, file_name, error):
        for row in range(self.progress_table.rowCount()):
            if self.progress_table.item(row, 0).text() == file_name:
                self.progress_table.item(row, 4).setText("Failed")
                downloaded = self.worker.analytics.get(file_name, {}).get("downloaded_bytes", 0)
                mb = downloaded / (1024*1024)
                self.progress_table.item(row, 2).setText(f"{mb:.2f} MB")
                break
        self.log(f"Error downloading {file_name}: {error}")
        self.show_notification("Error", f"{file_name}\n{error}")
        QtWidgets.QMessageBox.critical(self, "Download Error", f"{file_name}\n{error}")

    def handle_download_canceled(self, file_name):
        for row in range(self.progress_table.rowCount()):
            if self.progress_table.item(row, 0).text() == file_name:
                self.progress_table.item(row, 4).setText("Canceled")
                break
        self.log(f"Download canceled: {file_name}")
        self.show_notification("Canceled", f"Download {file_name} has been canceled.")
        QtWidgets.QMessageBox.information(self, "Download Canceled", f"Download {file_name} has been canceled.")

    def handle_overall_progress(self, current, total):
        self.overall_progress_bar.setValue(current)

    def all_downloads_complete(self):
        self.update_report()
        QtWidgets.QMessageBox.information(self, "Info", "All downloads are complete.")
        self.download_list.clear()
        self.queue_list.clear()
        self.progress_table.setRowCount(0)
        self.added_file_names.clear()
        self.start_button.setEnabled(True)
        self.start_button.setStyleSheet("background-color: #FF5722; color: white; font-size: 14px;")

    def log(self, message):
        self.log_text.append(message)

    def save_settings(self):
        try:
            self.config_data["concurrent_downloads"] = int(self.concurrent_input.text())
            self.config_data["chunk_size"] = int(self.chunk_input.text())
            self.config_data["resume_downloads"] = self.resume_checkbox.isChecked()
            extensions = [ext.strip() for ext in self.extensions_input.text().split(",") if ext.strip()]
            self.config_data["allowed_extensions"] = extensions if extensions else DEFAULT_CONFIG["allowed_extensions"]
            self.config_data["min_bitrate"] = self.bitrate_combo.currentData()
            self.config_data["download_folder"] = self.download_folder
            self.config_data["language"] = self.language_combo.currentData()
            self.config_data["theme"] = self.theme_combo.currentData()
            self.language = self.config_data["language"]
            self.theme = self.config_data["theme"]
            save_config(self.config_data)
            self.log("Settings saved.")
            QtWidgets.QMessageBox.information(self, "Settings", "Settings saved successfully.")
            self.update_ui_texts()
            self.apply_theme()
            allowed_exts = [ext.strip().lower() for ext in self.config_data["allowed_extensions"]]
            self.bitrate_combo.setVisible(".mp3" in allowed_exts)
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid settings values.")
            logging.error("Error saving settings: Invalid values.")

    def update_cache(self):
        global cache_data
        cache_data = {}
        save_cache_data()
        self.log("Cache updated and old data cleared.")

    def update_report(self):
        if self.worker is None or not hasattr(self.worker, "analytics"):
            return
        for file_name, data in self.worker.analytics.items():
            found = False
            for row in range(self.report_table.rowCount()):
                if self.report_table.item(row, 0).text() == file_name:
                    found = True
                    duration = "-" 
                    if data["end"] and data["start"]:
                        duration = f"{data['end'] - data['start']:.2f}"
                    errors = data.get("errors", 0)
                    downloaded = data.get("downloaded_bytes", 0)
                    mb = downloaded / (1024*1024)
                    status = data.get("status", "-")
                    self.report_table.item(row, 1).setText(str(duration))
                    self.report_table.item(row, 2).setText(str(errors))
                    self.report_table.item(row, 3).setText(f"{mb:.2f} MB")
                    self.report_table.item(row, 4).setText(status)
                    break
            if not found:
                row = self.report_table.rowCount()
                self.report_table.insertRow(row)
                duration = "-" 
                if data["end"] and data["start"]:
                    duration = f"{data['end'] - data['start']:.2f}"
                errors = data.get("errors", 0)
                downloaded = data.get("downloaded_bytes", 0)
                mb = downloaded / (1024*1024)
                status = data.get("status", "-")
                self.report_table.setItem(row, 0, QtWidgets.QTableWidgetItem(file_name))
                self.report_table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(duration)))
                self.report_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(errors)))
                self.report_table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{mb:.2f} MB"))
                self.report_table.setItem(row, 4, QtWidgets.QTableWidgetItem(status))
        self.log("Reports updated.")

    def update_ui_texts(self):
        self.setWindowTitle(tr("app_title", self.language))
        self.tabs.setTabText(0, tr("download_tab", self.language))
        self.tabs.setTabText(1, tr("settings_tab", self.language))
        self.tabs.setTabText(2, tr("report_tab", self.language))
        self.tabs.setTabText(3, tr("about_tab", self.language))
        self.url_input.setPlaceholderText(tr("add_url_placeholder", self.language))

    def apply_theme(self):
        if self.theme == "dark":
            style = """
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: 'Segoe UI'; font-size: 14px; }
            QTabWidget::pane { border: 1px solid #555555; }
            QTabBar::tab { background-color: #3c3f41; color: #ffffff; padding: 6px; border: 1px solid #555555; border-bottom: none; }
            QTabBar::tab:selected { background-color: #2b2b2b; color: #ffffff; }
            QPushButton { background-color: #3c3f41; border: none; padding: 6px; color: #ffffff; }
            QPushButton:hover { background-color: #4e5254; }
            QLineEdit, QComboBox, QListWidget, QTextEdit { background-color: #3c3f41; border: 1px solid #555555; padding: 4px; color: #ffffff; }
            QTableWidget { background-color: #3c3f41; color: #ffffff; }
            QTableWidget::item { background-color: #3c3f41; color: #ffffff; }
            QHeaderView::section { background-color: #3c3f41; color: #ffffff; padding: 4px; border: 1px solid #555555; }
            QProgressBar { border: 1px solid #555555; text-align: center; color: #ffffff; }
            QProgressBar::chunk { background-color: #007ACC; }
            QToolTip { background-color: #555555; color: #000000; border: 1px solid #000000FF; }
            """
        else:
            style = """
            QWidget { background-color: #f0f0f0; color: #000000; font-family: 'Segoe UI'; font-size: 14px; }
            QPushButton { background-color: #e0e0e0; border: none; padding: 6px; }
            QPushButton:hover { background-color: #d5d5d5; }
            QLineEdit, QComboBox, QListWidget, QTextEdit { background-color: #ffffff; border: 1px solid #cccccc; padding: 4px; color: #000000; }
            QTableWidget { background-color: #ffffff; color: #000000; }
            QTableWidget::item { background-color: #ffffff; color: #000000; }
            QHeaderView::section { background-color: #e0e0e0; color: #000000; padding: 4px; border: 1px solid #cccccc; }
            QProgressBar { border: 1px solid #cccccc; text-align: center; }
            QProgressBar::chunk { background-color: #4CAF50; }
            QToolTip { background-color: #f0f0f0; color: #000000; border: 1px solid #000000; }
            """
        self.setStyleSheet(style)

    def show_notification(self, title, message):
        self.tray_icon.showMessage(title, message, QtGui.QIcon("icon.png"), 3000)

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.worker = None
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
