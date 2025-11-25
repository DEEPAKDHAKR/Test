import discord
from discord.ext import commands

TOKEN = "MTE4MDQ1ODA2NzQwMjQzNjYxOA.G24WTj.Vo1R5SSs6QbRfTdV1R1S0rRATt1Eo4gJfRns9s"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

bot.run(TOKEN)
