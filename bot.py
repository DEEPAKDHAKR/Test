import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import asyncio
from mcstatus import JavaServer

# -------------------------------
# Bot & Intents
# -------------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# -------------------------------
# Global Variables
# -------------------------------
monitored_sites = []   # Websites to monitor
bot_admins = []        # Bot Admin IDs
server_ip = None
server_port = None
log_channel_id = None

# -------------------------------
# Helper Function
# -------------------------------
def is_bot_admin(interaction: discord.Interaction):
    return interaction.user.id in bot_admins or interaction.user.guild_permissions.administrator

# -------------------------------
# BOT READY
# -------------------------------
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot is online as {bot.user}")
    server_status_loop.start()
    website_monitor_loop.start()

# -------------------------------
# /ping Command
# -------------------------------
@tree.command(name="ping", description="Check bot latency")
async def ping_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Ping: {round(bot.latency*1000)} ms")

# -------------------------------
# /help Command
# -------------------------------
@tree.command(name="help", description="Show all bot commands")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📘 OP Help Menu",
        description="Niche tumhare bot ke saare commands diye gaye hain:",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🟦 Main Commands",
        value=(
            "`/bot url: time:` Start website monitoring\n"
            "`/stopbot` – Stop monitoring\n"
            "`/list` – Show monitored websites\n"
            "`/ping` – Check bot latency"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ Admin Commands",
        value=(
            "`/adminadd user:` Add a Bot Admin\n"
            "`/adminremove user:` Remove Bot Admin\n"
            "`/adminlist` – Show all Bot Admins"
        ),
        inline=False
    )

    embed.add_field(
        name="🎮 Minecraft Server Commands",
        value=(
            "`/serverjoin ip port:` Connect bot to Minecraft server\n"
            "`/serverchannel channel:` Set server log channel\n"
            "`/mc command:` Run Minecraft command (RCON required)\n"
            "`/serverstatus:` Instant server status check"
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
# /bot Command (website monitor)
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

# Website Monitor Loop
@tasks.loop(seconds=5)
async def website_monitor_loop():
    async with aiohttp.ClientSession() as session:
        for site in monitored_sites:
            try:
                async with session.get(site['url']) as resp:
                    print(f"Pinged {site['url']} — Status: {resp.status}")
            except Exception as e:
                print(f"Error pinging {site['url']}: {e}")

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
@tree.command(name="list", description="Show monitored websites")
async def list_cmd(interaction: discord.Interaction):
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

    await interaction.response.send_message(embed=embed)

# -------------------------------
# Admin Commands
# -------------------------------
@tree.command(name="adminadd", description="Add a Bot Admin (Server Admin Only)")
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

@tree.command(name="adminlist", description="Show all Bot Admins")
async def admin_list_cmd(interaction: discord.Interaction):
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
# Minecraft Commands
# -------------------------------
@tree.command(name="serverjoin", description="Connect bot to Minecraft server")
@app_commands.describe(ip="Minecraft server IP", port="Minecraft server port")
async def server_join_cmd(interaction: discord.Interaction, ip: str, port: int):
    global server_ip, server_port
    server_ip = ip
    server_port = port
    await interaction.response.send_message(f"✅ Server Connected!\nIP: {ip}\nPort: {port}")

@tree.command(name="serverchannel", description="Set channel for Minecraft server updates")
@app_commands.describe(channel="Select a channel")
async def server_channel_cmd(interaction: discord.Interaction, channel: discord.TextChannel):
    global log_channel_id
    log_channel_id = channel.id
    await interaction.response.send_message(f"📌 Server log channel set to: {channel.mention}")

@tree.command(name="serverstatus", description="Check Minecraft server status")
async def server_status_cmd(interaction: discord.Interaction):
    if not server_ip or not server_port:
        await interaction.response.send_message("❌ Server not connected.")
        return

    try:
        server = JavaServer.lookup(f"{server_ip}:{server_port}")
        status = server.status()
        await interaction.response.send_message(f"🟢 Server Online — Players: {status.players.online}")
    except:
        await interaction.response.send_message("🔴 Server Offline")

@tree.command(name="mc", description="Run command on Minecraft server")
@app_commands.describe(command="Minecraft command to run")
async def mc_cmd(interaction: discord.Interaction, command: str):
    await interaction.response.send_message("⚡ MC command execution feature requires RCON setup (not included)")

# -------------------------------
# Minecraft Server Loop
# -------------------------------
@tasks.loop(seconds=15)
async def server_status_loop():
    if not server_ip or not server_port or not log_channel_id:
        return
    channel = bot.get_channel(log_channel_id)
    if not channel:
        return

    try:
        server = JavaServer.lookup(f"{server_ip}:{server_port}")
        status = server.status()
        await channel.send(f"🟢 Server Online — Players: {status.players.online}")
    except:
        await channel.send("🔴 Server Offline")

# -------------------------------
# Run Bot
# -------------------------------
bot.run("YOUR_BOT_TOKEN_HERE")@app_commands.describe(user="Select a member to add as Bot Admin")
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
