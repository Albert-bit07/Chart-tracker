"""
Project- Stocks Reader
"""
import yfinance as yf
import pygame,sys,time
from plyer import notification

pygame.mixer.init()
ticker = str(input("Enter ticker:"))
target_price = float(input("Insert Target Price"))
Current_price=0
target_triggered=False
last_price = None
print(f"Tracking {ticker}... waiting for price to cross {target_price}")

while True:
    stock = yf.Ticker(ticker)
    data = stock.history(period ="1d", interval = "1m")
    Current_price = data['Close'].iloc[-1]

    if last_price is not None and not target_triggered:
        if last_price < target_price<= Current_price:
            notification.notify(
                title='Chart tracker',
                message=f'{ticker} has crossed {target_price} upward',
                timeout=10)
            BUY_SELL = input("Buy or Sell: ").capitalize().strip()
            Price_entry = float(input("Enter entry price: "))
            target_triggered=True

        elif last_price>target_price>=Current_price:
            notification.notify(
                title='Chart tracker',
                message=f'{ticker} has crossed {target_price} downward',
                timeout=10)
            BUY_SELL = input("Buy or Sell: ").capitalize().strip()
            Price_entry = float(input("Enter entry price: "))
            target_triggered=True
            
            
    if target_triggered:
        if (BUY_SELL=='Buy' and Current_price > Price_entry
            or BUY_SELL =='Sell' and Current_price < Price_entry) :
            print("In the money")
            pygame.mixer.music.load('Win.mp3')
            pygame.mixer.music.play()

        elif (BUY_SELL=='Buy' and Current_price < Price_entry
              or BUY_SELL =='Sell' and Current_price > Price_entry):
            print("Out the money")
            pygame.mixer.music.load('Lose.mp3')
            pygame.mixer.music.play()

    last_price=Current_price
    time.sleep(60)
        
        



