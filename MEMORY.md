# repo-finder (AI用圧縮版)

## TL;DR
GitHub未連携ローカルGitリポジトリ検出CLI。Python+Click。20テスト通過。

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
tests/              # 20個のpytestテスト
.venv/              # 仮想環境（.gitignore）
```

## 主要関数
- `scan_directory(path, depth, exclude)` → 未連携リポジトリ検出
- `get_git_remotes(path)` → git remote結果取得
- `has_github_remote(remotes)` → GitHub URL判定
- `main()` → Click CLI

## 検出ロジック
```python
if .git exists and not has_github_remote(get_git_remotes(path)):
    report_repo(path, status="no_remote|non_github")
```

## GitHub
https://github.com/kazuhiko-hotta/repo-finder

## 拡張案
CI/CD、PyPI自動公開、並列処理、設定ファイル
