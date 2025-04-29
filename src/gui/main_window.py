import sys
import os
import threading
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
    QTextEdit, QProgressBar, QFileDialog, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QUrl, QThread

# 親ディレクトリをパスに追加して、他のモジュールをインポートできるようにする
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.crawler import WebCrawler
from utils.export import export_pages_to_csv, export_links_to_csv


class CrawlerSignals(QObject):
    """クローラーのシグナルを定義するクラス"""
    update_progress = pyqtSignal(int, int)  # 進捗更新シグナル (現在のページ数, 合計ページ数)
    update_status = pyqtSignal(str)  # ステータス更新シグナル
    finished = pyqtSignal(list, list, list)  # 完了シグナル (pages, external_links, broken_links)
    error = pyqtSignal(str)  # エラーシグナル


class CrawlerThread(QThread):
    """バックグラウンドでクローラーを実行するスレッド"""
    
    def __init__(self, base_url, max_pages=None, delay=0.5, max_workers=10):
        super().__init__()
        self.base_url = base_url
        self.max_pages = max_pages
        self.delay = delay
        self.max_workers = max_workers
        self.signals = CrawlerSignals()
        
    def run(self):
        try:
            crawler = WebCrawler(
                self.base_url, 
                max_pages=self.max_pages, 
                delay=self.delay,
                max_workers=self.max_workers
            )
            
            # 元のクラスに進捗状況通知機能を追加
            original_process_url = crawler._process_url
            
            def process_url_with_signals(url, source_url):
                result = original_process_url(url, source_url)
                self.signals.update_progress.emit(len(crawler.pages), len(crawler.visited_urls))
                return result
                
            crawler._process_url = process_url_with_signals
            
            # クローリング実行
            pages, external_links, broken_links = crawler.start_crawl()
            self.signals.finished.emit(pages, external_links, broken_links)
            
        except Exception as e:
            self.signals.error.emit(str(e))


class DirectoryDiggerApp(QMainWindow):
    """ディレクトリ探索アプリのメインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Directory Digger - ウェブサイト構造探索ツール")
        self.setMinimumSize(800, 600)
        
        # インスタンス変数の初期化
        self.crawler_thread = None
        self.pages = []
        self.external_links = []
        self.broken_links = []
        
        # UI構築
        self._init_ui()
        
        # ロギング設定
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def _init_ui(self):
        """UIを初期化する"""
        # メインウィジェットとレイアウト
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # URLと設定のグループ
        settings_group = QGroupBox("クロール設定")
        settings_layout = QVBoxLayout()
        
        # URL入力
        url_layout = QHBoxLayout()
        url_label = QLabel("開始URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        settings_layout.addLayout(url_layout)
        
        # クロール設定
        params_layout = QHBoxLayout()
        
        # 最大ページ数
        max_pages_label = QLabel("最大ページ数:")
        self.max_pages_input = QSpinBox()
        self.max_pages_input.setRange(0, 100000)
        self.max_pages_input.setValue(1000)
        self.max_pages_input.setSpecialValueText("無制限")
        params_layout.addWidget(max_pages_label)
        params_layout.addWidget(self.max_pages_input)
        
        # 遅延
        delay_label = QLabel("遅延 (秒):")
        self.delay_input = QDoubleSpinBox()
        self.delay_input.setRange(0.1, 10.0)
        self.delay_input.setValue(0.5)
        self.delay_input.setSingleStep(0.1)
        params_layout.addWidget(delay_label)
        params_layout.addWidget(self.delay_input)
        
        # ワーカー数
        workers_label = QLabel("ワーカー数:")
        self.workers_input = QSpinBox()
        self.workers_input.setRange(1, 50)
        self.workers_input.setValue(10)
        params_layout.addWidget(workers_label)
        params_layout.addWidget(self.workers_input)
        
        settings_layout.addLayout(params_layout)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 操作ボタン
        buttons_layout = QHBoxLayout()
        
        self.start_button = QPushButton("クロール開始")
        self.start_button.clicked.connect(self.start_crawling)
        buttons_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_crawling)
        buttons_layout.addWidget(self.stop_button)
        
        self.export_button = QPushButton("CSVエクスポート")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_results)
        buttons_layout.addWidget(self.export_button)
        
        main_layout.addLayout(buttons_layout)
        
        # ステータスとプログレスバー
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("準備完了")
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v/%m ページ")
        status_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(status_layout)
        
        # ログ表示エリア
        log_group = QGroupBox("ログ")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
    
    def log(self, message):
        """ログメッセージを表示エリアに追加"""
        self.log_text.append(message)
        # 自動スクロール
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
    def start_crawling(self):
        """クローリングを開始する"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "入力エラー", "有効なURLを入力してください")
            return
        
        # URLが http:// または https:// で始まっているか確認
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
            self.url_input.setText(url)
        
        # 入力値を取得
        max_pages = None if self.max_pages_input.value() == 0 else self.max_pages_input.value()
        delay = self.delay_input.value()
        max_workers = self.workers_input.value()
        
        # クローラーの準備
        self.crawler_thread = CrawlerThread(
            base_url=url,
            max_pages=max_pages,
            delay=delay,
            max_workers=max_workers
        )
        
        # シグナル接続
        self.crawler_thread.signals.update_progress.connect(self.update_progress)
        self.crawler_thread.signals.update_status.connect(self.update_status)
        self.crawler_thread.signals.finished.connect(self.crawling_finished)
        self.crawler_thread.signals.error.connect(self.handle_error)
        
        # UIの状態更新
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.export_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        
        # クローリング開始
        self.log(f"クローリング開始: {url}")
        self.crawler_thread.start()
    
    def stop_crawling(self):
        """クローリングを停止する"""
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.crawler_thread.terminate()
            self.log("クローリングを停止しました")
            
            # UIの状態更新
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("停止しました")
    
    def update_progress(self, current, total):
        """進捗バーとステータスを更新する"""
        self.progress_bar.setMaximum(max(total, 1))  # 0除算防止
        self.progress_bar.setValue(current)
        self.status_label.setText(f"クロール中: {current}/{total} ページ")
        
    def update_status(self, status):
        """ステータスメッセージを更新する"""
        self.status_label.setText(status)
        self.log(status)
    
    def crawling_finished(self, pages, external_links, broken_links):
        """クローリング完了時の処理"""
        self.pages = pages
        self.external_links = external_links
        self.broken_links = broken_links
        
        # 結果の統計情報をログに表示
        self.log(f"クロール完了: {len(pages)}ページを探索しました")
        self.log(f"外部リンク: {len(external_links)}件")
        self.log(f"リンク切れ: {len(broken_links)}件")
        
        # UIの状態更新
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.export_button.setEnabled(True)
        self.status_label.setText("クロール完了")
        
    def handle_error(self, error_message):
        """エラーハンドリング"""
        self.log(f"エラーが発生しました: {error_message}")
        QMessageBox.critical(self, "エラー", error_message)
        
        # UIの状態更新
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("エラーが発生しました")
    
    def export_results(self):
        """結果をCSVにエクスポートする"""
        if not self.pages and not self.external_links and not self.broken_links:
            QMessageBox.warning(self, "警告", "エクスポートするデータがありません")
            return
            
        # 出力ディレクトリを選択
        output_dir = QFileDialog.getExistingDirectory(
            self, "保存先ディレクトリを選択", os.path.expanduser("~")
        )
        
        if not output_dir:
            return
            
        try:
            # タイムスタンプを作成（ファイル名の一貫性のため）
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 各種CSVをエクスポート
            results = []
            
            if self.pages:
                filename = f"pages_{timestamp}.csv"
                path = export_pages_to_csv(self.pages, output_dir, filename)
                if path:
                    results.append(f"ページ情報: {path}")
            
            if self.external_links:
                filename = f"external_links_{timestamp}.csv"
                path = export_links_to_csv(self.external_links, output_dir, filename, 'external')
                if path:
                    results.append(f"外部リンク: {path}")
            
            if self.broken_links:
                filename = f"broken_links_{timestamp}.csv"
                path = export_links_to_csv(self.broken_links, output_dir, filename, 'broken')
                if path:
                    results.append(f"リンク切れ: {path}")
            
            # 結果を表示
            if results:
                message = "以下のファイルを保存しました：\n" + "\n".join(results)
                QMessageBox.information(self, "エクスポート完了", message)
                self.log(message)
            else:
                QMessageBox.warning(self, "エクスポート失敗", "エクスポートに失敗しました")
                
        except Exception as e:
            self.log(f"エクスポート中にエラーが発生しました: {str(e)}")
            QMessageBox.critical(self, "エラー", f"エクスポート中にエラーが発生しました: {str(e)}")


def main():
    app = QApplication(sys.argv)
    window = DirectoryDiggerApp()
    window.show()
    sys.exit(app.exec())