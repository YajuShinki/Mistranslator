import discord
import logging
import mistranslate as mt

#Initial setup
logging.basicConfig(level=logging.INFO)

class BotClient(discord.Client):
    async def on_ready(self):
        print('Login successful. User ID: {0}'.format(self.user))
        
    async def on_message(self,message):
        if message.author == client.user:
            return
        #Parse input
        if message.content.startswith('mistl!'):
            
        
client = BotClient()
client.run()
