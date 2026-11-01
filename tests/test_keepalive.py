from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'keepalive.sh'


class KeepaliveTests(unittest.TestCase):
    def run_git(self, cwd, *args, env=None):
        return subprocess.check_output(['git', *args], cwd=cwd, env=env, text=True).strip()

    def make_repository(self, root, age):
        remote = root / 'origin.git'
        local = root / 'checkout'
        self.run_git(root, 'init', '--bare', '--initial-branch=main', str(remote))
        self.run_git(root, 'clone', str(remote), str(local))
        self.run_git(local, 'config', 'user.name', 'Calendar test')
        self.run_git(local, 'config', 'user.email', 'test@example.invalid')
        (local / 'feed.ics').write_text('unchanged subscription data\n')
        self.run_git(local, 'add', 'feed.ics')
        stamp = (datetime.now(timezone.utc) - timedelta(days=age)).isoformat()
        env = dict(os.environ, GIT_AUTHOR_DATE=stamp, GIT_COMMITTER_DATE=stamp)
        self.run_git(local, 'commit', '-m', 'Initial calendar', env=env)
        self.run_git(local, 'push', 'origin', 'main')
        return local, remote

    def test_inactive_repository_gets_one_empty_commit_and_recent_run_is_noop(self):
        with tempfile.TemporaryDirectory() as temp:
            local, remote = self.make_repository(Path(temp), 31)
            original = self.run_git(local, 'rev-parse', 'HEAD')
            tree = self.run_git(local, 'rev-parse', 'HEAD^{tree}')
            subprocess.run(['bash', str(SCRIPT)], cwd=local, check=True, capture_output=True)
            new_head = self.run_git(local, 'rev-parse', 'HEAD')
            self.assertNotEqual(new_head, original)
            self.assertEqual(self.run_git(local, 'rev-parse', 'HEAD^{tree}'), tree)
            self.assertEqual(self.run_git(remote, 'rev-parse', 'main'), new_head)
            subprocess.run(['bash', str(SCRIPT)], cwd=local, check=True, capture_output=True)
            self.assertEqual(self.run_git(local, 'rev-parse', 'HEAD'), new_head)

    def test_failed_push_is_reported_and_remote_is_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            local, remote = self.make_repository(Path(temp), 31)
            original = self.run_git(remote, 'rev-parse', 'main')
            hook = remote / 'hooks' / 'pre-receive'
            hook.write_text('#!/bin/sh\nexit 1\n')
            hook.chmod(0o755)
            result = subprocess.run(['bash', str(SCRIPT)], cwd=local, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(self.run_git(remote, 'rev-parse', 'main'), original)
