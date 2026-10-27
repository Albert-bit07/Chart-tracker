import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('tracker', Path(__file__).resolve().parents[1] / 'Project Stock reader.py')
tracker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracker)

class TrackerTests(unittest.TestCase):
    def test_main_stops_cleanly_during_prompts_or_monitoring(self):
        for exception in (KeyboardInterrupt, EOFError):
            for phase in ('ticker', 'target', 'monitor'):
                with self.subTest(exception=exception.__name__, phase=phase):
                    inputs = [exception()] if phase == 'ticker' else ['AAPL', exception()] if phase == 'target' else ['AAPL', '10']
                    with patch('builtins.input', side_effect=inputs), \
                         patch.object(tracker, 'monitor', side_effect=exception()) as monitor, \
                         patch('builtins.print') as output:
                        try:
                            tracker.main()
                        except (KeyboardInterrupt, EOFError):
                            self.fail('Normal user interruption escaped main')
                    self.assertIn(('\nTracking stopped.',), [call.args for call in output.call_args_list])
                    if phase == 'monitor':
                        monitor.assert_called_once_with('AAPL', 10)
                    else:
                        monitor.assert_not_called()

    def test_cli_eof_exits_without_traceback(self):
        for input_text in ('', 'AAPL\n'):
            with self.subTest(input_text=input_text):
                result = subprocess.run([sys.executable, tracker.__file__], input=input_text,
                    capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('Tracking stopped.', result.stdout)
                self.assertEqual(result.stderr, '')

    def test_position_alert_uses_quote_fetched_after_entry_input(self):
        # The user may spend minutes answering the entry prompts. The quote
        # that triggered those prompts must not produce a position alert.
        with patch.object(tracker, 'get_current_price', side_effect=[9, 11, None, 8, KeyboardInterrupt]), \
             patch.object(tracker.time, 'sleep') as sleep, \
             patch('builtins.input', side_effect=['buy', '10']), \
             patch.object(tracker, 'play_result') as audio, \
             patch('plyer.notification.notify'):
            with self.assertRaises(KeyboardInterrupt):
                tracker.monitor('AAPL', 10)
        self.assertEqual([call.args[0] for call in audio.call_args_list], ['lose'])
        self.assertEqual(sleep.call_count, 4)

    def test_positive_prices(self):
        for value in ['bad', 'nan', 'inf', '-1', '0']:
            with self.assertRaises(ValueError):
                tracker.positive_price(value)
        self.assertEqual(tracker.positive_price('1.25'), 1.25)

    def test_crossing_boundaries(self):
        self.assertEqual(tracker.crossing(9, 10, 10), 'upward')
        self.assertEqual(tracker.crossing(11, 10, 10), 'downward')
        self.assertIsNone(tracker.crossing(10, 11, 10))
        self.assertIsNone(tracker.crossing(None, 11, 10))

    def test_quote_failure_recovers_without_repeating_audio(self):
        with patch.object(tracker, 'get_current_price', side_effect=[None, 9, 11, 12, 8, KeyboardInterrupt]), patch.object(tracker.time, 'sleep') as sleep, patch('builtins.input', side_effect=['buy', '10']), patch.object(tracker, 'play_result') as audio, patch('plyer.notification.notify'):
            with self.assertRaises(KeyboardInterrupt):
                tracker.monitor('AAPL', 10)
            self.assertEqual([call.args[0] for call in audio.call_args_list], ['win', 'lose'])
            self.assertEqual(sleep.call_count, 5)

    def test_empty_and_invalid_provider_data(self):
        import pandas as pd
        with patch('yfinance.Ticker') as ticker:
            for values in [[], [float('nan')]]:
                ticker.return_value.history.return_value = pd.DataFrame({'Close': values})
                self.assertIsNone(tracker.get_current_price('AAPL'))

    def test_short_and_break_even(self):
        self.assertEqual(tracker.position_result('sell', 9, 10), 'win')
        self.assertEqual(tracker.position_result('sell', 11, 10), 'lose')
        self.assertEqual(tracker.position_result('buy', 10, 10), 'even')
