# Repo Finder

指定されたディレクトリ配下から、GitHubに未連携のローカルGitリポジトリを検出するツール。

## 依存関係

- Python 3.8以上
- click 8.0.0以上

## インストール

### 方法1: pipで直接インストール（推奨）

```bash
pip3 install repo-finder
```

PyPIから最新版をインストールできます。

### 方法2: GitHubからインストール

```bash
pip3 install git+https://github.com/kazuhiko-hotta/repo-finder.git
```

### 方法3: ローカルで開発・実行

```bash
cd repo_finder
pip3 install -e .
```

`pyproject.toml`に記載された依存関係（click）が自動的にインストールされます。

### pyproject.toml

```toml
[project]
dependencies = [
    "click>=8.0.0",
]
```

## 使い方

```bash
# カレントディレクトリ直下を検索（深さ1）
python repo_finder.py

# 特定のディレクトリを指定
python repo_finder.py /home/user/projects

# 検索深さを変更（デフォルト: 1）
python repo_finder.py /home/user/projects --depth 2

# JSON形式で出力
python repo_finder.py --format json

# 除外パターンをカスタマイズ
python repo_finder.py --exclude node_modules,build,dist
```

## オプション

| オプション | 短縮形 | デフォルト | 説明 |
|-----------|--------|-----------|------|
| `--depth` | `-d` | 1 | 検索するディレクトリの深さ |
| `--exclude` | `-e` | `node_modules,.venv,__pycache__,.idea,.git` | 除外するディレクトリ |
| `--format` | `-f` | `text` | 出力形式 (`text` または `json`) |

## 出力例

### テキスト形式（デフォルト・カラー対応）

ターミナル出力はカラー表示に対応しています：

```
検索対象: /home/user/projects
深さ: 1
================================
[未連携] /home/user/projects/my-app
  → リモート未設定
  ⚠ 未コミットの変更あり

[未連携] /home/user/projects/legacy-tool
  → リモート: https://gitlab.com/user/repo.git

================================
検出: 2 件
```

**カラースキーム:**
- 見出し: 青（太字）
- `[未連携]` ラベル: 黄色（太字）
- パス: 白
- 情報テキスト: シアン
- 未コミット警告: 赤（太字）
- 検出件数: 緑（太字）

### JSON形式

```json
[
  {
    "path": "/home/user/projects/my-app",
    "status": "no_remote",
    "remotes": [],
    "uncommitted": true
  },
  {
    "path": "/home/user/projects/legacy-tool",
    "status": "non_github",
    "remotes": ["https://gitlab.com/user/repo.git"],
    "uncommitted": false
  }
]
```

**フィールド説明:**
- `path`: リポジトリのパス
- `status`: `no_remote`（リモート未設定）または `non_github`（GitHub以外）
- `remotes`: 設定されているリモートURLのリスト
- `uncommitted`: 未コミットの変更があるかどうか（true/false）

## 検出条件

- `.git` ディレクトリが存在する
- 以下のいずれかを満たす:
  - Gitリモートが設定されていない
  - GitリモートがGitHub以外（GitLab, Bitbucket等）

## 注意事項

- Gitがインストールされている必要があります
- 除外パターンはディレクトリ名の部分一致で判定されます
