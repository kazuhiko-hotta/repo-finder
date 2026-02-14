#!/usr/bin/env python3
"""
GitHubに未連携のローカルGitリポジトリを検出するツール
"""

import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import click


def styled(text: str, color: str = "white", bold: bool = False) -> str:
    """テキストに色とスタイルを適用するヘルパー関数"""
    return click.style(text, fg=color, bold=bold)


def get_git_remotes(repo_path: str) -> List[str]:
    """リポジトリのGitリモートURL一覧を取得"""
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []

        remotes = []
        for line in result.stdout.strip().split("\n"):
            if line and len(line.split()) >= 2:
                parts = line.split()
                if len(parts) >= 2:
                    remotes.append(parts[1])
        return list(set(remotes))
    except Exception:
        return []


def has_github_remote(remotes: List[str]) -> bool:
    """リモートリストにGitHubが含まれるかチェック"""
    for remote in remotes:
        if "github.com" in remote:
            return True
    return False


def has_uncommitted_changes(repo_path: str) -> bool:
    """リポジトリに未コミットの変更があるかチェック"""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return False
        # --porcelainは変更がある場合に空でない出力を返す
        return bool(result.stdout.strip())
    except Exception:
        return False


def scan_directory(
    target_path: str, max_depth: int = 1, exclude_patterns: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    ディレクトリをスキャンして未連携リポジトリを検出

    Args:
        target_path: 検索対象のパス
        max_depth: 検索するディレクトリの深さ
        exclude_patterns: 除外するディレクトリ名のリスト

    Returns:
        未連携リポジトリの情報リスト
    """
    if exclude_patterns is None:
        exclude_patterns = ["node_modules", ".venv", "__pycache__", ".idea", ".git"]

    results = []
    target = Path(target_path).resolve()

    if not target.exists():
        return results

    def should_exclude(path: Path) -> bool:
        """パスが除外パターンにマッチするかチェック"""
        for pattern in exclude_patterns:
            if pattern in path.parts:
                return True
        return False

    def scan_at_depth(current_path: Path, current_depth: int):
        """指定された深さでディレクトリをスキャン"""
        if current_depth > max_depth:
            return

        try:
            for item in current_path.iterdir():
                if not item.is_dir():
                    continue

                if should_exclude(item):
                    continue

                if current_depth == max_depth:
                    # 最終深さ: .gitディレクトリをチェック
                    git_dir = item / ".git"
                    if git_dir.exists() and git_dir.is_dir():
                        remotes = get_git_remotes(str(item))
                        uncommitted = has_uncommitted_changes(str(item))

                        if not remotes:
                            results.append(
                                {
                                    "path": str(item),
                                    "status": "no_remote",
                                    "remotes": [],
                                    "uncommitted": uncommitted,
                                }
                            )
                        elif not has_github_remote(remotes):
                            results.append(
                                {
                                    "path": str(item),
                                    "status": "non_github",
                                    "remotes": remotes,
                                    "uncommitted": uncommitted,
                                }
                            )
                else:
                    # 中間深さ: さらに深くスキャン
                    scan_at_depth(item, current_depth + 1)
        except PermissionError:
            pass

    scan_at_depth(target, 1)
    return results


def format_text_output(results: List[Dict[str, Any]]) -> str:
    """結果をテキスト形式でフォーマット（カラー対応）"""
    if not results:
        return styled("未連携のリポジトリは見つかりませんでした。", "bright_black")

    lines = []
    lines.append(styled("=" * 48, "bright_black"))

    for repo in results:
        # [未連携] ラベル（黄色 + 太字）
        lines.append(
            f"{styled('[未連携]', 'bright_yellow', bold=True)} {styled(repo['path'], 'bright_white')}"
        )

        if repo["status"] == "no_remote":
            lines.append(f"  {styled('→', 'cyan')} {styled('リモート未設定', 'cyan')}")
        else:
            remotes_str = ", ".join(repo["remotes"])
            lines.append(
                f"  {styled('→', 'cyan')} {styled('リモート:', 'cyan')} {styled(remotes_str, 'bright_cyan')}"
            )

        # 未コミットの変更がある場合は表示（赤 + 太字）
        if repo.get("uncommitted"):
            lines.append(
                f"  {styled('⚠ 未コミットの変更あり', 'bright_red', bold=True)}"
            )

        lines.append("")

    lines.append(styled("=" * 48, "bright_black"))
    lines.append(styled(f"検出: {len(results)} 件", "bright_green", bold=True))

    return "\n".join(lines)


def format_json_output(results: List[Dict[str, Any]]) -> str:
    """結果をJSON形式でフォーマット"""
    return json.dumps(results, indent=2, ensure_ascii=False)


@click.command(no_args_is_help=True)
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--depth",
    "-d",
    default=1,
    type=int,
    help="検索するディレクトリの深さ（デフォルト: 1）",
)
@click.option(
    "--exclude",
    "-e",
    default="node_modules,.venv,__pycache__,.idea,.git",
    help="除外するディレクトリ（カンマ区切り）",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    default="text",
    type=click.Choice(["text", "json"], case_sensitive=False),
    help="出力形式（text または json）",
)
def main(path: str, depth: int, exclude: str, output_format: str):
    """
    GitHubに未連携のローカルGitリポジトリを検出します。

    PATH: 検索対象のディレクトリパス（デフォルト: カレントディレクトリ）
    """
    exclude_patterns = [p.strip() for p in exclude.split(",") if p.strip()]

    click.echo(
        f"{styled('検索対象:', 'bright_blue', bold=True)} {styled(path, 'bright_white')}"
    )
    click.echo(
        f"{styled('深さ:', 'bright_blue', bold=True)} {styled(str(depth), 'bright_white')}"
    )
    click.echo("")

    results = scan_directory(path, depth, exclude_patterns)

    if output_format.lower() == "json":
        output = format_json_output(results)
    else:
        output = format_text_output(results)

    click.echo(output)


if __name__ == "__main__":
    main()
