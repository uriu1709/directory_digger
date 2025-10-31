import unittest
import sys
import os
import tempfile
import json

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.hierarchy import (
    build_hierarchy_tree,
    compare_hierarchies,
    generate_tree_text,
    flatten_hierarchy
)
from utils.export import (
    export_hierarchy_comparison_to_csv,
    export_hierarchy_tree_to_json,
    export_hierarchy_tree_to_text
)


class TestHierarchyFunctions(unittest.TestCase):
    """階層構造分析機能のテスト"""

    def setUp(self):
        """テストデータの準備"""
        self.sample_pages = [
            {
                'url': 'https://example.com/',
                'title': 'Home',
                'breadcrumb': ['ホーム'],
                'breadcrumb_depth': 1,
                'url_hierarchy': ['/'],
                'url_depth': 1
            },
            {
                'url': 'https://example.com/products',
                'title': 'Products',
                'breadcrumb': ['ホーム', '製品'],
                'breadcrumb_depth': 2,
                'url_hierarchy': ['/', 'products'],
                'url_depth': 2
            },
            {
                'url': 'https://example.com/products/electronics',
                'title': 'Electronics',
                'breadcrumb': ['ホーム', '製品', '電子機器'],
                'breadcrumb_depth': 3,
                'url_hierarchy': ['/', 'products', 'electronics'],
                'url_depth': 3
            },
            {
                'url': 'https://example.com/about',
                'title': 'About',
                'breadcrumb': None,
                'breadcrumb_depth': 0,
                'url_hierarchy': ['/', 'about'],
                'url_depth': 2
            }
        ]

    def test_build_hierarchy_tree_url(self):
        """URL階層ツリーの構築をテスト"""
        tree = build_hierarchy_tree(self.sample_pages, 'url')

        # ルートが存在することを確認
        self.assertIn('/', tree)

        # products が存在することを確認
        self.assertIn('products', tree['/']['_children'])

        # electronics が products の子として存在することを確認
        self.assertIn('electronics', tree['/']['_children']['products']['_children'])

    def test_build_hierarchy_tree_breadcrumb(self):
        """パンくず階層ツリーの構築をテスト"""
        tree = build_hierarchy_tree(self.sample_pages, 'breadcrumb')

        # ホームが存在することを確認
        self.assertIn('ホーム', tree)

        # 製品がホームの子として存在することを確認
        self.assertIn('製品', tree['ホーム']['_children'])

    def test_compare_hierarchies(self):
        """階層比較機能をテスト"""
        comparison = compare_hierarchies(self.sample_pages)

        # 比較結果が4件あることを確認
        self.assertEqual(len(comparison), 4)

        # 最初のページの比較結果を確認
        first = comparison[0]
        self.assertEqual(first['url'], 'https://example.com/')
        self.assertEqual(first['url_depth'], 1)
        self.assertEqual(first['breadcrumb_depth'], 1)
        self.assertTrue(first['depth_match'])
        self.assertTrue(first['has_breadcrumb'])

        # パンくずがないページを確認
        about = [c for c in comparison if 'about' in c['url']][0]
        self.assertFalse(about['has_breadcrumb'])
        self.assertIsNone(about['depth_match'])

    def test_generate_tree_text(self):
        """ツリーテキスト生成をテスト"""
        tree = build_hierarchy_tree(self.sample_pages, 'url')
        text = generate_tree_text(tree)

        # テキストが生成されることを確認
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)

        # ツリー構造の記号が含まれることを確認
        self.assertTrue('├──' in text or '└──' in text)

    def test_flatten_hierarchy(self):
        """階層フラット化をテスト"""
        flattened = flatten_hierarchy(self.sample_pages, 'url')

        # フラット化されたリストが返されることを確認
        self.assertIsInstance(flattened, list)
        self.assertGreater(len(flattened), 0)

        # 各要素に必要なキーが含まれることを確認
        for item in flattened:
            self.assertIn('level', item)
            self.assertIn('path', item)
            self.assertIn('pages', item)


class TestHierarchyExport(unittest.TestCase):
    """階層構造エクスポート機能のテスト"""

    def setUp(self):
        """テストデータの準備"""
        self.sample_pages = [
            {
                'url': 'https://example.com/',
                'title': 'Home',
                'breadcrumb': ['ホーム'],
                'breadcrumb_depth': 1,
                'url_hierarchy': ['/'],
                'url_depth': 1
            },
            {
                'url': 'https://example.com/products',
                'title': 'Products',
                'breadcrumb': ['ホーム', '製品'],
                'breadcrumb_depth': 2,
                'url_hierarchy': ['/', 'products'],
                'url_depth': 2
            }
        ]

        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ディレクトリを削除
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_hierarchy_comparison_to_csv(self):
        """階層比較CSVエクスポートをテスト"""
        path = export_hierarchy_comparison_to_csv(
            self.sample_pages,
            self.temp_dir,
            'test_comparison.csv'
        )

        # ファイルが作成されたことを確認
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))

        # CSVの内容を確認
        import pandas as pd
        df = pd.read_csv(path)
        self.assertEqual(len(df), 2)
        self.assertIn('url', df.columns)
        self.assertIn('url_hierarchy', df.columns)
        self.assertIn('breadcrumb_hierarchy', df.columns)
        self.assertIn('depth_match', df.columns)

    def test_export_hierarchy_tree_to_json(self):
        """階層ツリーJSONエクスポートをテスト"""
        path = export_hierarchy_tree_to_json(
            self.sample_pages,
            self.temp_dir,
            'test_tree.json',
            'url'
        )

        # ファイルが作成されたことを確認
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))

        # JSONの内容を確認
        with open(path, 'r', encoding='utf-8') as f:
            tree = json.load(f)

        self.assertIsInstance(tree, dict)
        self.assertIn('/', tree)

    def test_export_hierarchy_tree_to_text(self):
        """階層ツリーテキストエクスポートをテスト"""
        path = export_hierarchy_tree_to_text(
            self.sample_pages,
            self.temp_dir,
            'test_tree.txt',
            'url'
        )

        # ファイルが作成されたことを確認
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))

        # テキストの内容を確認
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertGreater(len(content), 0)
        self.assertIn('階層構造ツリー', content)

    def test_export_with_empty_pages(self):
        """空のページリストでのエクスポートをテスト"""
        path = export_hierarchy_comparison_to_csv(
            [],
            self.temp_dir,
            'test_empty.csv'
        )

        # 空の場合はNoneが返されることを確認
        self.assertIsNone(path)


if __name__ == '__main__':
    unittest.main()
