import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('tracker', Path(__file__).resolve().parents[1] / 'Project Stock reader.py')
tracker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracker)

class TrackerTests(unittest.TestCase):
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
