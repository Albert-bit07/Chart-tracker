"""Interactive desktop price-crossing monitor; no orders are placed."""
import logging
import math
from pathlib import Path
import time

logger = logging.getLogger(__name__)


def positive_price(value):
    price = float(value)
    if not math.isfinite(price) or price <= 0:
        raise ValueError('Price must be finite and greater than zero')
    return price


def read_price(prompt):
    while True:
        try:
            return positive_price(input(prompt))
        except ValueError as error:
            print(error)


def get_current_price(ticker):
    import yfinance as yf
    try:
        data = yf.Ticker(ticker).history(period='1d', interval='1m')
        return None if data.empty else positive_price(data['Close'].iloc[-1])
    except Exception:
        logger.warning('Price unavailable for %s', ticker, exc_info=True)
        return None


def crossing(previous, current, target):
    if previous is not None:
        if previous < target <= current:
            return 'upward'
        if previous > target >= current:
            return 'downward'
    return None


def position_result(side, current, entry):
    if current == entry:
        return 'even'
    return 'win' if (side == 'buy') == (current > entry) else 'lose'


def play_result(result):
    if result == 'even':
        return
    try:
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        filename = 'Win.mp3' if result == 'win' else 'Lose.mp3'
        pygame.mixer.music.load(str(Path(__file__).resolve().parent / filename))
        pygame.mixer.music.play()
    except Exception:
        logger.warning('Audio unavailable', exc_info=True)


def monitor(ticker, target):
    previous = None
    side = None
    entry = None
    last_result = None
    while True:
        current = get_current_price(ticker)
        if current is None:
            time.sleep(60)
            continue
        direction = crossing(previous, current, target)
        if direction and side is None:
            message = f'{ticker} crossed {target} {direction}'
            print(message)
            try:
                from plyer import notification
                notification.notify(title='Chart tracker', message=message, timeout=10)
            except Exception:
                logger.warning('Desktop notification unavailable', exc_info=True)
            while side not in ('buy', 'sell'):
                side = input('Buy or Sell: ').strip().lower()
            entry = read_price('Enter entry price: ')
        elif side is not None:
            result = position_result(side, current, entry)
            if result != last_result:
                print({'win': 'In the money', 'lose': 'Out of the money', 'even': 'At entry price'}[result])
                play_result(result)
                last_result = result
        previous = current
        time.sleep(60)


def main():
    try:
        ticker = ''
        while not ticker:
            ticker = input('Enter ticker: ').strip().upper()
        target = read_price('Insert target price: ')
        print(f'Tracking {ticker}... waiting for price to cross {target}')
        monitor(ticker, target)
    except (KeyboardInterrupt, EOFError):
        print('\nTracking stopped.')


if __name__ == '__main__':
    main()
