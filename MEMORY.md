# repo-finder MEMORY

## プロジェクト概要
GitHubに未連携のローカルGitリポジトリを検出するCLIツール

## 重要なファイル
- `repo_finder.py` - メインスクリプト（エントリーポイント）
- `pyproject.toml` - プロジェクト設定と依存関係
- `README.md` - 仕様書と使い方
- `tests/test_repo_finder.py` - テストスイート（20個のテスト）
- `.gitignore` - venvとキャッシュファイルを除外

## 技術スタック
- Python 3.8+
- Click 8.0.0+ (CLIフレームワーク)
- pytest (テスト)

## 主要機能
1. 指定パス直下のディレクトリをスキャン（デフォルト深さ1）
2. `.git`ディレクトリを持つリポジトリを検出
3. GitHubリモートがないものをリストアップ
4. テキスト/JSON出力形式対応

## インストール方法
```bash
pip3 install repo-finder
# または
pip3 install git+https://github.com/kazuhiko-hotta/repo-finder.git
```

## 使い方
```bash
repo-finder /path/to/search          # 基本使用
repo-finder --depth 2                # 深さ変更
repo-finder --format json            # JSON出力
repo-finder --exclude node_modules   # 除外パターン
```

## GitHubリポジトリ
https://github.com/kazuhiko-hotta/repo-finder

## 開発メモ
- venvを使用: `source .venv/bin/activate`
- テスト実行: `pytest`
- 全20個のテストが通過済み

## 依存関係
```toml
[project]
dependencies = ["click>=8.0.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "pytest-cov>=4.0.0"]
```

## 除外パターン（デフォルト）
- node_modules
- .venv
- __pycache__
- .idea
- .git

## 検出条件
1. `.git`ディレクトリが存在
2. 以下のいずれか:
   - Gitリモート未設定
   - GitリモートがGitHub以外（GitLab, Bitbucket等）

## 出力形式
- **テキスト**: 人間が読みやすい形式（デフォルト）
- **JSON**: 他ツール連携用

## 今後の拡張案（メモ）
- [ ] GitHub ActionsでのCI/CD
- [ ] PyPIへの自動公開
- [ ] 設定ファイル対応
- [ ] 並列処理による高速化
- [ ] インタラクティブモード
