import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests

TOKEN = "YOUR_BOT_TOKEN"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Store running uptime tasks
uptime_tasks = {}

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    try:
        await bot.tree.sync()
        print("Slash commands synced.")
    except Exception as e:
        print(e)


# ====================================================
#  /bot url time  → Uptime Monitor Command
# ====================================================
@bot.tree.command(name="bot", description="Keep a website alive by pinging it every few minutes.")
@app_commands.describe(
    url="Website URL (https://example.com)",
    time="Time in minutes after which the bot will check the website again"
)
async def bot_uptime(interaction: discord.Interaction, url: str, time: int):

    # Validate URL
    if not url.startswith("http://") and not url.startswith("https://"):
        await interaction.response.send_message("❌ Please enter a valid URL starting with http:// or https://")
        return

    # Stop old task if exists
    if interaction.user.id in uptime_tasks:
        uptime_tasks[interaction.user.id].cancel()

    # Create new task
    @tasks.loop(minutes=time)
    async def uptime_task():
        try:
            requests.get(url)
            print(f"Pinged: {url}")
        except:
            print(f"Failed to ping: {url}")

    uptime_tasks[interaction.user.id] = uptime_task
    uptime_task.start()

    await interaction.response.send_message(
        f"✅ Bot will now ping **{url}** every **{time} minutes**.\n"
        f"To stop it, type `/stopbot`"
    )


# ====================================================
#   /stopbot → Stop monitoring
# ====================================================
@bot.tree.command(name="stopbot", description="Stop website uptime monitoring.")
async def stop_uptime(interaction: discord.Interaction):

    if interaction.user.id in uptime_tasks:
        uptime_tasks[interaction.user.id].cancel()
        del uptime_tasks[interaction.user.id]
        await interaction.response.send_message("🛑 Website monitoring stopped.")
    else:
        await interaction.response.send_message("❌ You have no running monitoring tasks.")


bot.run(TOKEN)
