import pandas as pd
import os
from datetime import datetime
import logging

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