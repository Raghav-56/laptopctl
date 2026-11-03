import importlib.machinery
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import types
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader('storage', str(Path(__file__).with_name('laptopctl-storage')))
spec = importlib.util.spec_from_loader(loader.name, loader)
storage = importlib.util.module_from_spec(spec)
loader.exec_module(storage)

HEADER = 'User,BlockStatus,FileStatus,BlockUsed,BlockSoftLimit,BlockHardLimit,BlockGrace,FileUsed,FileSoftLimit,FileHardLimit,FileGrace\n'
ROW = '#1234,-,-,1048576,0,2097152,0,42,100,200,0\n'


class StorageCommands(unittest.TestCase):
    def invoke(self, args, outputs):
        calls = []

        def run(command, **kwargs):
            calls.append(command)
            if command[0] == 'repquota':
                return subprocess.CompletedProcess(command, 0, next(outputs), '')
            return subprocess.CompletedProcess(command, 0)

        user = types.SimpleNamespace(pw_name='alice', pw_uid=1234)
        with patch.object(sys, 'argv', ['laptopctl-storage', *args]), \
             patch.object(storage.os, 'geteuid', return_value=0), \
             patch.object(storage.pwd, 'getpwnam', return_value=user), \
             patch.object(storage.subprocess, 'run', side_effect=run), \
             redirect_stdout(io.StringIO()) as output:
            storage.main()
        return calls, output.getvalue()

    def test_set_preserves_inode_limits_and_reports_result(self):
        calls, output = self.invoke(['set', 'alice', '4G'], iter([HEADER + ROW, HEADER + ROW.replace('2097152', '4194304')]))
        self.assertIn(['setquota', '-u', '1234', '0', '4194304', '100', '200', '/'], calls)
        self.assertIn('1.00 GiB used   limit 4.00 GiB', output)

    def test_rejects_limit_below_usage(self):
        with self.assertRaisesRegex(storage.StorageError, 'refusing a lower limit'):
            self.invoke(['set', 'alice', '512M'], iter([HEADER + ROW]))

    def test_missing_record_is_unlimited_and_remove_preserves_inodes(self):
        _, output = self.invoke(['status', 'alice'], iter([HEADER]))
        self.assertIn('0.00 GiB used   limit unlimited', output)
        calls, _ = self.invoke(['remove', 'alice'], iter([HEADER + ROW, HEADER + ROW]))
        self.assertIn(['setquota', '-u', '1234', '0', '0', '100', '200', '/'], calls)

    def test_rejects_unrecognized_report(self):
        with self.assertRaisesRegex(storage.StorageError, 'cannot interpret'):
            self.invoke(['status', 'alice'], iter(['unexpected output']))


if __name__ == '__main__':
    unittest.main()
