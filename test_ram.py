import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch


loader = importlib.machinery.SourceFileLoader('ram', str(Path(__file__).with_name('laptopctl-ram')))
spec = importlib.util.spec_from_loader(loader.name, loader)
ram = importlib.util.module_from_spec(spec)
loader.exec_module(ram)
G = 1024 ** 3


class RamCommands(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.values = {'MemoryHigh': str(6 * G), 'MemoryMax': str(8 * G),
                       'MemorySwapMax': str(2 * G), 'MemoryCurrent': str(G)}
        self.applied = []
        self.calls = []
        self.fail_timer = False
        self.patch('STATE_DIR', Path(self.temp.name))
        self.patch('account_named', lambda _: types.SimpleNamespace(pw_uid=61111, pw_name='test-account'))
        self.patch('properties', lambda _: self.values.copy())
        self.patch('memory_info', lambda: {'MemTotal': 24 * G, 'SwapTotal': 8 * G})
        self.patch('runtime_override', lambda _: Path(self.temp.name) / 'runtime.conf')
        self.patch('apply', self.apply)
        self.patch('command', self.command)

    def patch(self, name, value):
        context = patch.object(ram, name, value)
        context.start()
        self.addCleanup(context.stop)

    def apply(self, uid, values, runtime):
        self.values.update({key: str(value) for key, value in values.items()})
        self.applied.append((values.copy(), runtime))

    def command(self, *args):
        self.calls.append(args)
        if args[0] == 'systemd-run' and self.fail_timer:
            raise ram.RamError('timer unavailable')
        return 'not-found' if args[:2] == ('systemctl', 'show') else ''

    def change(self, *args):
        ram.change(ram.parser().parse_args(list(args)))

    def test_boost_restores_original_limits(self):
        self.change('boost', 'test-account', '12G', '--high', '10G', '--for', '2h')
        self.assertEqual(self.values['MemoryMax'], str(12 * G))
        state = ram.read_state(61111)
        self.assertEqual(state['baseline']['MemoryMax'], str(8 * G))
        self.assertTrue(ram.runtime_override(61111).exists())
        self.assertTrue(ram.restore(61111, state['token']))
        self.assertEqual(self.values['MemoryMax'], str(8 * G))
        self.assertIsNone(ram.read_state(61111))
        self.assertFalse(ram.runtime_override(61111).exists())

    def test_renewal_retains_original_baseline_and_ignores_stale_timer(self):
        self.change('boost', 'test-account', '12G')
        old = ram.read_state(61111)
        self.change('boost', 'test-account', '14G')
        new = ram.read_state(61111)
        self.assertNotEqual(old['token'], new['token'])
        self.assertFalse(ram.restore(61111, old['token']))
        self.assertEqual(self.values['MemoryMax'], str(14 * G))
        ram.restore(61111, new['token'])
        self.assertEqual(self.values['MemoryMax'], str(8 * G))

    def test_owner_boost_restores_owner_baseline(self):
        self.values.update(MemoryHigh=str(20 * G), MemoryMax=str(22 * G), MemorySwapMax=str(7 * G))
        self.change('boost', 'test-account', '23G')
        ram.restore(61111)
        self.assertEqual(self.values['MemoryHigh'], str(20 * G))
        self.assertEqual(self.values['MemoryMax'], str(22 * G))
        self.assertEqual(self.values['MemorySwapMax'], str(7 * G))

    def test_permanent_change_ends_boost(self):
        self.change('boost', 'test-account', '12G')
        self.change('set', 'test-account', '10G', '--high', '8G', '--swap', '3G')
        self.assertIsNone(ram.read_state(61111))
        self.assertEqual(self.values['MemoryMax'], str(10 * G))
        self.assertFalse(self.applied[-1][1])

    def test_timer_failure_leaves_baseline_and_no_state(self):
        self.fail_timer = True
        with self.assertRaisesRegex(ram.RamError, 'timer unavailable'):
            self.change('boost', 'test-account', '12G')
        self.assertEqual(self.values['MemoryMax'], str(8 * G))
        self.assertIsNone(ram.read_state(61111))

    def test_validation_failures_do_not_change_caps(self):
        for args in [('25G',), ('8G', '--high', '9G'), ('8G', '--swap', '9G'), ('0',)]:
            with self.subTest(args=args), self.assertRaises(ram.RamError):
                self.change('set', 'test-account', *args)
        self.assertEqual(self.applied, [])

    def test_lowering_below_usage_requires_force(self):
        self.values['MemoryCurrent'] = str(9 * G)
        with self.assertRaisesRegex(ram.RamError, 'current usage exceeds'):
            self.change('set', 'test-account', '8G')
        self.change('set', 'test-account', '8G', '--force')
        self.assertEqual(self.values['MemoryMax'], str(8 * G))

    def test_restore_without_boost_does_nothing(self):
        self.assertFalse(ram.restore(61111))
        self.assertEqual(self.applied, [])

    def test_status_includes_login_users_and_excludes_service_accounts(self):
        self.assertTrue(ram.is_login_account(types.SimpleNamespace(pw_uid=1004, pw_shell='/bin/bash')))
        self.assertFalse(ram.is_login_account(types.SimpleNamespace(pw_uid=65532, pw_shell='/usr/sbin/nologin')))
        self.assertFalse(ram.is_login_account(types.SimpleNamespace(pw_uid=0, pw_shell='/bin/bash')))

    def test_sizes_and_durations(self):
        self.assertEqual(ram.size('512MiB'), 512 * 1024 ** 2)
        self.assertEqual(ram.size('8G'), 8 * G)
        self.assertEqual(ram.duration('2h'), 7200)
        self.assertEqual(ram.duration('30m'), 1800)
        for value in ['infinity', '-1G', '8G;id']:
            with self.assertRaises(Exception):
                ram.size(value)
        for value in ['0s', '-2h', '2h;id']:
            with self.assertRaises(Exception):
                ram.duration(value)


if __name__ == '__main__':
    unittest.main()
