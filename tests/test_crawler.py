import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# 親ディレクトリをインポートパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crawler.crawler import WebCrawler

class TestWebCrawler(unittest.TestCase):
    """WebCrawlerクラスのテスト"""
    
    @patch('src.crawler.crawler.requests.get')
    def test_process_url(self, mock_get):
        """_process_urlメソッドのテスト"""
        # requestsのモックを設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <title>テストページ</title>
                <meta name="description" content="テスト用の説明文">
                <meta name="keywords" content="テスト, クローラー">
            </head>
            <body>
                <a href="https://example.com/page1">ページ1</a>
                <a href="https://example.com/page2">ページ2</a>
                <a href="https://external.com/page">外部リンク</a>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        # テスト用クローラーを初期化
        crawler = WebCrawler('https://example.com')
        
        # 非公開メソッドをテスト
        crawler._process_url('https://example.com', 'https://example.com')
        
        # ページが正しく抽出されたか確認
        self.assertEqual(len(crawler.pages), 1)
        page = crawler.pages[0]
        self.assertEqual(page['url'], 'https://example.com')
        self.assertEqual(page['title'], 'テストページ')
        self.assertEqual(page['description'], 'テスト用の説明文')
        self.assertEqual(page['keywords'], 'テスト, クローラー')
        
        # URLキューに正しくページが追加されたか確認
        self.assertEqual(crawler.url_queue.qsize(), 2)  # 同一ドメインのリンクのみが追加される
        
        # 外部リンクが正しく記録されたか確認
        self.assertEqual(len(crawler.external_links), 1)
        self.assertEqual(crawler.external_links[0][0], 'https://external.com/page')
    
    @patch('src.crawler.crawler.requests.get')
    def test_broken_links(self, mock_get):
        """リンク切れURLの処理テスト"""
        # 404レスポンスのモックを設定
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # テスト用クローラーを初期化
        crawler = WebCrawler('https://example.com')
        
        # 非公開メソッドをテスト
        crawler._process_url('https://example.com/not-found', 'https://example.com')
        
        # リンク切れが正しく記録されたか確認
        self.assertEqual(len(crawler.broken_links), 1)
        self.assertEqual(crawler.broken_links[0][0], 'https://example.com/not-found')
        self.assertEqual(crawler.broken_links[0][1], 'https://example.com')
        
        # ページが追加されていないことを確認
        self.assertEqual(len(crawler.pages), 0)

    @patch('src.crawler.crawler.requests.get')
    def test_breadcrumb_extraction(self, mock_get):
        """パンくずリスト抽出のテスト"""
        # パンくずリスト付きHTMLのモックを設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head><title>テストページ</title></head>
            <body>
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb">
                        <li><a href="/">ホーム</a></li>
                        <li><a href="/products">製品</a></li>
                        <li>電子機器</li>
                    </ol>
                </nav>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        # テスト用クローラーを初期化
        crawler = WebCrawler('https://example.com')

        # 非公開メソッドをテスト
        crawler._process_url('https://example.com/products/electronics', 'https://example.com')

        # パンくずリストが正しく抽出されたか確認
        self.assertEqual(len(crawler.pages), 1)
        page = crawler.pages[0]
        self.assertIn('breadcrumb', page)
        self.assertIsNotNone(page['breadcrumb'])
        self.assertEqual(len(page['breadcrumb']), 3)
        self.assertIn('ホーム', page['breadcrumb'])
        self.assertIn('製品', page['breadcrumb'])
        self.assertIn('電子機器', page['breadcrumb'])

    def test_url_hierarchy_calculation(self):
        """URL階層計算のテスト"""
        crawler = WebCrawler('https://example.com')

        # ルートURL
        hierarchy = crawler._calculate_url_hierarchy('https://example.com/')
        self.assertEqual(hierarchy, ['/'])

        # 1階層URL
        hierarchy = crawler._calculate_url_hierarchy('https://example.com/products')
        self.assertEqual(hierarchy, ['/', 'products'])

        # 複数階層URL
        hierarchy = crawler._calculate_url_hierarchy('https://example.com/products/electronics/phones')
        self.assertEqual(hierarchy, ['/', 'products', 'electronics', 'phones'])

        # 末尾スラッシュ付きURL
        hierarchy = crawler._calculate_url_hierarchy('https://example.com/products/')
        self.assertEqual(hierarchy, ['/', 'products'])

    @patch('src.crawler.crawler.requests.get')
    def test_hierarchy_in_page_info(self, mock_get):
        """ページ情報に階層情報が含まれることをテスト"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head><title>テストページ</title></head>
            <body>
                <nav aria-label="breadcrumb">
                    <ol><li>ホーム</li><li>製品</li></ol>
                </nav>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        crawler = WebCrawler('https://example.com')
        crawler._process_url('https://example.com/products', 'https://example.com')

        self.assertEqual(len(crawler.pages), 1)
        page = crawler.pages[0]

        # 階層情報フィールドが存在することを確認
        self.assertIn('breadcrumb', page)
        self.assertIn('breadcrumb_depth', page)
        self.assertIn('url_hierarchy', page)
        self.assertIn('url_depth', page)

        # 深さが正しく計算されていることを確認
        self.assertEqual(page['url_depth'], 2)  # / と products
        self.assertEqual(page['breadcrumb_depth'], 2)  # ホーム と 製品

if __name__ == '__main__':
    unittest.main()