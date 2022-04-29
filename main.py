import time

from discord import Client, TextChannel, Guild

import config
import discord


class Observer:
    def __init__(self, consult_channel: TextChannel, reviewer_channel: TextChannel,
                 darkmoon_discord: Guild):
        self.consult_channel = consult_channel  # Канал #консультации
        self.reviewer_channel = reviewer_channel  # Канал #рецензенты-помощь
        self.darkmoon_discord = darkmoon_discord  # Сервер даркмуна
        self.darkmoon_role = self.darkmoon_discord.get_role(config.darkmoon_team_role_id).mention  # Роль Darkmoon для упоминания
        self.last_checked_message_date = None  # Сюда записываем дату и время последнего сообщения ПЕРЕД тем, которое без реакции

    async def observe(self):
        while True:
            time.sleep(config.notification_interval)  # Выжидается периодичность напоминания
            messages_queue = await self.check_consult_channel()
            useful_messages = []  # массив для ссылок на неотвеченные консультации
            async for message in messages_queue:
                useful = True
                member = await self.darkmoon_discord.fetch_member(message.author.id)  # забираем ид пользователя
                if member:  # Если чел не на нашем дискорде, то мы ему не отвечаем =)
                    for role in member.roles:
                        if role.id == config.darkmoon_team_role_id:
                            useful = False
                            break  # Сообщения от гмов игнорятся
                    if not useful:  # для того, чтобы не перебирать все роли чела, экономим время
                        continue
                    if not message.reactions:  # нам нужны только сообщения, на которые не нужна реакция
                        useful_messages.append(message.jump_url)
                    else:
                        if not self.last_checked_message_date:
                            self.last_checked_message_date = message.created_at  # Если есть реакция, мы записываем дату
                        # этого сообщения и в следующий раз точно не будем начинать с него
            if len(useful_messages) > 0:  # Постим сообщение, только если ссылки есть
                links = ''
                for link in useful_messages:
                    links += f'{link}\n'
                await self.reviewer_channel.send(self.darkmoon_role)
                await self.reviewer_channel.send(f"{config.notification_message}{links}")

    async def check_consult_channel(self):
        if self.last_checked_message_date is None:  # Бот запишет дату последнего сообщения с реакцией в ряд для того,
            # чтобы не перечитывать все еще раз
            return self.consult_channel.history(oldest_first=True)
        return self.consult_channel.history(oldest_first=True, after=self.last_checked_message_date)


class MyClient(Client):
    async def on_ready(self):
        consult_channel = Client.get_channel(self, id=config.consult_channel_id)
        reviewer_help_channel = Client.get_channel(self, id=config.reviewer_help_channel_id)
        darkmoon_discord = Client.get_guild(self, id=config.server_id)
        observer = Observer(consult_channel, reviewer_help_channel,darkmoon_discord)
        await observer.observe()


client = MyClient()
client.run(config.bot_token)