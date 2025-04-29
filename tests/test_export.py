import sys
import os
import unittest
import tempfile
import pandas as pd
from unittest.mock import patch, MagicMock

# 親ディレクトリをインポートパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.export import export_pages_to_csv, export_links_to_csv

class TestExport(unittest.TestCase):
    """エクスポート機能のテスト"""
    
    def setUp(self):
        """テスト用のダミーデータを準備"""
        # テスト用ページデータ
        self.test_pages = [
            {
                'url': 'https://example.com',
                'title': 'Example Domain',
                'keywords': 'example, domain',
                'description': 'This is an example website',
                'notes': 'Test note'
            },
            {
                'url': 'https://example.com/page1',
                'title': 'Page 1',
                'keywords': 'page1, test',
                'description': 'Page 1 description',
                'notes': ''
            }
        ]
        
        # テスト用リンクデータ
        self.test_links = [
            ('https://external.com', 'https://example.com'),
            ('https://another.com', 'https://example.com/page1')
        ]
        
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
    
    def test_export_pages_to_csv(self):
        """ページデータのCSVエクスポート機能をテスト"""
        # CSVエクスポート
        output_path = export_pages_to_csv(self.test_pages, self.temp_dir, 'test_pages.csv')
        
        # ファイルが作成されたことを確認
        self.assertTrue(os.path.exists(output_path))
        
        # CSVの内容を検証
        df = pd.read_csv(output_path)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['url'], 'https://example.com')
        self.assertEqual(df.iloc[0]['title'], 'Example Domain')
        self.assertEqual(df.iloc[1]['url'], 'https://example.com/page1')
    
    def test_export_links_to_csv(self):
        """リンクデータのCSVエクスポート機能をテスト"""
        # 外部リンクとしてエクスポート
        output_path = export_links_to_csv(
            self.test_links, self.temp_dir, 'test_external_links.csv', 'external'
        )
        
        # ファイルが作成されたことを確認
        self.assertTrue(os.path.exists(output_path))
        
        # CSVの内容を検証
        df = pd.read_csv(output_path)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['link_url'], 'https://external.com')
        self.assertEqual(df.iloc[0]['source_url'], 'https://example.com')
        self.assertEqual(df.iloc[1]['link_url'], 'https://another.com')
    
    def test_empty_data(self):
        """空のデータセットでのエクスポート処理をテスト"""
        # 空のページリスト
        result = export_pages_to_csv([], self.temp_dir, 'empty_pages.csv')
        self.assertIsNone(result)
        
        # 空のリンクリスト
        result = export_links_to_csv([], self.temp_dir, 'empty_links.csv')
        self.assertIsNone(result)
    
    def tearDown(self):
        """テスト終了後の後処理"""
        # テスト用の一時ファイルを削除
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

if __name__ == '__main__':
    unittest.main()