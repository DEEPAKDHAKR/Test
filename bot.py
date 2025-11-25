import discord
from discord.ext import tasks
from discord import app_commands
import aiohttp
import asyncio

TOKEN = "YOUR_BOT_TOKEN_HERE"

bot = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(bot)

# -------------------------------
# Global Lists
# -------------------------------
monitored_sites = []  # Stores monitored URLs
bot_admins = []       # Stores Bot Admin users

# -------------------------------
# Helper Functions
# -------------------------------
def is_bot_admin(interaction: discord.Interaction):
    """Check if user is Bot Admin or Server Administrator"""
    return interaction.user.id in bot_admins or interaction.user.guild_permissions.administrator

# -------------------------------
# Bot Ready
# -------------------------------
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot is ready! Logged in as {bot.user}")

# -------------------------------
# /bot Command
# -------------------------------
@tree.command(name="bot", description="Start website monitoring (Bot Admin Only)")
@app_commands.describe(url="Website URL", time="Time in seconds to ping")
async def bot_cmd(interaction: discord.Interaction, url: str, time: int):
    if not is_bot_admin(interaction):
        await interaction.response.send_message("❌ You do not have Bot Admin permission!", ephemeral=True)
        return

    monitored_sites.append({
        "url": url,
        "user": interaction.user.name,
        "time": time
    })

    await interaction.response.send_message(
        f"🔵 Monitoring started for **{url}** every **{time} seconds** by **{interaction.user.name}**"
    )

    # Start ping loop
    async def keep_alive():
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get(url) as response:
                        print(f"Pinged {url} — Status: {response.status}")
                except Exception as e:
                    print(f"Error pinging {url}: {e}")
                await asyncio.sleep(time)

    asyncio.create_task(keep_alive())

# -------------------------------
# /stopbot Command
# -------------------------------
@tree.command(name="stopbot", description="Stop monitoring (Bot Admin Only)")
async def stopbot_cmd(interaction: discord.Interaction):
    if not is_bot_admin(interaction):
        await interaction.response.send_message("❌ You do not have Bot Admin permission!", ephemeral=True)
        return

    monitored_sites.clear()
    await interaction.response.send_message("🛑 Monitoring stopped.")

# -------------------------------
# /list Command
# -------------------------------
@tree.command(name="list", description="Show all monitored URLs (Bot Admin Only)")
async def list_cmd(interaction: discord.Interaction):
    if not is_bot_admin(interaction):
        await interaction.response.send_message("❌ You do not have Bot Admin permission!", ephemeral=True)
        return

    if len(monitored_sites) == 0:
        await interaction.response.send_message("❌ No URLs added yet.")
        return

    embed = discord.Embed(
        title="📜 Monitored Websites",
        color=discord.Color.green()
    )

    for site in monitored_sites:
        embed.add_field(
            name=f"🌐 {site['url']}",
            value=f"👤 Added by: {site['user']}\n⏱ Time: {site['time']} seconds",
            inline=False
        )

    embed.set_footer(text="© DEEPAKDHAKR ⚡")
    await interaction.response.send_message(embed=embed)

# -------------------------------
# /adminadd Command
# -------------------------------
@tree.command(name="adminadd", description="Add a member as Bot Admin (Server Admin Only)")
@app_commands.describe(user="Select a member to add as Bot Admin")
async def admin_add_cmd(interaction: discord.Interaction, user: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Only Server Admins can add Bot Admins!", ephemeral=True)
        return

    if user.id in bot_admins:
        await interaction.response.send_message(f"❌ {user.name} is already a Bot Admin.", ephemeral=True)
        return

    bot_admins.append(user.id)
    await interaction.response.send_message(f"✅ {user.name} is now a Bot Admin!")

# -------------------------------
# /adminremove Command
# -------------------------------
@tree.command(name="adminremove", description="Remove a Bot Admin (Server Admin Only)")
@app_commands.describe(user="Select a member to remove from Bot Admin")
async def admin_remove_cmd(interaction: discord.Interaction, user: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Only Server Admins can remove Bot Admins!", ephemeral=True)
        return

    if user.id not in bot_admins:
        await interaction.response.send_message(f"❌ {user.name} is not a Bot Admin.", ephemeral=True)
        return

    bot_admins.remove(user.id)
    await interaction.response.send_message(f"🗑️ {user.name} has been removed from Bot Admins.")

# -------------------------------
# /adminlist Command
# -------------------------------
@tree.command(name="adminlist", description="Show all Bot Admins")
async def admin_list_cmd(interaction: discord.Interaction):
    if not is_bot_admin(interaction):
        await interaction.response.send_message("❌ You do not have Bot Admin permission!", ephemeral=True)
        return

    if len(bot_admins) == 0:
        await interaction.response.send_message("❌ Bot Admin list is empty.")
        return

    embed = discord.Embed(
        title="🛡️ Bot Admin List",
        color=discord.Color.gold()
    )

    for admin_id in bot_admins:
        user = interaction.guild.get_member(admin_id)
        if user:
            embed.add_field(name=user.name, value=f"User ID: {admin_id}", inline=False)

    await interaction.response.send_message(embed=embed)

# -------------------------------
# /help Command
# -------------------------------
@tree.command(name="help", description="Show all bot commands in OP embed")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📘 OP Help Menu",
        description="Niche tumhare bot ke saare commands diye gaye hain:",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🟦 Main Commands",
        value=(
            "**/bot url: time:** Start website monitoring\n"
            "**/stopbot** – Stop monitoring\n"
            "**/list** – Show monitored websites"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ Admin Commands",
        value=(
            "**/adminadd user:** Add a Bot Admin\n"
            "**/adminremove user:** Remove Bot Admin\n"
            "**/adminlist** – Show all Bot Admins"
        ),
        inline=False
    )

    embed.add_field(
        name="⚡ 24/7 Bot Info",
        value="Bot auto-restarts using run.py or VPS screen for 24/7 uptime.",
        inline=False
    )

    embed.set_footer(text="© DEEPAKDHAKR ⚡")
    embed.timestamp = discord.utils.utcnow()

    await interaction.response.send_message(embed=embed)

# -------------------------------
# Run Bot
# -------------------------------
bot.run(TOKEN)
