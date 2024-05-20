from telegram import Bot
import asyncio


class TelegramBot:
    def __init__(self, token, chat_id):
        self.bot = Bot(token=token)
        self.chat_id = chat_id

    async def send_message(self, message):
        await self.bot.send_message(chat_id=self.chat_id, text=message)
