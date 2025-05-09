import os
import asyncio
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
from telegram import Update
from tabulate import tabulate
from telegram.ext import Application, MessageHandler, filters, CallbackContext

def fetch_stock_data():
    url = "https://chartink.com/screener/process"
    condition = {"scan_clause": "( {cash} ( latest high > 3 days ago high and latest volume > 2000000 ) ) "}
    
    try:
        with requests.session() as s:
            r_data = s.get(url)
            soup = bs(r_data.content, "lxml")
            meta = soup.find("meta", {'name': 'csrf-token'})["content"]
            
            header = {"x-csrf-token": meta}
            data = s.post(url, headers=header, data=condition).json()
            stock_list = pd.DataFrame(data["data"])
            stock_list = stock_list[(stock_list["close"] >= 300) & (stock_list["close"] <= 3000)]
            stock_list = stock_list[['name', 'close']]
            if stock_list.empty:
                return "No data found."
            stock_list = tabulate(stock_list, headers='keys', tablefmt='grid')
            return stock_list
    except Exception as e:
        return f"Error fetching data: {str(e)}"

async def handle_message(update: Update, context: CallbackContext) -> None:
    stock_list = fetch_stock_data()
    if stock_list != "No data found." and not stock_list.startswith("Error"):
        for i in range(0, len(stock_list), 4096):
            await update.message.reply_text(stock_list[i:i + 4096])
    else:
        await update.message.reply_text(stock_list)

def main():
    
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    bot_token = os.getenv("TG_BOT_TOKEN")
    # bot_token = "7181361938:AAGa1F2naro72PuXeyNfBFJPXtklnjJmyDQ"
    app = Application.builder().token(bot_token).build()
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == '__main__':
    main()
