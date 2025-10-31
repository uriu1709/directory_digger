# Directory Digger

ウェブサイトのディレクトリ構造を探索し、CSVファイルにまとめるデスクトップアプリケーションです。指定したウェブサイトのページを巡回し、ページ情報、外部リンク、リンク切れなどの情報を収集します。

## 機能

- ウェブサイトのページを再帰的に探索
- ページ情報（URL、タイトル、キーワード、ディスクリプション）を収集
- 外部リンクとリンク切れを検出
- 結果をCSVファイルにエクスポート
- マルチスレッドで高速処理
- わかりやすいGUIインターフェース
- リクエスト間の遅延や最大ページ数などの設定が可能

### 新機能：階層構造分析

- **パンくずリスト自動抽出**: ページ内のパンくずリストを自動的に検出・抽出
- **URL階層分析**: URLパス構造から階層を自動計算
- **階層比較機能**: URL階層とパンくず階層の整合性をチェック
- **ツリー構造出力**: 階層構造をツリー形式でテキストまたはJSON形式でエクスポート
- **不一致検出**: URL構造とパンくず構造の差異を自動検出

## インストール方法

### 実行可能ファイル（EXE）を使用する方法

Windowsユーザーは、[リリースページ](https://github.com/uriu1709/directory_digger/releases)から最新の`DirectoryDigger.exe`をダウンロードして直接実行できます。インストール不要で使用できます。

### Pythonから実行する方法

#### 前提条件

- Python 3.7以上
- pip (Pythonパッケージマネージャー)

#### セットアップ手順

1. リポジトリをクローンするか、ZIPファイルとしてダウンロードします
   ```
   git clone https://github.com/yourusername/directory_digger.git
   cd directory_digger
   ```

2. 必要なパッケージをインストールします
   ```
   pip install -r requirements.txt
   ```

## 使用方法

### アプリケーションの起動

EXEファイルを使用する場合は、ダウンロードした`DirectoryDigger.exe`をダブルクリックして実行します。

Pythonから実行する場合は以下のコマンドを使用します：
```
python src/main.py
```

### 基本的な使い方

1. 「開始URL」に探索を開始したいウェブサイトのURLを入力します
2. 必要に応じてクロール設定を調整します
   - 最大ページ数: 処理するページ数の上限（0=無制限）
   - 遅延: リクエスト間の待機時間（秒）
   - ワーカー数: 並行して実行するスレッド数
3. 「クロール開始」ボタンをクリックして探索を開始します
4. 探索が完了したら「CSVエクスポート」ボタンをクリックして結果を保存します

## エクスポートされるファイル

### 基本ファイル

1. **ページ情報CSV** (`pages_YYYYMMDD_HHMMSS.csv`)
   - URL、ページタイトル、キーワード、ディスクリプション
   - パンくずリスト（抽出された場合）
   - URL階層とパンくず階層の深さ

2. **外部リンクCSV** (`external_links_YYYYMMDD_HHMMSS.csv`)
   - リンク先URL、リンク元ページURL

3. **リンク切れCSV** (`broken_links_YYYYMMDD_HHMMSS.csv`)
   - リンク切れURL、リンク元ページURL

### 階層構造ファイル（オプション）

4. **階層比較CSV** (`hierarchy_comparison_YYYYMMDD_HHMMSS.csv`)
   - 各ページのURL階層とパンくず階層を比較
   - 階層の深さ、一致/不一致の判定
   - パンくずの有無

5. **URL階層ツリー** (`hierarchy_tree_url_YYYYMMDD_HHMMSS.txt`)
   - URLパス構造に基づく階層ツリーをテキスト形式で出力
   - 視覚的にわかりやすいツリー表示

6. **パンくず階層ツリー** (`hierarchy_tree_breadcrumb_YYYYMMDD_HHMMSS.txt`)
   - パンくずリストに基づく階層ツリーをテキスト形式で出力

7. **JSON形式ツリー** (`hierarchy_tree_*.json`)
   - 階層構造をJSON形式で出力（プログラムでの再利用に便利）

## 開発情報

### プロジェクト構造

```
directory_digger/
├── docs/               # ドキュメント
├── resources/          # リソースファイル
├── src/                # ソースコード
│   ├── crawler/
│   │   └── crawler.py     # クローリング機能（パンくず抽出、URL階層解析）
│   ├── gui/
│   │   └── main_window.py # GUIコンポーネント
│   ├── utils/
│   │   ├── export.py      # CSV/JSON/テキストエクスポート機能
│   │   └── hierarchy.py   # 階層構造分析・比較機能（NEW!）
│   └── main.py            # アプリケーションエントリーポイント
├── tests/
│   ├── test_crawler.py    # クローラーテスト
│   ├── test_export.py     # エクスポートテスト
│   └── test_hierarchy.py  # 階層機能テスト（NEW!）
├── requirements.txt       # 依存パッケージ
└── README.md              # このファイル
```

### テストの実行

```
python -m unittest discover -s tests
```

## 階層構造分析の活用例

### パンくずリスト抽出

以下の形式のパンくずリストを自動的に検出します：

- `aria-label="breadcrumb"` を持つ `<nav>` 要素
- `class="breadcrumb"` を持つリスト要素
- Schema.org の BreadcrumbList 形式

### URL階層 vs パンくず階層の比較

エクスポートされた `hierarchy_comparison_*.csv` を開くと、以下のような情報が確認できます：

```csv
url,title,url_hierarchy,url_depth,breadcrumb_hierarchy,breadcrumb_depth,depth_match,has_breadcrumb
https://example.com/,Home,/,1,ホーム,1,Yes,Yes
https://example.com/p/12345,Product,/ > p > 12345,3,ホーム > 製品 > スマホ,3,Yes,Yes
https://example.com/about,About,/ > about,2,,0,N/A,No
```

これにより以下が分かります：
- どのページにパンくずリストがあるか
- URL構造とパンくず構造が一致しているか
- 階層の深さの差異

### ツリー構造の確認

`hierarchy_tree_url_*.txt` を開くと、以下のような視覚的なツリーが表示されます：

```
/ (10)
├── products (5)
│   ├── electronics (3)
│   │   └── phones (2)
│   └── clothing (2)
└── about (1)
```

これにより、サイト全体の構造を一目で把握できます。

## トラブルシューティング

- **クロール中にエラーが発生する場合**: サーバーへのリクエスト頻度が高すぎる可能性があります。「遅延」の値を大きくしてみてください。
- **メモリ使用量が多い場合**: 「最大ページ数」を制限するか、「ワーカー数」を減らしてみてください。

## ライセンス

MIT

## 貢献

バグ報告や機能リクエストは、Issueを作成してください。プルリクエストも歓迎します。