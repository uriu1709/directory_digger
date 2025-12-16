"""
階層構造の分析と比較を行うユーティリティモジュール
"""

def build_hierarchy_tree(pages, hierarchy_type='url'):
    """
    ページリストから階層ツリー構造を構築する

    Parameters:
    -----------
    pages : list
        ページ情報のリスト
    hierarchy_type : str
        'url' または 'breadcrumb' - どちらの階層を使用するか

    Returns:
    --------
    dict
        階層ツリー構造
    """
    tree = {}

    for page in pages:
        if hierarchy_type == 'url':
            hierarchy = page.get('url_hierarchy', [])
        elif hierarchy_type == 'breadcrumb':
            hierarchy = page.get('breadcrumb', [])
        else:
            continue

        if not hierarchy:
            continue

        # ツリーに階層を追加
        current = tree
        for level, item in enumerate(hierarchy):
            if item not in current:
                current[item] = {
                    '_pages': [],
                    '_children': {}
                }
            current[item]['_pages'].append({
                'url': page['url'],
                'title': page['title'],
                'depth': level
            })
            current = current[item]['_children']

    return tree


def compare_hierarchies(pages):
    """
    URL階層とパンくず階層を比較し、差異を検出する

    Parameters:
    -----------
    pages : list
        ページ情報のリスト

    Returns:
    --------
    list
        比較結果のリスト。各要素は以下のキーを持つ辞書:
        - url: ページURL
        - title: ページタイトル
        - url_hierarchy: URL階層（文字列）
        - breadcrumb_hierarchy: パンくず階層（文字列）
        - url_depth: URL階層の深さ
        - breadcrumb_depth: パンくず階層の深さ
        - depth_match: 深さが一致するかどうか
        - has_breadcrumb: パンくずが存在するか
    """
    comparison_results = []

    for page in pages:
        url_hierarchy = page.get('url_hierarchy', [])
        breadcrumb = page.get('breadcrumb', [])
        url_depth = page.get('url_depth', 0)
        breadcrumb_depth = page.get('breadcrumb_depth', 0)

        # 階層を文字列に変換
        url_hierarchy_str = ' > '.join(url_hierarchy) if url_hierarchy else ''
        breadcrumb_hierarchy_str = ' > '.join(breadcrumb) if breadcrumb else ''

        # 深さが一致するかチェック
        depth_match = (url_depth == breadcrumb_depth) if breadcrumb else None

        comparison_results.append({
            'url': page['url'],
            'title': page['title'],
            'url_hierarchy': url_hierarchy_str,
            'breadcrumb_hierarchy': breadcrumb_hierarchy_str,
            'url_depth': url_depth,
            'breadcrumb_depth': breadcrumb_depth,
            'depth_match': depth_match,
            'has_breadcrumb': bool(breadcrumb)
        })

    return comparison_results


def generate_tree_text(tree, indent=0, max_depth=None):
    """
    階層ツリーをテキスト形式で生成する

    Parameters:
    -----------
    tree : dict
        階層ツリー構造
    indent : int
        現在のインデントレベル
    max_depth : int, optional
        表示する最大深さ（Noneの場合は無制限）

    Returns:
    --------
    str
        テキスト形式のツリー
    """
    if max_depth is not None and indent >= max_depth:
        return ""

    lines = []
    items = [(k, v) for k, v in tree.items() if not k.startswith('_')]

    for i, (key, value) in enumerate(items):
        is_last = (i == len(items) - 1)
        prefix = "└── " if is_last else "├── "
        continuation = "    " if is_last else "│   "

        # ページ数を取得
        page_count = len(value.get('_pages', []))
        lines.append(f"{'    ' * indent}{prefix}{key} ({page_count})")

        # 子要素を再帰的に処理
        children = value.get('_children', {})
        if children:
            child_text = generate_tree_text(children, indent + 1, max_depth)
            if child_text:
                # 継続線を追加
                child_lines = child_text.split('\n')
                for line in child_lines:
                    if line:
                        lines.append(f"{'    ' * indent}{continuation}{line}")

    return '\n'.join(lines)


def flatten_hierarchy(pages, hierarchy_type='url'):
    """
    階層構造をフラットなリストに変換する

    Parameters:
    -----------
    pages : list
        ページ情報のリスト
    hierarchy_type : str
        'url' または 'breadcrumb'

    Returns:
    --------
    list
        フラット化された階層リスト。各要素は以下のキーを持つ辞書:
        - level: 階層レベル（0から始まる）
        - path: 階層パス（文字列）
        - pages: このレベルに属するページのリスト
    """
    hierarchy_dict = {}

    for page in pages:
        if hierarchy_type == 'url':
            hierarchy = page.get('url_hierarchy', [])
        elif hierarchy_type == 'breadcrumb':
            hierarchy = page.get('breadcrumb', [])
        else:
            continue

        if not hierarchy:
            continue

        # 各階層レベルを記録
        for level, item in enumerate(hierarchy):
            path = ' > '.join(hierarchy[:level + 1])
            if path not in hierarchy_dict:
                hierarchy_dict[path] = {
                    'level': level,
                    'path': path,
                    'pages': []
                }
            hierarchy_dict[path]['pages'].append({
                'url': page['url'],
                'title': page['title']
            })

    # ソートして返す
    return sorted(hierarchy_dict.values(), key=lambda x: (x['level'], x['path']))
