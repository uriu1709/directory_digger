import pandas as pd
import os
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

def export_pages_to_csv(pages, output_dir='./output', filename=None):
    """
    ページ情報をCSVファイルにエクスポートする
    
    Parameters:
    -----------
    pages : list
        ページ情報のリスト。各ページは辞書型で、url, title, keywords, description, notesのキーを持つ
    output_dir : str, optional
        出力先ディレクトリのパス
    filename : str, optional
        出力ファイル名（省略時は日時から自動生成）
    
    Returns:
    --------
    str
        エクスポートされたCSVファイルのパス
    """
    if not pages:
        logger.warning("エクスポートするページが見つかりません")
        return None
    
    # 出力ディレクトリがなければ作成
    os.makedirs(output_dir, exist_ok=True)
    
    # ファイル名が指定されていなければ日時から生成
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"pages_{timestamp}.csv"
    
    # 出力ファイルのフルパス
    output_path = os.path.join(output_dir, filename)
    
    # DataFrameに変換してCSVに保存
    try:
        df = pd.DataFrame(pages)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"ページ情報を{output_path}にエクスポートしました")
        return output_path
    except Exception as e:
        logger.error(f"CSVエクスポート中にエラーが発生しました: {str(e)}")
        return None

def export_links_to_csv(links, output_dir='./output', filename=None, link_type='external'):
    """
    リンクリストをCSVファイルにエクスポートする
    
    Parameters:
    -----------
    links : list
        リンクのリスト。各リンクはタプル(link_url, source_url)の形式
    output_dir : str, optional
        出力先ディレクトリのパス
    filename : str, optional
        出力ファイル名（省略時は日時とlink_typeから自動生成）
    link_type : str, optional
        リンクの種類（'external'または'broken'）
    
    Returns:
    --------
    str
        エクスポートされたCSVファイルのパス
    """
    if not links:
        logger.warning(f"エクスポートする{link_type}リンクが見つかりません")
        return None
    
    # 出力ディレクトリがなければ作成
    os.makedirs(output_dir, exist_ok=True)
    
    # ファイル名が指定されていなければ日時から生成
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{link_type}_links_{timestamp}.csv"
    
    # 出力ファイルのフルパス
    output_path = os.path.join(output_dir, filename)
    
    # DataFrameに変換してCSVに保存
    try:
        df = pd.DataFrame(links, columns=['link_url', 'source_url'])
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"{link_type}リンク情報を{output_path}にエクスポートしました")
        return output_path
    except Exception as e:
        logger.error(f"CSVエクスポート中にエラーが発生しました: {str(e)}")
        return None


def export_hierarchy_comparison_to_csv(pages, output_dir='./output', filename=None):
    """
    URL階層とパンくず階層の比較結果をCSVファイルにエクスポートする

    Parameters:
    -----------
    pages : list
        ページ情報のリスト
    output_dir : str, optional
        出力先ディレクトリのパス
    filename : str, optional
        出力ファイル名（省略時は日時から自動生成）

    Returns:
    --------
    str
        エクスポートされたCSVファイルのパス
    """
    if not pages:
        logger.warning("エクスポートするページが見つかりません")
        return None

    # 出力ディレクトリがなければ作成
    os.makedirs(output_dir, exist_ok=True)

    # ファイル名が指定されていなければ日時から生成
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"hierarchy_comparison_{timestamp}.csv"

    # 出力ファイルのフルパス
    output_path = os.path.join(output_dir, filename)

    # 比較データを作成
    comparison_data = []
    for page in pages:
        url_hierarchy = page.get('url_hierarchy', [])
        breadcrumb = page.get('breadcrumb', [])
        url_depth = page.get('url_depth', 0)
        breadcrumb_depth = page.get('breadcrumb_depth', 0)

        # 階層を文字列に変換
        url_hierarchy_str = ' > '.join(url_hierarchy) if url_hierarchy else ''
        breadcrumb_str = ' > '.join(breadcrumb) if breadcrumb else ''

        # 深さが一致するかチェック
        depth_match = 'Yes' if (url_depth == breadcrumb_depth and breadcrumb) else ('No' if breadcrumb else 'N/A')

        comparison_data.append({
            'url': page['url'],
            'title': page['title'],
            'url_hierarchy': url_hierarchy_str,
            'url_depth': url_depth,
            'breadcrumb_hierarchy': breadcrumb_str,
            'breadcrumb_depth': breadcrumb_depth,
            'depth_match': depth_match,
            'has_breadcrumb': 'Yes' if breadcrumb else 'No'
        })

    # DataFrameに変換してCSVに保存
    try:
        df = pd.DataFrame(comparison_data)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"階層比較情報を{output_path}にエクスポートしました")
        return output_path
    except Exception as e:
        logger.error(f"CSVエクスポート中にエラーが発生しました: {str(e)}")
        return None


def export_hierarchy_tree_to_json(pages, output_dir='./output', filename=None, hierarchy_type='url'):
    """
    階層ツリー構造をJSON形式でエクスポートする

    Parameters:
    -----------
    pages : list
        ページ情報のリスト
    output_dir : str, optional
        出力先ディレクトリのパス
    filename : str, optional
        出力ファイル名（省略時は日時から自動生成）
    hierarchy_type : str, optional
        'url' または 'breadcrumb'

    Returns:
    --------
    str
        エクスポートされたJSONファイルのパス
    """
    if not pages:
        logger.warning("エクスポートするページが見つかりません")
        return None

    # 出力ディレクトリがなければ作成
    os.makedirs(output_dir, exist_ok=True)

    # ファイル名が指定されていなければ日時から生成
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"hierarchy_tree_{hierarchy_type}_{timestamp}.json"

    # 出力ファイルのフルパス
    output_path = os.path.join(output_dir, filename)

    # 階層ツリーを構築
    from .hierarchy import build_hierarchy_tree

    try:
        tree = build_hierarchy_tree(pages, hierarchy_type)

        # JSONに保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)

        logger.info(f"階層ツリー（{hierarchy_type}）を{output_path}にエクスポートしました")
        return output_path
    except Exception as e:
        logger.error(f"JSONエクスポート中にエラーが発生しました: {str(e)}")
        return None


def export_hierarchy_tree_to_text(pages, output_dir='./output', filename=None, hierarchy_type='url', max_depth=None):
    """
    階層ツリー構造をテキスト形式でエクスポートする

    Parameters:
    -----------
    pages : list
        ページ情報のリスト
    output_dir : str, optional
        出力先ディレクトリのパス
    filename : str, optional
        出力ファイル名（省略時は日時から自動生成）
    hierarchy_type : str, optional
        'url' または 'breadcrumb'
    max_depth : int, optional
        表示する最大深さ

    Returns:
    --------
    str
        エクスポートされたテキストファイルのパス
    """
    if not pages:
        logger.warning("エクスポートするページが見つかりません")
        return None

    # 出力ディレクトリがなければ作成
    os.makedirs(output_dir, exist_ok=True)

    # ファイル名が指定されていなければ日時から生成
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"hierarchy_tree_{hierarchy_type}_{timestamp}.txt"

    # 出力ファイルのフルパス
    output_path = os.path.join(output_dir, filename)

    # 階層ツリーを構築
    from .hierarchy import build_hierarchy_tree, generate_tree_text

    try:
        tree = build_hierarchy_tree(pages, hierarchy_type)
        tree_text = generate_tree_text(tree, max_depth=max_depth)

        # テキストファイルに保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"階層構造ツリー ({hierarchy_type})\n")
            f.write("=" * 50 + "\n\n")
            f.write(tree_text)

        logger.info(f"階層ツリー（{hierarchy_type}）を{output_path}にエクスポートしました")
        return output_path
    except Exception as e:
        logger.error(f"テキストエクスポート中にエラーが発生しました: {str(e)}")
        return None