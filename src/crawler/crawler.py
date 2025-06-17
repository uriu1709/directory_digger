import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import logging
import validators
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
import threading

class WebCrawler:
    """
    ウェブサイトを探索し、ページ情報を収集するクローラークラス
    """
    
    def __init__(self, base_url, max_pages=None, delay=0.5, max_workers=10):
        """
        クローラーの初期化
        
        Parameters:
        -----------
        base_url : str
            クロールを開始するURL
        max_pages : int, optional
            クロールする最大ページ数、Noneの場合は無制限
        delay : float, optional
            リクエスト間の遅延（秒）
        max_workers : int, optional
            並行して実行するワーカーの最大数
        """
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.delay = delay
        self.max_workers = max_workers
        
        # 訪問済みURLの集合
        self.visited_urls = set()
        # 探索するURLのキュー
        self.url_queue = Queue()
        # 見つかったページの情報を格納するリスト
        self.pages = []
        # 外部リンクのリスト [(外部URL, ソースURL)]
        self.external_links = []
        # リンク切れのリスト [(リンク切れURL, ソースURL)]
        self.broken_links = []
        
        # 同期用ロック
        self.lock = threading.Lock()
        
        # ロギング設定
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def start_crawl(self):
        """クローリングを開始する"""
        self.url_queue.put((self.base_url, self.base_url))  # (URL, ソースURL)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            while True:
                # キューから次のURLを取得
                try:
                    current_url, source_url = self.url_queue.get(timeout=5)
                except Empty:
                    # キューが空で、すべてのタスクが終了したら終了
                    if all(future.done() for future in futures):
                        break
                    continue
                
                # 既に訪問済みのURLはスキップ
                if current_url in self.visited_urls:
                    self.url_queue.task_done()
                    continue
                
                # 最大ページ数に達したら終了
                if self.max_pages and len(self.visited_urls) >= self.max_pages:
                    self.url_queue.task_done()
                    break
                
                # URLをセットに追加
                self.visited_urls.add(current_url)
                
                # 非同期でページをクロール
                future = executor.submit(self._process_url, current_url, source_url)
                futures.append(future)
                
                # 遅延を入れる
                time.sleep(self.delay)
                
        self.logger.info(f"クロール完了: {len(self.pages)}ページを探索しました")
        return self.pages, self.external_links, self.broken_links
    
    def _process_url(self, url, source_url):
        """
        URLを処理し、情報を抽出する
        
        Parameters:
        -----------
        url : str
            処理するURL
        source_url : str
            このURLが見つかったソースのURL
        """
        try:
            self.logger.info(f"処理中: {url}")
            response = requests.get(url, timeout=10)
            
            # ステータスコードが200以外の場合は壊れたリンクとして記録
            if response.status_code != 200:
                with self.lock:
                    self.broken_links.append((url, source_url))
                return
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # ページ情報を収集
            title = soup.title.text.strip() if soup.title else "No Title"
            
            # メタタグからキーワードとディスクリプションを抽出
            keywords = ""
            description = ""
            
            meta_keywords = soup.find("meta", attrs={"name": "keywords"})
            if meta_keywords and meta_keywords.get("content"):
                keywords = meta_keywords["content"]
                
            meta_description = soup.find("meta", attrs={"name": "description"})
            if meta_description and meta_description.get("content"):
                description = meta_description["content"]
            
            # ページ情報を記録
            page_info = {
                "url": url,
                "title": title,
                "keywords": keywords,
                "description": description,
                "notes": ""
            }
            
            with self.lock:
                self.pages.append(page_info)
            
            # このページ内のリンクを収集
            self._collect_links(soup, url)
            
        except Exception as e:
            self.logger.error(f"エラー {url}: {str(e)}")
            with self.lock:
                self.broken_links.append((url, source_url))
    
    def _collect_links(self, soup, source_url):
        """
        ページ内のリンクを収集し、キューに追加する
        
        Parameters:
        -----------
        soup : BeautifulSoup
            解析するページのBeautifulSoupオブジェクト
        source_url : str
            このリンクが見つかったソースのURL
        """
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '').strip()
            
            # 空のリンク、JavaScriptリンク、アンカーリンクは無視
            if not href or href.startswith(('javascript:', '#')):
                continue
            
            # 相対URLを絶対URLに変換
            absolute_url = urljoin(source_url, href)
            
            # URLが有効かチェック
            if not validators.url(absolute_url):
                continue
            
            # 同じドメインのリンクのみをクロールキューに追加
            parsed_url = urlparse(absolute_url)
            if parsed_url.netloc == self.base_domain:
                # フラグメント (#以降) を除去
                clean_url = absolute_url.split('#')[0]
                if clean_url not in self.visited_urls:
                    self.url_queue.put((clean_url, source_url))
            else:
                # 外部リンクの場合は記録
                with self.lock:
                    self.external_links.append((absolute_url, source_url))