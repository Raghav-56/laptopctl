import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).with_name('laptopctl')


class DesktopCommands(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.log = self.root / 'calls.jsonl'
        program = '''#!/usr/bin/env python3
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['CALL_LOG'], 'a') as f:
    f.write(json.dumps([name, *args]) + '\\n')
if name == 'sudo':
    sys.exit(0)
if args[:3] == ['--user', 'is-enabled', '--quiet']:
    sys.exit(0 if os.environ.get('HAS_KRDP') == '1' else 1)
if args[:3] == ['--user', 'is-active', '--quiet']:
    target = args[-1]
    key = 'KDE_RUNNING' if target == 'plasma-core.target' else 'KRDP_RUNNING'
    sys.exit(0 if os.environ.get(key) == '1' else 1)
if 'is-active' in args:
    print('active')
elif args[:1] == ['show']:
    print('sddm.service')
elif 'status' in args:
    print('service status')
'''
        for command in ('systemctl', 'sudo'):
            path = self.root / command
            path.write_text(program)
            path.chmod(0o755)
        self.env = os.environ.copy()
        self.env.pop('LAPTOPCTL_RDP_BACKEND', None)
        self.env.update(PATH=str(self.root) + os.pathsep + self.env['PATH'],
                        CALL_LOG=str(self.log), HAS_KRDP='0', KDE_RUNNING='1')

    def run_cli(self, *args):
        return subprocess.run(['bash', str(SCRIPT), *args], env=self.env,
                              text=True, capture_output=True)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_gui_controls_the_configured_display_manager(self):
        self.assertEqual(self.run_cli('gui', 'on').returncode, 0)
        self.assertEqual(self.calls(), [['sudo', 'systemctl', 'start', 'display-manager.service']])

    def test_enabled_krdp_uses_user_scope_without_sudo(self):
        self.env['HAS_KRDP'] = '1'
        result = self.run_cli('rdp', 'on')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(['systemctl', '--user', 'start', 'app-org.kde.krdpserver.service'], self.calls())
        self.assertFalse(any(call[0] == 'sudo' for call in self.calls()))

    def test_krdp_off_does_not_stop_the_desktop(self):
        self.env['HAS_KRDP'] = '1'
        self.assertEqual(self.run_cli('rdp', 'off').returncode, 0)
        self.assertEqual(self.calls()[-1], ['systemctl', '--user', 'stop', 'app-org.kde.krdpserver.service'])

    def test_xrdp_fallback_preserves_service_order(self):
        self.assertEqual(self.run_cli('rdp', 'on').returncode, 0)
        self.assertEqual(self.calls()[-1], ['sudo', 'systemctl', 'start', 'xrdp-sesman', 'xrdp'])

    def test_explicit_xrdp_overrides_installed_krdp(self):
        self.env.update(HAS_KRDP='1', LAPTOPCTL_RDP_BACKEND='xrdp')
        self.assertEqual(self.run_cli('rdp', 'off').returncode, 0)
        self.assertEqual(self.calls(), [['sudo', 'systemctl', 'stop', 'xrdp', 'xrdp-sesman']])

    def test_krdp_requires_a_running_kde_session(self):
        self.env.update(HAS_KRDP='1', KDE_RUNNING='0')
        result = self.run_cli('rdp', 'on')
        self.assertEqual(result.returncode, 1)
        self.assertIn('laptopctl gui on', result.stderr)
        self.assertFalse(any('start' in call for call in self.calls()))

    def test_status_uses_the_selected_provider(self):
        self.env['HAS_KRDP'] = '1'
        result = self.run_cli('rdp', 'status')
        self.assertEqual(result.stdout, 'service status\n')
        self.assertEqual(self.calls()[-1], ['systemctl', '--user', 'status', 'app-org.kde.krdpserver.service', '--no-pager'])

    def test_invalid_backend_cannot_run_a_command(self):
        self.env['LAPTOPCTL_RDP_BACKEND'] = 'other'
        self.assertEqual(self.run_cli('rdp', 'on').returncode, 2)
        self.assertFalse(self.log.exists())


if __name__ == '__main__':
    unittest.main()
