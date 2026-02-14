# repo-finder (AI用圧縮版)

## TL;DR
GitHub未連携ローカルGitリポジトリ検出CLI。Python+Click。カラー出力対応。24テスト通過。

## コマンド
```bash
pip3 install repo-finder                    # インストール
repo-finder /path/to/search --depth 1       # 実行
pytest                                      # テスト
```

## 依存
- click>=8.0.0
- pytest>=7.0.0 (dev)

## ファイル構成
```
repo_finder.py      # メイン（CLIエントリポイント）
pyproject.toml      # 設定
README.md           # ユーザードキュメント
MEMORY.md           # このファイル
tests/              # 24個のpytestテスト
.venv/              # 仮想環境（.gitignore）
```

## 主要関数
- `scan_directory(path, depth, exclude)` → 未連携リポジトリ検出
- `get_git_remotes(path)` → git remote結果取得
- `has_github_remote(remotes)` → GitHub URL判定
- `has_uncommitted_changes(path)` → 未コミット変更検出
- `styled(text, color, bold)` → カラー出力用ヘルパー
- `main()` → Click CLI

## 検出ロジック
```python
if .git exists and not has_github_remote(get_git_remotes(path)):
    report_repo(path, status="no_remote|non_github", uncommitted=bool)
```

## カラースキーム
- `styled()` ヘルパー関数で統一管理
- 青: 見出し、黄: ラベル、白: パス
- シアン: 情報、赤: 警告、緑: 成功

## GitHub
https://github.com/kazuhiko-hotta/repo-finder

## 機能
- [x] 未連携リポジトリ検出
- [x] 未コミット変更検出
- [x] カラー出力
- [x] JSON/テキスト出力
- [x] 24個のテスト

## 拡張案
CI/CD、PyPI自動公開、並列処理、設定ファイル
