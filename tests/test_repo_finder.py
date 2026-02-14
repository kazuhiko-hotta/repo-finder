"""
Repo Finderのユニットテストと統合テスト
"""

import os
import json
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from repo_finder import (
    get_git_remotes,
    has_github_remote,
    has_uncommitted_changes,
    scan_directory,
    format_text_output,
    format_json_output,
    main,
)


class TestGetGitRemotes:
    """get_git_remotes関数のテスト"""

    def test_get_git_remotes_success(self):
        """正常にリモートURLを取得できる場合"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="origin  https://github.com/user/repo.git (fetch)\n"
                "origin  https://github.com/user/repo.git (push)\n"
                "upstream  https://gitlab.com/user/repo.git (fetch)\n",
            )
            result = get_git_remotes("/tmp/test")

            assert len(result) == 2
            assert "https://github.com/user/repo.git" in result
            assert "https://gitlab.com/user/repo.git" in result

    def test_get_git_remotes_no_remotes(self):
        """リモートが設定されていない場合"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            result = get_git_remotes("/tmp/test")

            assert result == []

    def test_get_git_remotes_git_error(self):
        """gitコマンドが失敗する場合"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            result = get_git_remotes("/tmp/test")

            assert result == []

    def test_get_git_remotes_exception(self):
        """例外が発生する場合"""
        with patch("subprocess.run", side_effect=Exception("Command failed")):
            result = get_git_remotes("/tmp/test")

            assert result == []


class TestHasGithubRemote:
    """has_github_remote関数のテスト"""

    def test_has_github_remote_true(self):
        """GitHubリモートがある場合"""
        remotes = ["https://github.com/user/repo.git", "git@github.com:user/repo.git"]
        assert has_github_remote(remotes) is True

    def test_has_github_remote_false(self):
        """GitHubリモートがない場合"""
        remotes = [
            "https://gitlab.com/user/repo.git",
            "https://bitbucket.org/user/repo.git",
        ]
        assert has_github_remote(remotes) is False

    def test_has_github_remote_empty(self):
        """リモートリストが空の場合"""
        assert has_github_remote([]) is False


class TestHasUncommittedChanges:
    """has_uncommitted_changes関数のテスト"""

    def test_has_uncommitted_changes_true(self):
        """未コミットの変更がある場合"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=" M modified_file.txt\n?? untracked_file.txt\n",
            )
            result = has_uncommitted_changes("/tmp/test")

            assert result is True

    def test_has_uncommitted_changes_false(self):
        """未コミットの変更がない場合"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            result = has_uncommitted_changes("/tmp/test")

            assert result is False

    def test_has_uncommitted_changes_git_error(self):
        """gitコマンドが失敗する場合"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            result = has_uncommitted_changes("/tmp/test")

            assert result is False

    def test_has_uncommitted_changes_exception(self):
        """例外が発生する場合"""
        with patch("subprocess.run", side_effect=Exception("Command failed")):
            result = has_uncommitted_changes("/tmp/test")

            assert result is False


class TestScanDirectory:
    """scan_directory関数のテスト"""

    @pytest.fixture
    def temp_dir(self):
        """テスト用の一時ディレクトリ"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_scan_no_git_repos(self, temp_dir):
        """Gitリポジトリがない場合"""
        result = scan_directory(str(temp_dir), max_depth=1)
        assert result == []

    def test_scan_with_git_no_remote(self, temp_dir):
        """.gitがあるがリモートがない場合"""
        repo_dir = temp_dir / "test-repo"
        repo_dir.mkdir()
        git_dir = repo_dir / ".git"
        git_dir.mkdir()

        with patch("repo_finder.get_git_remotes", return_value=[]):
            with patch("repo_finder.has_uncommitted_changes", return_value=False):
                result = scan_directory(str(temp_dir), max_depth=1)

        assert len(result) == 1
        assert result[0]["path"] == str(repo_dir)
        assert result[0]["status"] == "no_remote"
        assert result[0]["uncommitted"] is False

    def test_scan_with_git_github_remote(self, temp_dir):
        """.gitがありGitHubリモートがある場合（除外される）"""
        repo_dir = temp_dir / "github-repo"
        repo_dir.mkdir()
        git_dir = repo_dir / ".git"
        git_dir.mkdir()

        with patch(
            "repo_finder.get_git_remotes",
            return_value=["https://github.com/user/repo.git"],
        ):
            with patch("repo_finder.has_uncommitted_changes", return_value=False):
                result = scan_directory(str(temp_dir), max_depth=1)

        assert result == []

    def test_scan_with_git_other_remote(self, temp_dir):
        """.gitがありGitHub以外のリモートがある場合"""
        repo_dir = temp_dir / "gitlab-repo"
        repo_dir.mkdir()
        git_dir = repo_dir / ".git"
        git_dir.mkdir()

        with patch(
            "repo_finder.get_git_remotes",
            return_value=["https://gitlab.com/user/repo.git"],
        ):
            with patch("repo_finder.has_uncommitted_changes", return_value=False):
                result = scan_directory(str(temp_dir), max_depth=1)

        assert len(result) == 1
        assert result[0]["status"] == "non_github"
        assert "gitlab.com" in result[0]["remotes"][0]
        assert result[0]["uncommitted"] is False

    def test_scan_excludes_patterns(self, temp_dir):
        """除外パターンが機能するか"""
        # 除外すべきディレクトリ
        node_modules = temp_dir / "node_modules"
        node_modules.mkdir()
        (node_modules / ".git").mkdir()

        # 通常のディレクトリ
        normal_repo = temp_dir / "normal-repo"
        normal_repo.mkdir()
        (normal_repo / ".git").mkdir()

        with patch("repo_finder.get_git_remotes", return_value=[]):
            with patch("repo_finder.has_uncommitted_changes", return_value=False):
                result = scan_directory(str(temp_dir), max_depth=1)

        assert len(result) == 1
        assert "node_modules" not in result[0]["path"]

    def test_scan_respects_depth(self, temp_dir):
        """深さ制限が機能するか"""
        # 深さ2のディレクトリ構造
        level1 = temp_dir / "level1"
        level1.mkdir()
        level2 = level1 / "level2"
        level2.mkdir()
        (level2 / ".git").mkdir()

        with patch("repo_finder.get_git_remotes", return_value=[]):
            with patch("repo_finder.has_uncommitted_changes", return_value=False):
                # 深さ1では検出されない
                result_depth1 = scan_directory(str(temp_dir), max_depth=1)
                assert len(result_depth1) == 0

                # 深さ2で検出される
                result_depth2 = scan_directory(str(temp_dir), max_depth=2)
                assert len(result_depth2) == 1


class TestFormatOutput:
    """出力フォーマット関数のテスト"""

    def test_format_text_output_empty(self):
        """空の結果をテキスト形式で表示"""
        result = format_text_output([])
        assert "見つかりませんでした" in result

    def test_format_text_output_with_results(self):
        """結果がある場合のテキスト形式"""
        data = [
            {
                "path": "/home/user/repo1",
                "status": "no_remote",
                "remotes": [],
                "uncommitted": False,
            },
            {
                "path": "/home/user/repo2",
                "status": "non_github",
                "remotes": ["https://gitlab.com/user/repo.git"],
                "uncommitted": True,
            },
        ]
        result = format_text_output(data)

        assert "repo1" in result
        assert "repo2" in result
        assert "リモート未設定" in result
        assert "gitlab.com" in result
        assert "検出: 2 件" in result
        assert "未コミットの変更あり" in result

    def test_format_json_output(self):
        """JSON形式での出力"""
        data = [
            {
                "path": "/home/user/repo",
                "status": "no_remote",
                "remotes": [],
                "uncommitted": True,
            }
        ]
        result = format_json_output(data)

        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["path"] == "/home/user/repo"
        assert parsed[0]["status"] == "no_remote"
        assert parsed[0]["uncommitted"] is True


class TestCLI:
    """CLI統合テスト"""

    @pytest.fixture
    def runner(self):
        """Clickテストランナー"""
        return CliRunner()

    def test_cli_help(self, runner):
        """ヘルプメッセージの表示"""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "未連携" in result.output
        assert "--depth" in result.output
        assert "--format" in result.output

    def test_cli_default_options(self, runner, tmp_path):
        """デフォルトオプションで実行"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, [str(tmp_path)])
            assert result.exit_code == 0
            assert "検索対象" in result.output

    def test_cli_json_format(self, runner, tmp_path):
        """JSON形式での出力"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, [str(tmp_path), "--format", "json"])
            assert result.exit_code == 0
            # JSONとしてパース可能か確認
            lines = result.output.split("\n")
            json_line = None
            for line in lines:
                if line.strip().startswith("["):
                    json_line = line
                    break
            if json_line:
                json.loads(json_line)

    def test_cli_with_git_repo(self, runner, tmp_path):
        """実際のGitリポジトリでのテスト"""
        repo_dir = tmp_path / "test-repo"
        repo_dir.mkdir()

        # git initを実行
        subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True)

        result = runner.invoke(main, [str(tmp_path)])
        assert result.exit_code == 0
        assert "test-repo" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
