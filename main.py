import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import logging
import re
from discord import app_commands, TextStyle
import json
import aiohttp
import asyncio
import os
import time
from discord.ui import Modal, TextInput, View, Button
from discord.ext import tasks
from discord import Interaction, ui
import pytz
import random
import string
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
import traceback

wc = "<:Accepted:1434344224211472527>"
wx = "<:Denied:1434345307336085647>"

def get_prefix(bot, message):
    return ['$', f'<@{bot.user.id}>']

bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, intents=discord.Intents.all())

logging.basicConfig(level=logging.INFO)
startTime = datetime.now()

class PaginatorView(View):
    def __init__(self, embeds: list, user_id: int = None, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current = 0
        self.user_id = user_id
        self.message = None
        self.update_buttons()
    
    def update_buttons(self):
        self.prev_button.disabled = (self.current == 0)
        self.next_button.disabled = (self.current == len(self.embeds) - 1)
        self.page_button.label = f"{self.current + 1}/{len(self.embeds)}"
    
    @discord.ui.button(emoji="<:left:1455102275684008092>", style=discord.ButtonStyle.primary, disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        if self.user_id and interaction.user.id != self.user_id:
            return await interaction.response.send_message(f"{wx} You are not allowed to interact with this menu.", ephemeral=True)
        
        if self.current > 0:
            self.current -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current], view=self)
    
    @discord.ui.button(label="1/1", style=discord.ButtonStyle.secondary, disabled=True)
    async def page_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
    
    @discord.ui.button(emoji="<:right:1455102274564001814>", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if self.user_id and interaction.user.id != self.user_id:
            return await interaction.response.send_message(f"{wx} You are not allowed to interact with this menu.", ephemeral=True)
        
        if self.current < len(self.embeds) - 1:
            self.current += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current], view=self)
    
    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except:
                pass

async def paginate(interaction: discord.Interaction, embeds: list, timeout: int = 180):
    if not embeds or len(embeds) == 0:
        raise ValueError("Embeds list cannot be empty")
    
    if len(embeds) == 1:
        return await interaction.response.send_message(embed=embeds[0])
    
    view = PaginatorView(embeds, user_id=interaction.user.id, timeout=timeout)
    await interaction.response.send_message(embed=embeds[0], view=view)
    view.message = await interaction.original_response()
    return view.message

@bot.command()
async def partner(ctx):
    allowed_roles = [1421277606275452970]
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        return
    await ctx.message.delete()
    member_count = ctx.guild.member_count

    def round_to_nearest_25(n):
        return int(round(n / 25.0) * 25)

    roleplay_required = round_to_nearest_25(member_count / 3)
    design_required = round_to_nearest_25(member_count / 3)
    community_required = round_to_nearest_25(member_count / 3)

    embed = discord.Embed(
        description=(
            f"### <:partner:1365413714164973781> Partnership Info\n"
            f"**Roleplay Servers Required Members:** `{roleplay_required}`\n"
            f"**Design Servers Required Members:** `{design_required}`\n"
            f"**Community Servers Required Members:** `{community_required}`\n\n"
            f"- Must be Related to ER:LC\n"
            f"- Server cannot have a bad history\n"
            f"- Server must be relatively active\n"
            f"- Professional/Non-Corrupt Ownership and Staff\n\n"
            f"### 🔁 Merge Information\n"
            f"-# We **do not** merge into servers, we only accept merges **into us**\n"
            f"- `250–1500 members`: Moderation to High-Ranking Supervisor\n"
            f"- `1500–3000 members`: Supervisor to Management\n"
            f"- `2000+ members`: Ownership will evaluate\n\n"
            f"- Must be Related to ER:LC\n"
            f"- Server cannot have a bad history\n"
            f"- Server **MUST** be active\n"
            f"- Professional/Non-Corrupt Ownership and Staff"
        ),
        color=0x2b2d31
    )
    await ctx.send(embed=embed)

class Application(app_commands.Group):
    def __init__(self):
        super().__init__(name="application", description="Manage staff applications")

    async def has_required_role(self, user: discord.Member) -> bool:
        required_roles = [1421270212229206117, 1421270212367487139]
        return any(role.id in required_roles for role in user.roles)

    @app_commands.command(name="result", description="Approve or deny a staff application.")
    @app_commands.describe(result="Select the application result.")
    @app_commands.choices(result=[  
        app_commands.Choice(name="Approved", value="approved"),
        app_commands.Choice(name="Denied", value="denied")
    ])
    async def result(self, interaction: discord.Interaction, member: discord.Member, result: app_commands.Choice[str], notes: str = None):
        if not await self.has_required_role(interaction.user):
            return await interaction.response.send_message(f"{wx} You do not have permission to use this command.", ephemeral=True)

        target_channel_id = 1421269122607612155
        await interaction.response.defer(ephemeral=True)

        is_approved = result.value == "approved"
        color = discord.Color.green() if is_approved else discord.Color.red()
        action_text = "Approved" if is_approved else "Denied"
        embed_title = f"Ohio State Roleplay | Staff Application | Response {action_text}"
        description = f"After careful review, **{member.name}**'s staff application has been {action_text.lower()}."

        embed = discord.Embed(title=embed_title, description=description, color=color)
        embed.set_footer(text=f'Application: Ohio State Roleplay | Staff Application | ID: {member.id}')
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        if notes:
            embed.add_field(name="Notes", value=notes, inline=False)

        target_channel = interaction.client.get_channel(target_channel_id)
        if target_channel:
            await target_channel.send(f"{member.mention}", embed=embed)
        else:
            return await interaction.followup.send(f"{wx} Results channel not found.", ephemeral=True)
        print(f"Attempting to send DM to {member.name}")

        try:
            dm_embed = discord.Embed(
                title=f"Application {action_text}",
                description=f"{'Congratulations' if is_approved else 'Unfortunately'} **{member.name}**, your application for Ohio State Roleplay staff has been {action_text.lower()}.",
                color=color,
                timestamp=datetime.now()
            )
            dm_embed.add_field(name="Server", value="Ohio State Roleplay", inline=False)
            dm_embed.set_author(name=member.name, icon_url=member.display_avatar.url)
            if notes:
                dm_embed.add_field(name="Notes", value=notes, inline=False)
            await member.send(embed=dm_embed)
            print(f"Successfully sent DM to {member.name}")
        except discord.errors.Forbidden:
            print(f"Failed to send DM to {member.name}. Permission denied.")

        if is_approved:
            role_ids = [1421269172502925362, 1421269170506567850]
            roles = [discord.Object(id=role_id) for role_id in role_ids]
            try:
                await member.add_roles(*roles)
                print(f"Successfully assigned roles to {member.name}")
            except Exception as e:
                print(f"Error assigning roles to {member.name}: {str(e)}")

        await interaction.followup.send(f"{wc} {action_text} {member.name}'s application.", ephemeral=True)
bot.tree.add_command(Application())

@bot.command(name='uptime', aliases=["ping"])
@commands.cooldown(1, 5.0, commands.BucketType.user)
async def uptime(ctx):
    now = datetime.now()
    delta = now - startTime
    days, remainder = divmod(int(delta.total_seconds()), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    uptime_response = f"<:greendot:1376906735993749545> **Uptime:**"
    if days > 0:
        uptime_response += f" {days} days,"
    if hours > 0:
        uptime_response += f" {hours} hours,"
    if minutes > 0:
        uptime_response += f" {minutes} minutes,"
    if seconds > 0:
        uptime_response += f" {seconds} seconds."

    ping = round(bot.latency * 1000)
    response = f"{uptime_response.strip(', ')}\n-# Ping: {ping} ms."
    await ctx.send(response)

API_BASE_URL = "https://api.policeroleplay.community/v1"
API_KEY = "VkoHSOpkdWklhvhrGDPb-ahJHwHXrWcPpliTHUcHKPGpZPTkuIASfdTgONwGY"

API_BANS_URL = f"{API_BASE_URL}/server/bans"

async def fetch_erlc_data():
    retry_attempts = 3
    attempt = 0

    while attempt < retry_attempts:
        try:
            headers = {'server-key': API_KEY}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE_URL}/server", headers=headers) as response:
                    if response.status == 200:
                        try:
                            if 'application/json' in response.headers.get('Content-Type', ''):
                                data = await response.json()
                                currentplayers = data.get("CurrentPlayers", 0)
                                return currentplayers
                            return 0
                        except ValueError:
                            return 0
                    if response.status == 502:
                        attempt += 1
                        await asyncio.sleep(2)
                        continue
                    return 0
        except aiohttp.ClientError:
            return 0
    return 0

async def fetch_erlc_players():
    retry_attempts = 3
    attempt = 0
    while attempt < retry_attempts:
        try:
            headers = {'server-key': API_KEY}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE_URL}/server/players", headers=headers) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            return data if isinstance(data, list) else []
                        except ValueError:
                            return []
                    if response.status == 502:
                        attempt += 1
                        await asyncio.sleep(2)
                        continue
                    return []
        except aiohttp.ClientError:
            return []
    return []

async def fetch_erlc_queue():
    retry_attempts = 3
    attempt = 0

    while attempt < retry_attempts:
        try:
            headers = {'server-key': API_KEY}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE_URL}/server/queue", headers=headers) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            if isinstance(data, dict):
                                return data.get("queue_count", 0)
                            if isinstance(data, list):
                                return len(data)
                            return 0
                        except ValueError:
                            return 0
                    if response.status == 502:
                        attempt += 1
                        await asyncio.sleep(2)
                        continue
                    return 0
        except aiohttp.ClientError:
            return 0
    return 0

async def fetch_erlc_bans():
    retry_attempts = 3
    attempt = 0

    while attempt < retry_attempts:
        try:
            headers = {"server-key": API_KEY}
            async with aiohttp.ClientSession() as session:
                async with session.get(API_BANS_URL, headers=headers) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            return data if isinstance(data, dict) else {}
                        except ValueError:
                            return {}
                    if response.status == 502:
                        attempt += 1
                        await asyncio.sleep(2)
                        continue
                    return {}
        except aiohttp.ClientError:
            return {}
    return {}

async def unban_player(player_id):
    print(f"DEBUG: sending unban for player_id {player_id}")
    await input_erlc_command(f":unban {player_id}")
    await asyncio.sleep(6)

async def unban_all_bans():
    bans = await fetch_erlc_bans()
    print("DEBUG: fetched bans:", bans)

    if not bans:
        print("DEBUG: bans is empty")
        return

    for player_id in bans:
        print(f"DEBUG: unbanning player_id {player_id}, username {bans[player_id]}")
        await unban_player(player_id)

@bot.command(name="unbanall")
async def unban_all_command(ctx):
    if ctx.author.id != 973619439822049330:
        return await ctx.send(f"{wx} You do not have permission to use this command.")

    bans = await fetch_erlc_bans()
    if not bans:
        return await ctx.send(f"{wx} No bans found.")

    amount_of_bans = len(bans)
    now = int(time.time())
    estimated_finish = now + (amount_of_bans * 6)

    await ctx.send(f"{wc} Starting unban process... This should be done <t:{estimated_finish}:R>")

    for player_id in bans:
        await unban_player(player_id)

    await ctx.send(f"{wc} Unban process finished.")

async def fetch_and_print_bans():
    headers = {"server-key": API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(API_BANS_URL, headers=headers) as response:
            data = await response.json()
            print(data)

@bot.command(name="printbans")
async def print_bans(ctx):
    if ctx.author.id != 973619439822049330:
        return await ctx.send(f"{wx} You do not have permission to use this command.")
    
    headers = {"server-key": API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(API_BANS_URL, headers=headers) as response:
            data = await response.json()
            print(data)

async def get_server_info(last_updated_time, bot):
    currentplayers = await fetch_erlc_data()
    queue_count = await fetch_erlc_queue()
    guild = bot.get_guild(1421266702326435912)
    role = guild.get_role(1434345009569595472)
    online_staff_count = len(role.members)
    
    embed_color = 0x2b2d31
    server_code = "ohioVC"

    image_embed = discord.Embed(color=embed_color)
    image_embed.set_image(
        url="https://cdn.discordapp.com/attachments/1414792429688852530/1441271029665366177/Copy_of_Ohioassets_3.png?ex=69646c3e&is=69631abe&hm=d241bd79f1aadf27866118f6ee10e3fd7472413421f9ebbc9e914cfb846e1bf8&")

    info_embed1 = discord.Embed(
        color=embed_color,
        description=f"## Ohio State Sessions\n- Ohio State Roleplay sessions are up to 24/7 other than the few sessions breaks.\n- The current session has been active since: **Unknown**"
    )
    info_embed1.set_image(url="https://trident.bot/assets/invisible.png")

    info_embed2 = discord.Embed(
        title="<:session:1421906928283418837> ERLC Server Information",
        color=embed_color,
    )
    info_embed2.add_field(name="**Server Name:**", value="Ohio State Roleplay I VC Only", inline=True)
    info_embed2.add_field(name="**Server Owner:**", value="Urnixss", inline=True)
    info_embed2.add_field(name="**Server Code:**", value="ohioVC", inline=True)
    info_embed2.set_image(url="https://trident.bot/assets/invisible.png")

    info_embed3 = discord.Embed(
        title="<:session:1421906928283418837> Server Status",
        color=embed_color,
        description=f"**Last Updated:** <t:{last_updated_time}:R>"
    )
    info_embed3.add_field(name="**Player Count:**", value=f"```{currentplayers}```", inline=True)
    info_embed3.add_field(name="**Online Staff:**", value=f"```{online_staff_count}```", inline=True)
    info_embed3.add_field(name="**In Queue:**", value=f"```{queue_count}```", inline=True)
    info_embed3.set_image(url="https://cdn.discordapp.com/attachments/1414792429688852530/1441281523704926360/OHIO_STATE_ROLEPLAY_3.png?ex=69647604&is=69632484&hm=ab23b421a16a5a1dc28522d4df8a44dd95e6513957637f3384d5960d513260d5&")

    join_button = Button(
        label="Quick Join",
        style=discord.ButtonStyle.link,
        url="https://policeroleplay.community/join/ohioVC"
    )
    view = View(timeout=None)
    view.add_item(join_button)
    await check_server_full(currentplayers, bot)
    return [image_embed, info_embed1, info_embed2, info_embed3], currentplayers

server_full_message_id = None
server_full_timestamp = None

SERVER_FULL_FILE = "server_full.json"

def save_server_full_message_id(message_id):
    data = {"server_full_message_id": message_id}
    with open(SERVER_FULL_FILE, "w") as f:
        json.dump(data, f)

def load_server_full_message_id():
    if os.path.exists(SERVER_FULL_FILE):
        with open(SERVER_FULL_FILE, "r") as f:
            data = json.load(f)
            return data.get("server_full_message_id")
    return None

async def check_server_full(currentplayers, bot):
    global server_full_message_id, server_full_timestamp
    full_channel = bot.get_channel(1421268025323159693)
    if not full_channel:
        return
    server_full_message_id = load_server_full_message_id()

    if currentplayers >= 39:
        if server_full_message_id:
            try:
                previous_message = await full_channel.fetch_message(server_full_message_id)
                if previous_message and previous_message.embeds:
                    for embed in previous_message.embeds:
                        if embed.title and embed.title == "Server Full":
                            return
            except discord.NotFound:
                server_full_message_id = None
        async for message in full_channel.history(limit=20):
            if message.embeds:
                for embed in message.embeds:
                    if embed.title and embed.title == "Server Full":
                        server_full_message_id = message.id
                        save_server_full_message_id(server_full_message_id)
                        return
        if not server_full_timestamp:
            server_full_timestamp = int(time.time())
        image_embed = discord.Embed(color=0x2b2d31)
        image_embed.set_image(url="https://cdn.discordapp.com/attachments/1414792429688852530/1441271029665366177/Copy_of_Ohioassets_3.png?ex=69646c3e&is=69631abe&hm=d241bd79f1aadf27866118f6ee10e3fd7472413421f9ebbc9e914cfb846e1bf8&")
        embed = discord.Embed(
            title="Server Full",
            description=f"Ohio State Roleplay has been full since <t:{server_full_timestamp}:R>. Keep joining as spots will open shortly.",
            color=0x2b2d31
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1414792429688852530/1441281523704926360/OHIO_STATE_ROLEPLAY_3.png?ex=69647604&is=69632484&hm=ab23b421a16a5a1dc28522d4df8a44dd95e6513957637f3384d5960d513260d5&")
        join_button = Button(
            label="Quick Join",
            style=discord.ButtonStyle.link,
            url="https://policeroleplay.community/join/ohioVC"
        )
        view = View(timeout=None)
        view.add_item(join_button)
        message = await full_channel.send(embeds=[image_embed, embed], view=view)
        server_full_message_id = message.id
        save_server_full_message_id(server_full_message_id)
    else:
        server_full_timestamp = None

@tasks.loop(seconds=30)
async def update_stats():
    last_updated_time = int(time.time())
    embeds, players = await get_server_info(last_updated_time, bot)

    if players is not None:
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name=f"Moderating {players} players")
        )

    if embeds:
        join_button = Button(
            label="Quick Join",
            style=discord.ButtonStyle.link,
            url="https://policeroleplay.community/join/ohioVC"
        )
        view = View(timeout=None)
        view.add_item(join_button)

        if hasattr(bot, "server_info_message") and bot.server_info_message:
            try:
                await bot.server_info_message.edit(embeds=embeds, view=view)
            except discord.HTTPException as e:
                if e.status == 429:
                    await asyncio.sleep(10)
                    try:
                        await bot.server_info_message.edit(embeds=embeds, view=view)
                    except Exception:
                        pass
        else:
            channel = bot.get_channel(1421268025323159693)
            if channel:
                try:
                    new_message = await channel.send(embeds=embeds, view=view)
                    bot.server_info_message = new_message
                    with open("server_info_message_id.txt", "w") as f:
                        f.write(str(new_message.id))
                except Exception:
                    pass

async def input_erlc_command(command: str):
    try:
        api_url = "https://api.policeroleplay.community/v1/server/command"
        payload = {"command": command}
        headers = {
            "Content-Type": "application/json",
            "server-key": "LnXkkiDJEgHynGXWwxyS-ahJHwHXrWcPpliTHUcHKPGpZPTkuIASfdTgONwGY"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return f"{wc} Command executed successfully"
                else:
                    return f"{wx} Error executing command. Status: {response.status}, Response: {await response.text()}"
    except Exception as e:
        return f"{wx} Error executing command: {str(e)}"

async def start_background_tasks():
    asyncio.create_task(check_and_notify_non_discord_players())

non_discord_players = set()

@bot.tree.command(name="players", description="Displays the current in-game players.")
@app_commands.choices(
    filter=[
        app_commands.Choice(name="In Discord", value="in_discord"),
        app_commands.Choice(name="Not In Discord", value="not_in_discord"),
        app_commands.Choice(name="Staff", value="staff")
    ]
)
async def players(interaction: discord.Interaction, filter: str = None):
    if not any(role.id == 1421277606275452970 for role in interaction.user.roles):
        await interaction.response.send_message(
            f"{wx} You do not have permission to use this command.",
            ephemeral=True
        )
        return
    await interaction.response.defer(ephemeral=True)

    try:
        players_data = await fetch_erlc_players()
    except Exception:
        await interaction.followup.send(
            f"{wx} Failed to Fetch In-Game Players.",
            ephemeral=True
        )
        return

    member_data = {
        member.nick.lower(): member 
        for member in interaction.guild.members 
        if member.nick
    }

    if not players_data:
        await interaction.followup.send(
            "<:reddot:1434346036717158400> No players currently in-game.",
            ephemeral=True
        )
        return

    owner_entry = None
    staff_in_discord_entries = []
    staff_not_in_discord_entries = []
    discord_entries = []
    non_discord_entries = []
    
    in_discord_count = 0
    in_voice_count = 0

    for player in players_data:
        if isinstance(player, dict) and "Player" in player and ':' in player["Player"]:
            full_player_name, player_id = player["Player"].split(':', 1)
            
            matching_member = next(
                (member for name, member in member_data.items() if full_player_name.lower() in name), 
                None
            )
            
            is_in_discord = matching_member is not None or full_player_name in ["JohnDoe", "JaneSmith"]
            display_name = full_player_name if len(full_player_name) <= 12 else full_player_name[:12] + "..."

            discord_emoji = "<:greendot:1434346112847974410>" if is_in_discord else "<:reddot:1434346036717158400>"
            mod_badge = " <:435:1423433098158407740>" if any(role in player.get("Permission", "") for role in ["Server Administrator", "Server Moderator", "Server Co-Owner"]) else ""
            owner_badge = " 👑" if "Server Owner" in player.get("Permission", "") else ""

            entry = f"- {discord_emoji} {display_name} (`{player_id}`){mod_badge}{owner_badge}"
            
            if is_in_discord and matching_member:
                entry += f" {matching_member.mention}"
                in_discord_count += 1
                
                if matching_member.voice and matching_member.voice.channel:
                    entry += f" 🔊 {matching_member.voice.channel.mention}"
                    in_voice_count += 1
            elif is_in_discord:
                in_discord_count += 1
            
            if "Server Owner" in player.get("Permission", ""):
                owner_entry = entry
            elif any(role in player.get("Permission", "") for role in ["Server Administrator", "Server Moderator", "Server Co-Owner"]):
                if is_in_discord:
                    staff_in_discord_entries.append((entry, player))
                else:
                    staff_not_in_discord_entries.append((entry, player))
            elif is_in_discord:
                discord_entries.append((entry, player))
            else:
                non_discord_entries.append((entry, player))

    staff_in_discord_entries.sort(key=lambda x: x[1].get("Permission", "").count("Server"), reverse=True)
    staff_not_in_discord_entries.sort(key=lambda x: x[1].get("Permission", "").count("Server"), reverse=True)
    discord_entries.sort(key=lambda x: x[1].get("Permission", "").count("Server"), reverse=True)
    non_discord_entries.sort(key=lambda x: x[1].get("Permission", "").count("Server"), reverse=True)

    if filter == "in_discord":
        entries = ([owner_entry] if owner_entry else []) + [entry[0] for entry in staff_in_discord_entries] + [entry[0] for entry in discord_entries]
    elif filter == "not_in_discord":
        entries = ([owner_entry] if owner_entry else []) + [entry[0] for entry in staff_not_in_discord_entries] + [entry[0] for entry in non_discord_entries]
    elif filter == "staff":
        entries = ([owner_entry] if owner_entry else []) + [entry[0] for entry in staff_in_discord_entries] + [entry[0] for entry in staff_not_in_discord_entries]
    else:
        entries = ([owner_entry] if owner_entry else []) + [entry[0] for entry in staff_in_discord_entries] + [entry[0] for entry in staff_not_in_discord_entries] + [entry[0] for entry in discord_entries] + [entry[0] for entry in non_discord_entries]

    players_per_page = 20
    pages = []
    
    for i in range(0, len(entries), players_per_page):
        page_entries = entries[i:i + players_per_page]
        description = "\n".join(page_entries)
        
        embed = discord.Embed(
            title="In-Game Server Players",
            description=description,
            color=0x2b2d31
        )
        embed.set_footer(text=f"{len(players_data)} Players • {in_discord_count} In Discord • {in_voice_count} In Voice")
        pages.append(embed)
    
    if len(pages) == 1:
        await interaction.followup.send(embed=pages[0], ephemeral=True)
    else:
        view = PaginatorView(pages, user_id=interaction.user.id, timeout=180)
        await interaction.followup.send(embed=pages[0], view=view, ephemeral=True)
        view.message = await interaction.original_response()

async def check_and_notify_non_discord_players():
    while True:
        try:
            players_data = await fetch_erlc_players()
            if not players_data:
                await asyncio.sleep(300)
                continue

            guild = bot.get_guild(1421266702326435912)
            if guild is None:
                await asyncio.sleep(300)
                continue

            member_mentions = {
                member.nick.lower(): member.mention
                for member in guild.members
                if member.nick
            }

            non_discord_players = []

            for player in players_data:
                if isinstance(player, dict) and "Player" in player and ':' in player["Player"]:
                    full_player_name, _ = player["Player"].split(':', 1)
                    permissions = player.get("Permission", "")

                    matching_member = next(
                        (mention for name, mention in member_mentions.items() if full_player_name.lower() in name),
                        None
                    )
                    is_in_discord = matching_member is not None or full_player_name in ["JohnDoe", "JaneSmith"]

                    if any(role in permissions for role in [
                        "Server Moderator", "Server Administrator", "Server Co-Owner", "Server Owner"
                    ]):
                        continue

                    if not is_in_discord:
                        non_discord_players.append(full_player_name)

            if non_discord_players:
                non_discord_names = ",".join(non_discord_players)
                message = "⚠️ You have been detected not in the communication server. Please join using the code: ohiostate."
                await input_erlc_command(f":pm {non_discord_names} {message}")

            await asyncio.sleep(300)

        except Exception as e:
            print(f"❌ Error in background task: {e}")

REQUIRED_ROLES = [1433587023414956052]

class Session(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="session", description="Manage server sessions.")
        self.bot = bot
        self.votes_dict = {}

    async def has_required_role(self, interaction: discord.Interaction) -> bool:
        return any(role.id in REQUIRED_ROLES for role in interaction.user.roles)

    @app_commands.command(name="vote", description="Start a session vote.")
    @app_commands.describe(votes="Maximum number of votes before voting ends.")
    async def vote(self, interaction: discord.Interaction, votes: int):
        if not await self.has_required_role(interaction):
            await interaction.response.send_message(
                f"{wx} You do not have permission to use this command.",
                ephemeral=True
            )
            return
        try:
            self.votes_dict = {}
            self.vote_count = 0
            self.max_votes = votes

            author_name = interaction.user.name
            author_avatar = interaction.user.avatar.url
            author_url = f"https://discord.com/users/{interaction.user.id}"

            channel_id = 1421268025323159693
            image_embed = discord.Embed(color=0x2b2d31)
            image_embed.set_image(url="https://cdn.discordapp.com/attachments/1414792429688852530/1441271029665366177/Copy_of_Ohioassets_3.png?ex=69646c3e&is=69631abe&hm=d241bd79f1aadf27866118f6ee10e3fd7472413421f9ebbc9e914cfb846e1bf8&")
            embed = discord.Embed(
                title="Session Vote",
                description=f"> The Directive Team has decided to host a Session Poll! If you would like a session to be hosted, click the 'Vote' button below. Remember, you are required to join after you vote or you will be punished.",
                color=0x2b2d31
            )
            embed.set_footer(
                text="All rights reserved, Ohio State Roleplay • 2025",
            )
            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1404567596698832967/1441637981231382690/ohio_new.png?ex=69232e3f&is=6921dcbf&hm=a7bdd936bd6e58212a137e557734944d94f56e0cf7588a9c9db322eb2eeb8487&')
            embed.set_author(name=author_name, url=author_url, icon_url=author_avatar)
            embed.set_image(url="https://cdn.discordapp.com/attachments/1414792429688852530/1441281523704926360/OHIO_STATE_ROLEPLAY_3.png?ex=69647604&is=69632484&hm=ab23b421a16a5a1dc28522d4df8a44dd95e6513957637f3384d5960d513260d5&")
            
            vote_button = Button(
                label=f"Vote (0/{votes})",
                style=discord.ButtonStyle.gray,
                custom_id="vote_button"
            )
            view = View(timeout=None)
            view.add_item(vote_button)

            view_votes_button = Button(
                label="View Votes",
                style=discord.ButtonStyle.gray,
                custom_id="view_votes_button"
            )
            view.add_item(view_votes_button)

            async def vote_callback(interaction: Interaction):
                user_id = interaction.user.id
                has_voted = user_id in self.votes_dict
                if self.vote_count >= self.max_votes:
                    if not has_voted:
                        await interaction.response.send_message(
                            f"{wx} Maximum votes have been reached.",
                            ephemeral=True
                        )
                        return
                    else:
                        self.votes_dict.pop(user_id)
                        self.vote_count -= 1
                        await interaction.response.send_message(
                            f"{wc} Your vote has been removed.",
                            ephemeral=True
                        )
                else:
                    if has_voted:
                        self.votes_dict.pop(user_id)
                        self.vote_count -= 1
                        await interaction.response.send_message(
                            f"{wc} Your vote has been removed.",
                            ephemeral=True
                        )
                    else:
                        self.votes_dict[user_id] = True
                        self.vote_count += 1
                        await interaction.response.send_message(
                            f"{wc} Your vote has been added.",
                            ephemeral=True
                        )
                vote_button.label = f"Vote ({self.vote_count}/{self.max_votes})"
                await interaction.message.edit(embeds=[image_embed, embed], view=view)

            async def view_votes_callback(interaction: Interaction):
                vote_list = "\n".join([f"<@{user_id}>" for user_id in self.votes_dict.keys()])
                if not vote_list:
                    vote_list = "> No one voted."
                view_embed = discord.Embed(
                    title="Session Votes",
                    description=f"These are the list of people who have voted for the session. Note that you are able to remove your vote by clicking the vote button again.\n\n{vote_list}",
                    color=0x2b2d31
                )
                await interaction.response.send_message(embed=view_embed, ephemeral=True)

            vote_button.callback = vote_callback
            view_votes_button.callback = view_votes_callback

            channel = self.bot.get_channel(channel_id)
            message = await channel.send(
                content="<@&1421277606275452970> <@&1421277505469550713>",
                embeds=[image_embed, embed],
                view=view
            )
            print(f"{author_name} has executed Session Vote.")
            await interaction.response.send_message(f"{wc} Session Vote has been executed successfully.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"{wx} An unexpected error occurred: {str(e)}", ephemeral=True)

    @app_commands.command(name="startup", description="Start the server session.")
    async def startup(self, interaction: discord.Interaction):
        if not await self.has_required_role(interaction):
            await interaction.response.send_message(
                f"{wx} You do not have permission to use this command.",
                ephemeral=True
            )
            return

        try:
            role_id = 1363720273756688465
            channel_id = 213
            role = interaction.guild.get_role(role_id)
            channel = interaction.client.get_channel(channel_id)

            if role and channel:
                await channel.set_permissions(role, send_messages=True, view_channel=True)
                messages = [message async for message in channel.history(limit=1)]
                if messages:
                    last_message = messages[0]
                    if last_message.content == "🔒":
                        await last_message.delete()
                await channel.send("🔓")

            global session_discord
            session_discord = "Online"
            author_name = interaction.user.name
            author_avatar = interaction.user.avatar.url
            author_url = f"https://discord.com/users/{interaction.user.id}"

            image_embed = discord.Embed(color=0x2b2d31)
            image_embed.set_image(url="https://cdn.discordapp.com/attachments/1414792429688852530/1441271029665366177/Copy_of_Ohioassets_3.png?ex=69646c3e&is=69631abe&hm=d241bd79f1aadf27866118f6ee10e3fd7472413421f9ebbc9e914cfb846e1bf8&")

            embed = discord.Embed(
                title="Server Startup",
                description=("> A session has been initiated, at this time we're asking those who voted during the waiting period to join. If you've voted for this session and don't join you will face moderation action."),
                color=0x2b2d31
            )
            embed.add_field(name="**Server Name**", value="`Ohio State Roleplay I VC Only`", inline=False)
            embed.add_field(name="**Join Code**", value="`ohioVC`", inline=False)
            embed.add_field(name="**Server Owner**", value="`Urnixss`", inline=False)

            embed.set_footer(
                text="All rights reserved, Ohio State Roleplay • 2025",
            )
            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1404567596698832967/1441637981231382690/ohio_new.png?ex=69232e3f&is=6921dcbf&hm=a7bdd936bd6e58212a137e557734944d94f56e0cf7588a9c9db322eb2eeb8487&')
            embed.set_author(name=author_name, url=author_url, icon_url=author_avatar)
            embed.set_image(url="https://cdn.discordapp.com/attachments/1414792429688852530/1441281523704926360/OHIO_STATE_ROLEPLAY_3.png?ex=69647604&is=69632484&hm=ab23b421a16a5a1dc28522d4df8a44dd95e6513957637f3384d5960d513260d5&")
            join_button = Button(label="Quick Join", style=discord.ButtonStyle.link, url="https://policeroleplay.community/join/ohioVC")

            view = View(timeout=None)
            view.add_item(join_button)

            session_channel = interaction.client.get_channel(1421268025323159693)
            if session_channel:
                message = await session_channel.send(
                    content="<@&1421277606275452970> <@&1421277505469550713>",
                    embeds=[image_embed, embed],
                    view=view
                )

            if self.votes_dict:
                voters = ' '.join([f'<@{user_id}>' for user_id in self.votes_dict.keys()])
                await session_channel.send(f"**<:arrow:1421979023356989582> Voters:** {voters}\n-# You are all required to join.")
            print(f"{author_name} has executed Session Startup.")
            await interaction.response.send_message(f"{wc} Session Startup has been executed successfully.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"{wx} An unexpected error occurred: {str(e)}", ephemeral=True)

    @app_commands.command(name="boost", description="Announce low player count and boost.")
    async def boost(self, interaction: discord.Interaction):
        if not await self.has_required_role(interaction):
            await interaction.response.send_message(
                f"{wx} You do not have permission to use this command.",
                ephemeral=True
            )
            return
        try:
            await interaction.response.send_message(f"{wc} Session Boost has been executed successfully.", ephemeral=True)
            embed = discord.Embed(
                title="Low Player Count",
                description="Our in-game server has dropped in players, many spots have opened up. Feel free to join!",
                color=0x2b2d31
            )
            embed.set_image(url="https://cdn.discordapp.com/attachments/1414792429688852530/1441281523704926360/OHIO_STATE_ROLEPLAY_3.png?ex=69647604&is=69632484&hm=ab23b421a16a5a1dc28522d4df8a44dd95e6513957637f3384d5960d513260d5&")
            join_button = Button(label="Quick Join", style=discord.ButtonStyle.link, url="https://policeroleplay.community/join/ohioVC")
            view = View(timeout=None)
            view.add_item(join_button)
            channel_id = 1421268025323159693
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                raise ValueError("The specified channel could not be found. Please check the channel ID.")
            print(f"{interaction.user.name} has executed Session Boost.")
            await channel.send(content="<@&1421277606275452970> <@&1421277505469550713>", embed=embed, view=view)
        except Exception as e:
            await interaction.response.send_message(f"{wx} An unexpected error occurred: {str(e)}", ephemeral=True)

    @app_commands.command(name="shutdown", description="Shut down the server session.")
    async def shutdown(self, interaction: discord.Interaction):
        if not await self.has_required_role(interaction):
            await interaction.response.send_message(
                f"{wx} You do not have permission to use this command.",
                ephemeral=True
            )
            return
        try:
            print(f"{interaction.user.name} has executed Session Shutdown.")
            await interaction.response.send_message(f"{wc} Session Shutdown has been executed successfully.", ephemeral=True)

            role_id = 1267946676325191711
            channel_id = 1324531610548305981
            session_channel_id = 1421268025323159693
            shutdown_log_channel_id = 1383975604256379102
            role = interaction.guild.get_role(role_id)
            channel = self.bot.get_channel(channel_id)
            session_channel = self.bot.get_channel(session_channel_id)
            shutdown_log_channel = self.bot.get_channel(shutdown_log_channel_id)
            current_players = await fetch_erlc_data()
            global session_discord
            session_discord = "Offline"
            author_name = interaction.user.name
            author_avatar = interaction.user.avatar.url
            author_url = f"https://discord.com/users/{interaction.user.id}"

            image_embed = discord.Embed(color=0x2b2d31)
            image_embed.set_image(url="https://cdn.discordapp.com/attachments/1414792429688852530/1441271029665366177/Copy_of_Ohioassets_3.png?ex=69646c3e&is=69631abe&hm=d241bd79f1aadf27866118f6ee10e3fd7472413421f9ebbc9e914cfb846e1bf8&")

            ssd_embed = discord.Embed(
                title="Server Shutdown",
                description="",
                color=0x2b2d31
            )
            ssd_embed.add_field(
                name="",
                value="The in-game server has now shut down! During this period, do not join the in-game server, or moderation actions may be taken against you!",
                inline=False
            )
            ssd_embed.add_field(
                name="",
                value="Another session will commence shortly, keep an eye on this channel for the next session. Thank you!",
                inline=False
            )
            ssd_embed.set_footer(
                text="All rights reserved, Ohio State Roleplay • 2025",
            )
            ssd_embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1404567596698832967/1441637981231382690/ohio_new.png?ex=69232e3f&is=6921dcbf&hm=a7bdd936bd6e58212a137e557734944d94f56e0cf7588a9c9db322eb2eeb8487&')
            ssd_embed.set_image(url="https://cdn.discordapp.com/attachments/1414792429688852530/1441281523704926360/OHIO_STATE_ROLEPLAY_3.png?ex=69647604&is=69632484&hm=ab23b421a16a5a1dc28522d4df8a44dd95e6513957637f3384d5960d513260d5&")
            ssd_embed.set_author(name=author_name, url=author_url, icon_url=author_avatar)
            session_channel_id = 1421268025323159693
            session_channel = self.bot.get_channel(session_channel_id)
            if session_channel is None:
                raise ValueError("The specified channel could not be found. Please check the channel ID.")
            await session_channel.send(content="", embeds=[image_embed, ssd_embed])
            shutdown_embed = discord.Embed(
                title="Server Shutdown",
                color=0xff0000
            )
            shutdown_embed.add_field(name="Manager", value=interaction.user.mention, inline=True)
            shutdown_embed.add_field(name="Players", value=str(current_players), inline=True)
            shutdown_embed.set_image(url="https://cdn.discordapp.com/attachments/1414792429688852530/1441281523704926360/OHIO_STATE_ROLEPLAY_3.png?ex=69647604&is=69632484&hm=ab23b421a16a5a1dc28522d4df8a44dd95e6513957637f3384d5960d513260d5&")
            if shutdown_log_channel:
                await shutdown_log_channel.send(embed=shutdown_embed)

            notification_response = await input_erlc_command(
                ":m 👋 Thank you for attending today's session! A server shutdown has commenced, meaning all players are required to leave. You will automatically be kicked in 1 minute."
            )
            if shutdown_log_channel:
                await shutdown_log_channel.send(notification_response)
            await asyncio.sleep(60)
            kick_response = await input_erlc_command(":kick all")
            if shutdown_log_channel:
                await shutdown_log_channel.send(kick_response)

        except Exception as e:
            await interaction.response.send_message(f"{wx} An unexpected error occurred: {str(e)}", ephemeral=True)

    @app_commands.command(name="full", description="Send the server full announcement.")
    async def full(self, interaction: discord.Interaction):
        if not await self.has_required_role(interaction):
            await interaction.response.send_message(
                f"{wx} You do not have permission to use this command.",
                ephemeral=True
            )
            return

        try:
            global server_full_message_id, server_full_timestamp
            channel_id = 1421268025323159693
            full_channel = self.bot.get_channel(channel_id)
            if not full_channel:
                return await interaction.response.send_message(f"{wx} Channel not found.", ephemeral=True)

            server_full_message_id = load_server_full_message_id()
            server_full_timestamp = int(time.time())

            image_embed = discord.Embed(color=0x2b2d31)
            image_embed.set_image(url="https://cdn.discordapp.com/attachments/1414792429688852530/1441271029665366177/Copy_of_Ohioassets_3.png?ex=69646c3e&is=69631abe&hm=d241bd79f1aadf27866118f6ee10e3fd7472413421f9ebbc9e914cfb846e1bf8&")

            embed = discord.Embed(
                title="Server Full",
                description=f"Ohio State Roleplay has been full since <t:{server_full_timestamp}:R>. Keep joining as spots will open shortly.",
                color=0x2b2d31
            )
            embed.set_image(url="https://cdn.discordapp.com/attachments/1414792429688852530/1441281523704926360/OHIO_STATE_ROLEPLAY_3.png?ex=69647604&is=69632484&hm=ab23b421a16a5a1dc28522d4df8a44dd95e6513957637f3384d5960d513260d5&")

            join_button = Button(
                label="Quick Join",
                style=discord.ButtonStyle.link,
                url="https://policeroleplay.community/join/ohioVC"
            )
            view = View(timeout=None)
            view.add_item(join_button)

            message = await full_channel.send(embeds=[image_embed, embed], view=view)
            server_full_message_id = message.id
            save_server_full_message_id(server_full_message_id)

            await interaction.response.send_message(f"{wc} Session full has been executed successfully.", ephemeral=True)
            print(f"{interaction.user.name} has executed Session Full.")
        except Exception as e:
            await interaction.response.send_message(f"{wx} An unexpected error occurred: {str(e)}", ephemeral=True)

bot.tree.add_command(Session(bot))

SUGGEST_CHANNEL_ID = 1421332916407111801
SUGGESTIONS_FILE = "suggestions.json"

if not os.path.exists(SUGGESTIONS_FILE):
    with open(SUGGESTIONS_FILE, "w") as f:
        json.dump({}, f)

def load_suggestions():
    with open(SUGGESTIONS_FILE, "r") as f:
        return json.load(f)

def save_suggestions(data):
    with open(SUGGESTIONS_FILE, "w") as f:
        json.dump(data, f, indent=4)

class VoteView(discord.ui.View):
    def __init__(self, message_id: int = 0):
        super().__init__(timeout=None)
        self.message_id = str(message_id) if message_id else None

    @discord.ui.button(emoji='<:like:1434347280244281404>', style=discord.ButtonStyle.green, custom_id="vote_up")
    async def upvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, vote_type="upvote")

    @discord.ui.button(emoji='<:dislike:1434347313056317562>', style=discord.ButtonStyle.red, custom_id="vote_down")
    async def downvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, vote_type="downvote")

    async def handle_vote(self, interaction, vote_type):
        try:
            if not self.message_id:
                self.message_id = str(interaction.message.id)

            user_id = str(interaction.user.id)
            suggestions = load_suggestions()
            entry = suggestions.get(self.message_id, {"upvote": [], "downvote": []})

            current, opposite = ("upvote", "downvote") if vote_type == "upvote" else ("downvote", "upvote")

            if user_id in entry[current]:
                entry[current].remove(user_id)
                action = f"{wc} You have removed your {vote_type}!"
            else:
                entry[current].append(user_id)
                if user_id in entry[opposite]:
                    entry[opposite].remove(user_id)
                action = f"{wc} You have {vote_type}d the suggestion!"

            suggestions[self.message_id] = entry
            save_suggestions(suggestions)

            channel = interaction.guild.get_channel(SUGGEST_CHANNEL_ID)
            message = await channel.fetch_message(int(self.message_id))
            embed = message.embeds[0]
            embed.set_field_at(0, name="Upvotes", value=str(len(entry["upvote"])), inline=True)
            embed.set_field_at(1, name="Downvotes", value=str(len(entry["downvote"])), inline=True)
            await message.edit(embed=embed, view=self)

            await interaction.response.send_message(action, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"{wx} An error occurred: {str(e)}", ephemeral=True)

STAFF = {
    1421270212229206117,
    1434353486778339348,
    1421270212367487139,
    1423448883182174259
}

@bot.tree.context_menu(name="Accept Suggestion")
async def accept_suggestion(interaction: discord.Interaction, message: discord.Message):
    if not any(role.id in STAFF for role in interaction.user.roles):
        await interaction.response.send_message(f"{wx} You do not have permission to use this.", ephemeral=True)
        return

    suggestions = load_suggestions()
    message_id = str(message.id)

    if message_id not in suggestions:
        await interaction.response.send_message(f"{wx} This is not a suggestion.", ephemeral=True)
        return

    entry = suggestions[message_id]
    if entry.get("status") in ("accepted", "denied"):
        await interaction.response.send_message(f"{wx} This suggestion has already been {entry['status']}.", ephemeral=True)
        return

    if not message.embeds:
        await interaction.response.send_message(f"{wx} No embed found.", ephemeral=True)
        return

    embed = message.embeds[0]
    embed.title = f"{wc} Suggestion Accepted"
    embed.color = discord.Color.green()

    entry["status"] = "accepted"
    entry["handled_by"] = str(interaction.user.id)
    suggestions[message_id] = entry
    save_suggestions(suggestions)

    await message.edit(embed=embed)
    await interaction.response.send_message(f"{wc} Suggestion accepted.", ephemeral=True)


@bot.tree.context_menu(name="Deny Suggestion")
async def deny_suggestion(interaction: discord.Interaction, message: discord.Message):
    if not any(role.id in STAFF for role in interaction.user.roles):
        await interaction.response.send_message(f"{wx} You do not have permission to use this.", ephemeral=True)
        return

    suggestions = load_suggestions()
    message_id = str(message.id)

    if message_id not in suggestions:
        await interaction.response.send_message(f"{wx} This is not a suggestion.", ephemeral=True)
        return

    entry = suggestions[message_id]
    if entry.get("status") in ("accepted", "denied"):
        await interaction.response.send_message(f"{wx} This suggestion has already been {entry['status']}.", ephemeral=True)
        return

    if not message.embeds:
        await interaction.response.send_message(f"{wx} No embed found.", ephemeral=True)
        return

    embed = message.embeds[0]
    embed.title = f"{wx} Suggestion Denied"
    embed.color = discord.Color.red()

    entry["status"] = "denied"
    entry["handled_by"] = str(interaction.user.id)
    suggestions[message_id] = entry
    save_suggestions(suggestions)

    await message.edit(embed=embed)
    await interaction.response.send_message(f"{wc} Suggestion denied.", ephemeral=True)

@bot.tree.command(name="suggest", description="Submit a suggestion.")
@app_commands.describe(suggestion="What is your suggestion?")
async def suggest(interaction: discord.Interaction, suggestion: str):
    embed = discord.Embed(
        title="New Suggestion",
        description=suggestion,
        color=0x2b2d31
    )
    embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url
    )
    embed.add_field(name="Upvotes", value="0", inline=True)
    embed.add_field(name="Downvotes", value="0", inline=True)

    channel = interaction.guild.get_channel(SUGGEST_CHANNEL_ID)
    msg = await channel.send(embed=embed, view=VoteView(0))

    view = VoteView(msg.id)
    await msg.edit(view=view)

    suggestions = load_suggestions()
    suggestions[str(msg.id)] = {"upvote": [], "downvote": []}
    save_suggestions(suggestions)

    await interaction.response.send_message(
        f"{wc} Your suggestion has been sent.",
        ephemeral=True
    )

LOA_FILE = "loa.json"
STAFF_ROLES = [1421277606275452970]
MANAGER_ROLES = [1421270212229206117, 1421270212367487139]
LOA_REMOVED_ROLES = [1465621302114123950, 1465621302114123950, 1465621302114123950, 1465621302114123950]
CHANNEL_ID = 1435316175847559349
GUILD_NAME = "Ohio State Roleplay"

time_multipliers = {
    "s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1,
    "d": 86400, "ds": 86400, "day": 86400, "days": 86400,
    "w": 604800, "wk": 604800, "week": 604800, "weeks": 604800,
    "y": 31536000, "yr": 31536000, "year": 31536000, "years": 31536000
}

def parse_time(time_input: str):
    time_regex = re.findall(r"(\d+)\s*(s|sec|secs|second|seconds|d|ds|day|days|w|wk|week|weeks|y|yr|year|years)", time_input, re.IGNORECASE)
    total_seconds = 0
    time_components = {"seconds": 0, "days": 0, "weeks": 0, "years": 0}
    for value, unit in time_regex:
        value = int(value)
        unit = unit.lower()
        total_seconds += value * time_multipliers[unit]
        if unit in ["s", "sec", "secs", "second", "seconds"]:
            time_components["seconds"] += value
        elif unit in ["d", "ds", "day", "days"]:
            time_components["days"] += value
        elif unit in ["w", "wk", "week", "weeks"]:
            time_components["weeks"] += value
        elif unit in ["y", "yr", "year", "years"]:
            time_components["years"] += value
    return (total_seconds, time_components) if total_seconds else (None, None)

def load_loa_data():
    if not os.path.exists(LOA_FILE):
        with open(LOA_FILE, "w") as f:
            json.dump([], f)
    with open(LOA_FILE, "r") as f:
        return json.load(f)

def save_loa_data(data):
    with open(LOA_FILE, "w") as f:
        json.dump(data, f, indent=4)

class LOAButtons(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="loa_accept_button")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id in MANAGER_ROLES for role in interaction.user.roles):
            return await interaction.response.send_message(f"{wx} You don't have permission to accept this request.", ephemeral=True)

        loa_data = load_loa_data()
        request = next((r for r in loa_data if r["message_id"] == interaction.message.id), None)
        if not request:
            return await interaction.response.send_message(f"{wx} LOA request not found.", ephemeral=True)

        request["status"] = "accepted"
        save_loa_data(loa_data)

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.set_footer(
            text=f"Status: Accepted - {interaction.user.display_name}",
            icon_url="https://cdn.discordapp.com/emojis/1365538102323449937.webp?size=96"
        )
        await interaction.response.edit_message(embed=embed, view=None)

        guild = interaction.guild
        member = guild.get_member(request["user_id"])
        if member:
            loa_role = guild.get_role(1421277503850545224)
            staff_role = guild.get_role(1421277606275452970)

            removed_roles = []

            for role_id in LOA_REMOVED_ROLES:
                role = guild.get_role(role_id)
                if role and role in member.roles:
                    await member.remove_roles(role, reason="LOA accepted")
                    removed_roles.append(role_id)

            request["removed_roles"] = removed_roles
            save_loa_data(loa_data)

            if loa_role:
                await member.add_roles(loa_role, reason="LOA accepted")
            if staff_role:
                await member.remove_roles(staff_role, reason="LOA accepted")
        
        print(f"{interaction.user.name} accepted {member}'s LOA.")
        user = interaction.client.get_user(request["user_id"])
        if user:
            try:
                await user.send(embed=discord.Embed(
                    title=f"{wc} Leave of Absence Accepted",
                    description=f"Your LOA request in **{GUILD_NAME}** was accepted!",
                    color=discord.Color.green()
                ))
            except discord.Forbidden:
                print(f"Could not DM {user.name} about accepted LOA.")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, custom_id="loa_deny_button")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id in MANAGER_ROLES for role in interaction.user.roles):
            return await interaction.response.send_message(f"{wx} You don't have permission to deny this request.", ephemeral=True)

        loa_data = load_loa_data()
        request = next((r for r in loa_data if r["message_id"] == interaction.message.id), None)
        if not request:
            return await interaction.response.send_message(f"{wx} LOA request not found.", ephemeral=True)

        request["status"] = "denied"
        save_loa_data(loa_data)

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.set_footer(
            text=f"Status: Denied - {interaction.user.display_name}",
            icon_url="https://cdn.discordapp.com/emojis/1365538455576121456.webp?size=96"
        )
        await interaction.response.edit_message(embed=embed, view=None)

        guild = interaction.guild
        member = guild.get_member(request["user_id"])

        print(f"{interaction.user.name} denied {member}'s LOA.")
        await interaction.user.send(embed=discord.Embed(
            title="<:Denied:1365538455576121456> Leave of Absence Denied",
            description=f"Your LOA request in **{GUILD_NAME}** was denied!",
            color=discord.Color.red()
        ))

class LOAActiveView(View):
    def __init__(self, loas, page=1):
        super().__init__(timeout=None)
        self.loas = loas
        self.page = page
        self.max_pages = (len(loas) - 1) // 5 + 1

        self.left_button = discord.ui.Button(
            label="⬅️", style=discord.ButtonStyle.secondary, custom_id=f"loa_active_left_{self.page}",
            disabled=self.page == 1
        )
        self.right_button = discord.ui.Button(
            label="➡️", style=discord.ButtonStyle.secondary, custom_id=f"loa_active_right_{self.page}"
        )

        if self.max_pages > 1:
            self.add_item(self.left_button)
            self.add_item(self.right_button)

        self.left_button.callback = self.left_button_callback
        self.right_button.callback = self.right_button_callback

    async def left_button_callback(self, interaction: discord.Interaction):
        if self.page > 1:
            self.page -= 1
            await self.update_embed(interaction)

    async def right_button_callback(self, interaction: discord.Interaction):
        if self.page < self.max_pages:
            self.page += 1
            await self.update_embed(interaction)

    async def update_embed(self, interaction: discord.Interaction):
        start_index = (self.page - 1) * 5
        end_index = start_index + 5
        page_loas = self.loas[start_index:end_index]

        embed = discord.Embed(
            title=f"Leave of Absences [{len(self.loas)}]",
            color=0x2b2d31
        )
        embed.set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else discord.Embed.Empty
        )

        for loa in page_loas:
            user = interaction.client.get_user(loa["user_id"])
            if user is None:
                try:
                    user = await interaction.client.fetch_user(loa["user_id"])
                except discord.NotFound:
                    user = None
                except discord.HTTPException:
                    user = None

            start_ts = loa["submitted_at"]
            end_ts = loa["ends_at"]

            if user is not None:
                staff_display = user.mention
            else:
                staff_display = f"`Unknown User ({loa['user_id']})`"

            embed.add_field(
                name="Leave of Absence",
                value=(
                    f"> **Staff Member:** {staff_display}\n"
                    f"> **Reason:** {loa['reason']}\n"
                    f"> **Started At:** <t:{start_ts}>\n"
                    f"> **Ends At:** <t:{end_ts}>"
                ),
                inline=False
            )

        self.left_button.disabled = self.page == 1
        self.right_button.disabled = self.page == self.max_pages

        self.left_button.custom_id = f"loa_active_left_{self.page}"
        self.right_button.custom_id = f"loa_active_right_{self.page}"

        embed.set_footer(text=f"Page {self.page} of {self.max_pages}")

        await interaction.response.edit_message(embed=embed, view=self)

class ExtendLOAModal(discord.ui.Modal, title="Extend Leave of Absence"):
    duration = discord.ui.TextInput(
        label="Duration",
        placeholder="1d (1 day), 2h (2 hours), etc.",
        required=True,
        max_length=10
    )

    def __init__(self, loa_entry, target_user, message):
        super().__init__()
        self.loa_entry = loa_entry
        self.target_user = target_user
        self.message = message

    async def on_submit(self, interaction: discord.Interaction):
        total_seconds, _ = parse_time(self.duration.value)
        if not total_seconds:
            return await interaction.response.send_message(f"{wx} Invalid duration format.", ephemeral=True)

        loa_data = load_loa_data()
        loa = next((l for l in loa_data if l["user_id"] == self.loa_entry["user_id"] and l["status"] == "accepted" and not l.get("ended")), None)

        if not loa:
            return await interaction.response.send_message(f"{wx} This LOA is no longer active.", ephemeral=True)

        loa["ends_at"] += int(total_seconds)
        save_loa_data(loa_data)

        print(f"{interaction.user.name} extended {self.target_user}'s LOA.")
        await self.message.edit(content=f"{wc} Successfully extended **@{self.target_user.name}'s** Leave of Absence.", embed=None, view=None)
        await interaction.response.defer()

class LOAManageView(View):
    def __init__(self, loa_entry=None, target_user=None):
        super().__init__(timeout=None)
        self.loa_entry = loa_entry
        self.target_user = target_user

    @discord.ui.button(label="Void LOA", emoji="<:ShiftEnded:1389039618837708891>", style=discord.ButtonStyle.secondary, custom_id="void_loa_button")
    async def void_loa(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id in MANAGER_ROLES for role in interaction.user.roles):
            return await interaction.response.send_message(f"{wx} You don't have permission to void LOAs.", ephemeral=True)

        if self.loa_entry is None or self.target_user is None:
            return await interaction.response.send_message(f"{wx} This button is no longer active.", ephemeral=True)

        loa_data = load_loa_data()
        loa = next((l for l in loa_data if l["user_id"] == self.loa_entry["user_id"] and l["status"] == "accepted" and not l.get("ended")), None)

        if not loa:
            return await interaction.response.send_message(f"{wx} This LOA is no longer active.", ephemeral=True)

        loa["ended"] = True
        save_loa_data(loa_data)

        removed_roles = loa.get("removed_roles", [])
        for role_id in removed_roles:
            role = interaction.guild.get_role(role_id)
            if role and role not in self.target_user.roles:
                await self.target_user.add_roles(role, reason="LOA forcefully voided")

        try:
            loa_role = interaction.guild.get_role(1421277503850545224)
            staff_role = interaction.guild.get_role(1421277606275452970)
            if loa_role and loa_role in self.target_user.roles:
                await self.target_user.remove_roles(loa_role, reason="LOA forcefully voided")
            if staff_role and staff_role not in self.target_user.roles:
                await self.target_user.add_roles(staff_role, reason="LOA forcefully voided")

            embed = discord.Embed(
                title="<:ShiftEnded:1389039618837708891> Leave of Absence Ended",
                description=f"Your Leave of Absence in **Ohio State Roleplay** was forcefully ended!",
                color=0xFF0000
            )
            await self.target_user.send(embed=embed)
        except discord.Forbidden:
            pass

        print(f"{interaction.user.name} has voided {self.target_user}'s LOA.")
        await interaction.message.edit(
            content=f"{wc} Successfully ended **@{self.target_user.name}'s** Leave of Absence.",
            embed=None,
            view=None
        )
        await interaction.response.defer()

    @discord.ui.button(label="Extend LOA", style=discord.ButtonStyle.primary, custom_id="extend_loa_button")
    async def extend_loa(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id in MANAGER_ROLES for role in interaction.user.roles):
            return await interaction.response.send_message(f"{wx} You don't have permission to extend LOAs.", ephemeral=True)

        if self.loa_entry is None or self.target_user is None:
            return await interaction.response.send_message(f"{wx} This button is no longer active.", ephemeral=True)

        await interaction.response.send_modal(ExtendLOAModal(self.loa_entry, self.target_user, interaction.message))

class LOAGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="loa", description="Manage Leave of Absence")

    @app_commands.command(name="request", description="Request a Leave of Absence")
    @app_commands.describe(
        duration="How long you want the LOA to last (e.g., 1d, 2h, 30m)",
        reason="The reason you are requesting a LOA"
    )
    async def request(self, interaction: discord.Interaction, duration: str, reason: str):
        if not any(role.id in STAFF_ROLES for role in interaction.user.roles):
            return await interaction.response.send_message(f"{wx} You don't have permission to use this command.", ephemeral=True)

        loa_data = load_loa_data()
        user_loas = [loa for loa in loa_data if loa["user_id"] == interaction.user.id]

        for loa in user_loas:
            if loa["status"] == "pending":
                return await interaction.response.send_message(f"{wx} You already have a pending Leave of Absence request.", ephemeral=True)
            if loa["status"] == "accepted" and not loa["ended"]:
                return await interaction.response.send_message(f"{wx} You already have an active Leave of Absence.", ephemeral=True)

        now = datetime.now(timezone.utc)
        start_ts = int(now.timestamp())
        total_seconds, _ = parse_time(duration)
        if not total_seconds:
            return await interaction.response.send_message(f"{wx} Invalid duration format.", ephemeral=True)

        end = now + timedelta(seconds=total_seconds)
        end_ts = int(end.timestamp())
        embed = discord.Embed(title="Leave Request", color=0x2b2d31)
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url if interaction.guild.icon else discord.Embed.Empty)
        embed.add_field(name="**LOA Information**", value=f"> **Staff Member:** {interaction.user.mention}\n> **Reason:** {reason}", inline=False)
        embed.add_field(name="Starts At:", value=f"<t:{start_ts}>", inline=True)
        embed.add_field(name="Ends At:", value=f"<t:{end_ts}>", inline=True)
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else discord.Embed.Empty)
        embed.set_footer(text="Status: Pending", icon_url="https://cdn.discordapp.com/emojis/1365530018700197969.webp?size=96")

        view = LOAButtons()
        channel = interaction.client.get_channel(CHANNEL_ID)
        message = await channel.send(content="<@&1421270212229206117>", embed=embed, view=view)

        loa_entry = {
            "user_id": interaction.user.id,
            "submitted_at": start_ts,
            "ends_at": end_ts,
            "reason": reason,
            "status": "pending",
            "message_id": message.id,
            "ended": False
        }

        loa_data.append(loa_entry)
        save_loa_data(loa_data)
        print(f"{interaction.user.name} has requested an LOA.")
        await interaction.response.send_message(f"{wc} Your LOA request has been submitted.", ephemeral=True)

    @app_commands.command(name="active", description="View active LOAs")
    async def active(self, interaction: discord.Interaction):
        if not any(role.id in STAFF_ROLES for role in interaction.user.roles):
            return await interaction.response.send_message(f"{wx} You don't have permission to use this command.", ephemeral=True)
        
        loa_data = load_loa_data()
        active_loas = [loa for loa in loa_data if loa["status"] == "accepted" and not loa.get("ended")]

        if not active_loas:
            return await interaction.response.send_message(f"{wx} No active LOAs found.", ephemeral=True)

        if len(active_loas) > 5:
            view = LOAActiveView(active_loas)
        else:
            view = discord.ui.View()

        embed = discord.Embed(
            title=f"Leave of Absences [{len(active_loas)}]",
            color=0x2b2d31
        )
        embed.set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else discord.Embed.Empty
        )

        for loa in active_loas[:5]:
            user = interaction.client.get_user(loa["user_id"])
            if user is None:
                try:
                    user = await interaction.client.fetch_user(loa["user_id"])
                except (discord.NotFound, discord.HTTPException):
                    user = None

            if user is not None:
                staff_display = user.mention
            else:
                staff_display = f"`Unknown User ({loa['user_id']})`"

            start_ts = loa["submitted_at"]
            end_ts = loa["ends_at"]

            embed.add_field(
                name="Leave of Absence",
                value=(
                    f"> **Staff Member:** {staff_display}\n"
                    f"> **Reason:** {loa['reason']}\n"
                    f"> **Started At:** <t:{start_ts}>\n"
                    f"> **Ends At:** <t:{end_ts}>"
                ),
                inline=False
            )
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="manage", description="Manage a user's Leave of Absence")
    @app_commands.describe(user="The user to manage")
    async def manage(self, interaction: discord.Interaction, user: discord.User):
        if not any(role.id in MANAGER_ROLES for role in interaction.user.roles):
            return await interaction.response.send_message(f"{wx} You don't have permission to use this command.", ephemeral=True)

        loa_data = load_loa_data()
        user_loa = next((loa for loa in loa_data if loa["user_id"] == user.id and loa["status"] == "accepted" and not loa.get("ended")), None)

        if not user_loa:
            return await interaction.response.send_message(f"{wx} **@{user.name}** is not currently on leave.", ephemeral=True)

        embed = discord.Embed(
            title="Leave of Absence",
            description=f"**Current LOA**\n"
                        f"> **Start Date:** <t:{user_loa['submitted_at']}>\n"
                        f"> **End Date:** <t:{user_loa['ends_at']}>\n"
                        f"> **Reason:** {user_loa['reason']}",
            color=0x2b2d31
        )
        embed.set_author(name=f"@{user.name}", icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)

        view = LOAManageView(user_loa, user)
        await interaction.response.send_message(embed=embed, view=view)

bot.tree.add_command(LOAGroup())

@tasks.loop(seconds=20)
async def check_loa_expiry():
    now_ts = int(datetime.now(timezone.utc).timestamp())
    loa_data = load_loa_data()
    updated = False

    for request in loa_data:
        if (
            not request.get("ended") and 
            request.get("status") == "accepted" and 
            now_ts >= request["ends_at"]
        ):
            request["ended"] = True
            updated = True

        removed_roles = request.get("removed_roles", [])
        for role_id in removed_roles:
            role = guild.get_role(role_id)
            if role and role not in user.roles:
                await user.add_roles(role, reason="LOA expired")

            guild = bot.get_guild(1421270212229206117)
            user = guild.get_member(request["user_id"]) if guild else None

            if user:
                loa_role = guild.get_role(1421277503850545224)
                staff_role = guild.get_role(1421277606275452970)
                if loa_role and loa_role in user.roles:
                    await user.remove_roles(loa_role, reason="LOA expired")
                if staff_role and staff_role not in user.roles:
                    await user.add_roles(staff_role, reason="LOA expired")

                try:
                    embed = discord.Embed(
                        title="<:idle:1434348036536008784> Leave of Absence Expired",
                        description="Your Leave of Absence in **Ohio State Roleplay** has expired.",
                        color=0x2b2d31
                    )
                    print(f"{user.name}'s LOA has expired.")
                    await user.send(embed=embed)
                except discord.Forbidden:
                    pass

    if updated:
        save_loa_data(loa_data)

INFRACTIONS_CHANNEL_ID = 1421280446079041687
REQUIRED_ROLE_IDS = [1421270212229206117, 1421270212367487139, 1421269172951711795, 1468728941706481859]
STRIKE_1_ROLE_ID = 1433650987209588838
STRIKE_2_ROLE_ID = 1433650986878107809
STRIKE_3_ROLE_ID = 1433650986001498112

STAFF_ROLE_IDS = [
    1421269162805825577, 1421269163334438942, 1421269163661332653, 1421270212367487139,
    1421269164160454788, 1421269164328226837, 1421269164680679465, 1421270212229206117,
    1421269166022852609, 1421269166467584090, 1421269166769438752, 1421269172951711795,
    1421269166903656488, 1421269167386005625, 1421269167394259017, 1421269168115810334,
    1421269169281830992, 1421269169391009894, 1421269170036670617, 1421269170506567850,
    1421269172502925362, 1468728941706481859

]

def generate_case_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def load_infractions():
    if not os.path.exists("infractions.json"):
        return []
    with open("infractions.json", "r") as f:
        return json.load(f)

def save_infractions(data):
    with open("infractions.json", "w") as f:
        json.dump(data, f, indent=4)

class InfractionCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="infraction", description="Infraction management commands.")
    
    @app_commands.command(name="issue", description="Issue an infraction to a staff member.")
    @app_commands.describe(
        user="The user receiving the infraction.",
        reason="The reason for the infraction.",
        type="The type of infraction.",
        notes="Additional notes (optional)."
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="Warning", value="Warning"),
        app_commands.Choice(name="Strike", value="Strike"),
        app_commands.Choice(name="Under Investigatiion", value="Under Investigation"),
        app_commands.Choice(name="Demotion", value="Demotion"),
        app_commands.Choice(name="Termination", value="Termination"),
    ])
    async def issue(self, interaction: discord.Interaction, user: discord.Member, reason: str, type: app_commands.Choice[str], notes: str = None):
        await interaction.response.defer(ephemeral=True)
        
        if not any(role.id in REQUIRED_ROLE_IDS for role in interaction.user.roles):
            return await interaction.followup.send(f"{wx} You do not have permission to use this command.", ephemeral=True)
        
        IGNORED_ROLE_ID = 1363615015101399211
        HIERARCHY_IGNORED_ROLE_ID = 1434345009569595472
        
        def get_highest_role(roles):
            filtered = [role for role in roles if role.id != IGNORED_ROLE_ID]
            return max(filtered, key=lambda r: r.position) if filtered else None
        
        if interaction.user.id != 973619439822049330:
            issuer_top = get_highest_role(interaction.user.roles)
            target_top = get_highest_role(user.roles)
            
            if issuer_top and target_top and issuer_top.id == HIERARCHY_IGNORED_ROLE_ID and target_top.id == HIERARCHY_IGNORED_ROLE_ID:
                issuer_roles_filtered = [role for role in interaction.user.roles if role.id not in [IGNORED_ROLE_ID, HIERARCHY_IGNORED_ROLE_ID]]
                target_roles_filtered = [role for role in user.roles if role.id not in [IGNORED_ROLE_ID, HIERARCHY_IGNORED_ROLE_ID]]
                
                issuer_top = max(issuer_roles_filtered, key=lambda r: r.position) if issuer_roles_filtered else None
                target_top = max(target_roles_filtered, key=lambda r: r.position) if target_roles_filtered else None
            
            if issuer_top and target_top and issuer_top.position <= target_top.position:
                return await interaction.followup.send(
                    f"{wx} You cannot infract someone whose highest role is the same or higher than yours.", ephemeral=True)
        
        channel = interaction.client.get_channel(INFRACTIONS_CHANNEL_ID)
        if channel is None:
            return await interaction.followup.send("Couldn't find the infractions channel.", ephemeral=True)
        
        case_id = generate_case_id()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        action_text = type.value
        
        if type.value == "Strike":
            user_roles = [role.id for role in user.roles]
            if STRIKE_1_ROLE_ID not in user_roles and STRIKE_2_ROLE_ID not in user_roles and STRIKE_3_ROLE_ID not in user_roles:
                await user.add_roles(discord.Object(id=STRIKE_1_ROLE_ID), reason="Strike 1 issued via infraction system.")
                action_text = "Strike 1"
            elif STRIKE_1_ROLE_ID in user_roles and STRIKE_2_ROLE_ID not in user_roles and STRIKE_3_ROLE_ID not in user_roles:
                await user.add_roles(discord.Object(id=STRIKE_2_ROLE_ID), reason="Strike 2 issued via infraction system.")
                action_text = "Strike 2"
            elif STRIKE_2_ROLE_ID in user_roles and STRIKE_3_ROLE_ID not in user_roles:
                await user.add_roles(discord.Object(id=STRIKE_3_ROLE_ID), reason="Strike 3 issued via infraction system.")
                action_text = "Strike 3"
            else:
                action_text = "Strike"
        
        if type.value == "Termination":
            roles_to_remove = [discord.Object(id=role_id) for role_id in STAFF_ROLE_IDS if role_id in [r.id for r in user.roles]]
            if roles_to_remove:
                await user.remove_roles(*roles_to_remove, reason="Termination - Staff roles removed.")
        
        embed = discord.Embed(
            title="⚠️ New Infraction Issued!",
            description=(
                f"- **⚠️ Staff Member:** {user.mention}\n"
                f"- **🔨 Action:** {action_text}\n"
                f"- **📋 Reason:** {reason}\n\n"
                "-# If you believe this infraction was unjustified, please contact a Management Team member."
            ),
            color=0x2b2d31,
            timestamp=interaction.created_at
        )
        embed.set_author(name=f"Issued By, {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1404567596698832967/1441637981231382690/ohio_new.png?ex=69232e3f&is=6921dcbf&hm=a7bdd936bd6e58212a137e557734944d94f56e0cf7588a9c9db322eb2eeb8487&")
        embed.set_footer(text=f"Case ID: {case_id}", icon_url=user.display_avatar.url)
        
        sent_message = await channel.send(
            content=f"{user.mention}",
            embed=embed
        )
        
        thread = await sent_message.create_thread(
            name="Infraction Discussion",
            auto_archive_duration=10080,
            reason="Infraction issued."
        )
        await thread.send("This thread is for discussing the infraction and sharing relevant information.")
        
        if notes:
            await thread.send(f"<:arrow:1421979023356989582> **Notes:** {notes}")
        
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            pass
        
        message_link = sent_message.jump_url
        infraction_entry = {
            "case_id": case_id,
            "issuer_id": interaction.user.id,
            "staff_id": user.id,
            "infraction_type": type.value,
            "reason": reason,
            "notes": notes or "",
            "timestamp": int(interaction.created_at.timestamp()),
            "message_link": message_link,
            "is_voided": False
        }
        
        infractions = load_infractions()
        infractions.append(infraction_entry)
        save_infractions(infractions)
        
        notify_channel = interaction.client.get_channel(1434349075330764910)
        if notify_channel:
            summary_embed = discord.Embed(
                title="Infraction Created",
                description=(
                    f"> **Case ID:** `{case_id}`\n"
                    f"> **Action:** {action_text}\n"
                    f"> **Reason:** {reason}\n"
                    f"> **Notes:** {notes or 'N/A'}"
                ),
                color=discord.Color.green(),
                timestamp=interaction.created_at
            )
            summary_embed.set_footer(
                text=f"@{interaction.user.name}",
                icon_url=interaction.user.display_avatar.url
            )
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="Jump To",
                    style=discord.ButtonStyle.link,
                    url=message_link
                )
            )
            await interaction.followup.send(f"{wc} Infraction issued for {user.mention}.", ephemeral=True)
            await notify_channel.send(embed=summary_embed, view=view)

    @app_commands.command(name="view", description="View an infraction's details.")
    @app_commands.describe(id="The ID of the infraction to view.")
    async def view(self, interaction: discord.Interaction, id: str):
        if not any(role.id in REQUIRED_ROLE_IDS for role in interaction.user.roles):
            return await interaction.response.send_message(
                f"{wx} You do not have permission to use this command.",
                ephemeral=True
            )

        IGNORED_ROLE_ID = 1363615015101399211

        def get_highest_role(roles):
            filtered = [role for role in roles if role.id != IGNORED_ROLE_ID]
            return max(filtered, key=lambda r: r.position) if filtered else None

        infractions = load_infractions()
        id = id.upper()
        infraction = next((i for i in infractions if i["case_id"].upper() == id), None)

        if infraction is None:
            return await interaction.response.send_message(
                f"Infraction with Case ID `{id}` not found.",
                ephemeral=True
            )

        member = interaction.guild.get_member(infraction["staff_id"])

        if member and interaction.user.id != 973619439822049330:
            issuer_top = get_highest_role(interaction.user.roles)
            target_top = get_highest_role(member.roles)

            if issuer_top and target_top and issuer_top.position <= target_top.position:
                return await interaction.response.send_message(
                    f"{wx} You cannot view infractions for someone whose highest role is the same or higher than yours.",
                    ephemeral=True
                )

        issuer = await bot.fetch_user(infraction["issuer_id"])
        staff = await bot.fetch_user(infraction["staff_id"])

        notes = infraction["notes"] if infraction["notes"] else "N/A"
        infraction_link = infraction.get("message_link", "N/A")

        embed = discord.Embed(
            color=0x2b2d31,
            timestamp=interaction.created_at
        )

        embed.add_field(
            name="<:rules:1422710161688104972> Case Information",
            value=(
                f"> **Issuer:** {issuer.mention}\n"
                f"> **Staff Member:** {staff.mention}\n"
                f"> **Action:** {infraction['infraction_type']}\n"
                f"> **Reason:** {infraction['reason']}\n"
            ),
            inline=False
        )

        embed.add_field(
            name=":clipboard: Additional Information",
            value=(
                f"> **Notes:** {notes}\n"
                f"> [**Jump to Infraction**]({infraction_link})"
            ),
            inline=False
        )

        embed.set_footer(
            text=f"Created by @{issuer.name}",
            icon_url=issuer.display_avatar.url
        )

        embed.set_author(
            name=f"Infraction | {infraction['case_id'].upper()}" +
            (" (Voided)" if infraction.get("is_voided") else "")
        )
        embed.set_thumbnail(url=staff.display_avatar.url)

        await interaction.response.send_message(
            embed=embed,
            view=InfractionEditView(infraction, interaction)
        )

bot.tree.add_command(InfractionCommands())

class InfractionEditView(ui.View):
    def __init__(self, infraction, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.infraction = infraction
        self.interaction = interaction
        self.add_item(EditButton(self.infraction, self.interaction))
        self.add_item(VoidButton(self.infraction, self.interaction))

class EditButton(ui.Button):
    def __init__(self, infraction, interaction: discord.Interaction):
        super().__init__(label="Edit", style=discord.ButtonStyle.primary, emoji="<:edit:1434348961627504731>", custom_id="edit_infraction")
        self.infraction = infraction
        self.interaction = interaction

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            return await interaction.response.send_message("You cannot edit someone else's view.", ephemeral=True)
        await interaction.response.edit_message(view=InfractionEditDropdownView(self.infraction, self.interaction))

class VoidButton(ui.Button):
    def __init__(self, infraction, interaction: discord.Interaction):
        super().__init__(label="Void", style=discord.ButtonStyle.danger, emoji="⚠️", custom_id="void_infraction")
        self.infraction = infraction
        self.interaction = interaction

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            return await interaction.response.send_message(f"{wx} You cannot interact with this.", ephemeral=True)

        message_link = None
        with open('infractions.json', 'r') as file:
            data = json.load(file)

        for inf in data:
            if inf['case_id'] == self.infraction['case_id']:
                if inf.get('is_voided', False):
                    return await interaction.response.send_message(f"{wx} This infraction has already been voided.", ephemeral=True)
                inf['is_voided'] = True
                message_link = inf.get('message_link')
                break

        with open('infractions.json', 'w') as file:
            json.dump(data, file, indent=4)

        if message_link:
            parts = message_link.rstrip('/').split('/')
            channel_id, message_id = int(parts[-2]), int(parts[-1])

            channel = interaction.client.get_channel(channel_id) \
                      or await interaction.client.fetch_channel(channel_id)
            try:
                original = await channel.fetch_message(message_id)
                if original.embeds:
                    e = original.embeds[0].copy()
                    e.color = discord.Color.red()
                    e.title = "Infraction Voided"
                    await original.edit(embed=e)
            except Exception as err:
                print(f"Failed updating original infraction embed: {err}")

        CHANNEL_ID = 1434349075330764910
        log_channel = interaction.client.get_channel(CHANNEL_ID)
        if log_channel and message_link:
            log_embed = discord.Embed(
                title="Infraction Voided",
                description=(
                    f"> **Case ID:** `{self.infraction['case_id']}`\n"
                    f"> **Action:** {self.infraction['infraction_type']}\n"
                    f"> **Reason:** {self.infraction['reason']}\n"
                    f"> **Notes:** {self.infraction.get('notes', '') or 'N/A'}"
                ),
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            log_embed.set_footer(
                text=f"@{interaction.user.name}",
                icon_url=interaction.user.display_avatar.url
            )
            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                label="Jump To",
                style=discord.ButtonStyle.link,
                url=message_link
            ))

            await log_channel.send(embed=log_embed, view=view)

        await interaction.message.edit(
            content=f"{wc} **{interaction.user.name}**, I've voided the infraction.",
            embed=None,
            view=None
        )

class ImDoneButton(discord.ui.Button):
    def __init__(self, infraction, interaction: discord.Interaction):
        super().__init__(label="I'm Done", style=discord.ButtonStyle.success)
        self.infraction = infraction
        self.interaction = interaction

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            return await interaction.response.send_message(f"{wx} You cannot interact with this.", ephemeral=True)
        await interaction.response.edit_message(view=InfractionEditView(self.infraction, self.interaction))

class InfractionEditDropdownView(discord.ui.View):
    def __init__(self, infraction, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.infraction = infraction
        self.interaction = interaction
        self.add_item(InfractionDropdown(self.infraction, self.interaction))
        self.add_item(ImDoneButton(self.infraction, self.interaction))

class InfractionDropdown(ui.Select):
    def __init__(self, infraction, interaction: discord.Interaction):
        options = [
            discord.SelectOption(label="Action", description="Edit the action."),
            discord.SelectOption(label="Reason", description="Edit the reason."),
            discord.SelectOption(label="Notes", description="Edit the notes."),
        ]
        super().__init__(placeholder="Select what to edit...", options=options, custom_id="edit_dropdown")
        self.infraction = infraction
        self.interaction = interaction

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            return await interaction.response.send_message(f"{wx} You cannot interact with this.", ephemeral=True)
        if self.values[0] == "Action":
            await interaction.response.edit_message(view=InfractionActionDropdownView(self.infraction, self.interaction))
        elif self.values[0] == "Reason":
            await self.show_reason_modal(interaction)
        elif self.values[0] == "Notes":
            await self.show_notes_modal(interaction)

    async def show_reason_modal(self, interaction: discord.Interaction):
        modal = discord.ui.Modal(title="Edit Reason")
        
        reason_input = discord.ui.TextInput(
            label="Reason", 
            style=discord.TextStyle.long,
            default=self.infraction['reason'],
            placeholder="The reason for the action",
            required=True,
            max_length=400
        )
        modal.add_item(reason_input)

        async def on_modal_submit(modal_interaction: discord.Interaction):
            new_reason = reason_input.value
            old_reason = self.infraction['reason']
            self.infraction['reason'] = new_reason

            with open('infractions.json', 'r') as file:
                data = json.load(file)

            for infraction in data:
                if infraction['case_id'] == self.infraction['case_id']:
                    infraction['reason'] = new_reason
                    break

            with open('infractions.json', 'w') as file:
                json.dump(data, file, indent=4)

            await self.update_infraction_embed(modal_interaction)
            channel = interaction.client.get_channel(1421280446079041687)

            if channel:
                embed = discord.Embed(
                    title="Infraction Updated",
                    description=(
                        f">>> **Case ID:** `{self.infraction['case_id']}`\n"
                        f"**Action:** {self.infraction['infraction_type']}\n"
                        f"**Old Reason:** {old_reason}\n"
                        f"**Updated Reason:** {new_reason}\n"
                        f"**Notes:** {self.infraction.get('notes', 'None')}"
                    ),
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(
                    text=f"@{modal_interaction.user.name}",
                    icon_url=modal_interaction.user.display_avatar.url
                )

                view = discord.ui.View()
                view.add_item(
                    discord.ui.Button(
                        label="Jump To",
                        url=self.infraction['message_link']
                    )
                )

                await channel.send(embed=embed, view=view)

        modal.on_submit = on_modal_submit
        await interaction.response.send_modal(modal)

    async def show_notes_modal(self, interaction: discord.Interaction):
        modal = discord.ui.Modal(title="Edit Notes")
        notes_input = discord.ui.TextInput(
            label="Notes", 
            style=discord.TextStyle.long,
            default=self.infraction['notes'] if self.infraction.get('notes') else '',
            placeholder="Additional notes or context",
            required=False,
            max_length=400
        )
        modal.add_item(notes_input)

        async def on_modal_submit(modal_interaction: discord.Interaction):
            new_notes = notes_input.value
            old_notes = self.infraction.get('notes', 'None')

            with open('infractions.json', 'r') as file:
                data = json.load(file)

            updated_infraction = None
            for infraction in data:
                if infraction['case_id'] == self.infraction['case_id']:
                    infraction['notes'] = new_notes
                    updated_infraction = infraction
                    break

            if updated_infraction is None:
                return await modal_interaction.response.send_message("Error: Infraction not found.", ephemeral=True)

            with open('infractions.json', 'w') as file:
                json.dump(data, file, indent=4)

            self.infraction = updated_infraction
            await self.update_infraction_embed(modal_interaction)

            embed = discord.Embed(
                title="Infraction Updated",
                description=(
                    f">>> **Case ID:** `{updated_infraction['case_id']}`\n"
                    f"**Action:** {updated_infraction.get('infraction_type', 'Unknown')}\n"
                    f"**Reason:** {updated_infraction.get('reason', 'None')}\n"
                    f"**Old Notes:** {old_notes}\n"
                    f"**Updated Notes:** {new_notes}"
                ),
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(
                text=f"@{modal_interaction.user.name}",
                icon_url=modal_interaction.user.display_avatar.url
            )

            view = discord.ui.View()
            message_link = updated_infraction.get('message_link')
            if message_link:
                view.add_item(discord.ui.Button(label="Jump To", url=message_link))

            log_channel = interaction.client.get_channel(1434349075330764910)
            if log_channel:
                await log_channel.send(embed=embed, view=view)

            if message_link:
                try:
                    message_id = int(message_link.split("/")[-1])
                    parts = message_link.split('/')
                    if len(parts) >= 6:
                        channel_id = int(parts[-2])
                        message_id = int(parts[-1])
                        channel = modal_interaction.guild.get_channel(channel_id)
                        if channel:
                            original_message = await channel.fetch_message(message_id)
                            if original_message.thread:
                                await original_message.thread.send(f"<:arrow:1421979023356989582> **Updated Notes:** {new_notes}")
                except Exception as e:
                    print(f"Failed to send notes update: {e}")

        modal.on_submit = on_modal_submit
        await interaction.response.send_modal(modal)

    async def update_infraction_embed(self, interaction: discord.Interaction):
        issuer = await bot.fetch_user(self.infraction['issuer_id'])
        staff = await bot.fetch_user(self.infraction['staff_id'])
        notes = self.infraction['notes'] if self.infraction['notes'] else "N/A"
        infraction_link = self.infraction.get('message_link', 'N/A')

        updated_embed = discord.Embed(
            color=0x2b2d31,
            timestamp=self.interaction.created_at
        )
        updated_embed.add_field(
            name="<:rules:1422710161688104972> Case Information",
            value=(
                f"> **Issuer:** {issuer.mention}\n"
                f"> **Staff Member:** {staff.mention}\n"
                f"> **Action:** {self.infraction['infraction_type']}\n"
                f"> **Reason:** {self.infraction['reason']}\n"
            ),
            inline=False
        )
        updated_embed.add_field(
            name=":clipboard: Additional Information",
            value=(
                f"> **Notes:** {notes}\n"
                f"> [**Jump to Infraction**]({infraction_link})"
            ),
            inline=False
        )
        updated_embed.set_footer(text=f"Created by @{issuer.name}", icon_url=issuer.display_avatar.url)
        updated_embed.set_author(
            name=f"Infraction | {self.infraction['case_id']}" + (" (Voided)" if self.infraction.get('is_voided') else "")
        )
        updated_embed.set_thumbnail(url=staff.display_avatar.url)

        await interaction.response.edit_message(
            embed=updated_embed,
            view=InfractionEditView(self.infraction, self.interaction)
        )

        if infraction_link and infraction_link != "N/A":
            try:
                parts = infraction_link.split("/")
                channel_id = int(parts[-2])
                message_id = int(parts[-1])
                channel = await bot.fetch_channel(channel_id)
                message = await channel.fetch_message(message_id)
                new_log_embed = discord.Embed(
                    title="⚠️ New Infraction Issued!",
                    description=(
                        f"- **⚠️ Staff Member:** {staff.mention}\n"
                        f"- **🔨 Action:** {self.infraction['infraction_type']}\n"
                        f"- **📋 Reason:** {self.infraction['reason']}\n\n"
                        "-# If you believe this infraction was unjustified, please contact a Management Team member."
                    ),
                    color=0x2b2d31,
                    timestamp=interaction.created_at
                )
                new_log_embed.set_author(name=f"Issued By, {issuer.display_name}", icon_url=issuer.display_avatar.url)
                new_log_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1404567596698832967/1441637981231382690/ohio_new.png?ex=69232e3f&is=6921dcbf&hm=a7bdd936bd6e58212a137e557734944d94f56e0cf7588a9c9db322eb2eeb8487&")
                new_log_embed.set_footer(text=f"Case ID: {self.infraction['case_id']}", icon_url=staff.display_avatar.url)

                await message.edit(content=f"{staff.mention}", embed=new_log_embed)

            except Exception as e:
                print(f"Failed to update infraction log message: {e}")

class InfractionActionDropdownView(ui.View):
    def __init__(self, infraction, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.infraction = infraction
        self.interaction = interaction
        self.add_item(ActionSelect(self.infraction, self.interaction))
        self.add_item(CancelButton(self.infraction, self.interaction))

class CancelButton(discord.ui.Button):
    def __init__(self, infraction, interaction: discord.Interaction):
        super().__init__(label="Cancel", style=discord.ButtonStyle.danger)
        self.infraction = infraction
        self.interaction = interaction

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            return await interaction.response.send_message(f"{wx} You cannot interact with this.", ephemeral=True)
        await interaction.response.edit_message(view=InfractionEditDropdownView(self.infraction, self.interaction))

class ActionSelect(ui.Select):
    def __init__(self, infraction, interaction: discord.Interaction):
        options = [
            discord.SelectOption(label="Warning", value="Warning"),
            discord.SelectOption(label="Strike", value="Strike"),
            discord.SelectOption(label="Under Investigation", value="Under Investigation"),
            discord.SelectOption(label="Demotion", value="Demotion"),
            discord.SelectOption(label="Termination", value="Termination"),
        ]
        super().__init__(placeholder="Select a new action...", options=options, custom_id="action_select")
        self.infraction = infraction
        self.interaction = interaction

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            return await interaction.response.send_message(f"{wx} You cannot interact with this.", ephemeral=True)
        old_action = self.infraction.get('infraction_type', 'Unknown')
        self.infraction['infraction_type'] = self.values[0]

        infractions = load_infractions()
        for i in infractions:
            if i['case_id'] == self.infraction['case_id']:
                i['infraction_type'] = self.values[0]
        save_infractions(infractions)

        issuer = await bot.fetch_user(self.infraction['issuer_id'])
        staff = await bot.fetch_user(self.infraction['staff_id'])
        notes = self.infraction['notes'] if self.infraction['notes'] else "N/A"
        infraction_link = self.infraction.get('message_link', 'N/A')

        updated_embed = discord.Embed(
            color=0x2b2d31,
            timestamp=self.interaction.created_at
        )
        updated_embed.add_field(
            name="<:rules:1422710161688104972> Case Information",
            value=(
                f"> **Issuer:** {issuer.mention}\n"
                f"> **Staff Member:** {staff.mention}\n"
                f"> **Action:** {self.infraction['infraction_type']}\n"
                f"> **Reason:** {self.infraction['reason']}\n"
            ),
            inline=False
        )
        updated_embed.add_field(
            name=":clipboard: Additional Information",
            value=(
                f"> **Notes:** {notes}\n"
                f"> [**Jump to Infraction**]({infraction_link})"
            ),
            inline=False
        )
        updated_embed.set_footer(text=f"Created by @{issuer.name}", icon_url=issuer.display_avatar.url)
        updated_embed.set_author(
            name=f"Infraction | {self.infraction['case_id']}" + (" (Voided)" if self.infraction.get('is_voided') else "")
        )
        updated_embed.set_thumbnail(url=staff.display_avatar.url)

        await interaction.response.edit_message(embed=updated_embed, view=InfractionEditView(self.infraction, self.interaction))

        log_embed = discord.Embed(
            title="Infraction Updated",
            description=(
                f">>> **Case ID:** `{self.infraction['case_id']}`\n"
                f"**Old Action:** {old_action}\n"
                f"**Updated Action:** {self.infraction['infraction_type']}\n"
                f"**Reason:** {self.infraction.get('reason', 'None')}\n"
                f"**Notes:** {self.infraction.get('notes', 'None')}"

            ),
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        log_embed.set_footer(
            text=f"@{interaction.user.name}",
            icon_url=interaction.user.display_avatar.url
        )

        view = discord.ui.View()
        if infraction_link and infraction_link != "N/A":
            view.add_item(discord.ui.Button(label="Jump To", url=infraction_link))

        log_channel = interaction.client.get_channel(1434349075330764910)
        if log_channel:
            await log_channel.send(embed=log_embed, view=view)

        if infraction_link and infraction_link != "N/A":
            try:
                parts = infraction_link.split("/")
                channel_id = int(parts[-2])
                message_id = int(parts[-1])
                channel = await bot.fetch_channel(channel_id)
                message = await channel.fetch_message(message_id)

                new_log_embed = discord.Embed(
                    title="⚠️ New Infraction Issued!",
                    description=(
                        f"- **⚠️ Staff Member:** {staff.mention}\n"
                        f"- **🔨 Action:** {self.infraction['infraction_type']}\n"
                        f"- **📋 Reason:** {self.infraction['reason']}\n\n"
                        "-# If you believe this infraction was unjustified, please contact a Management Team member."
                    ),
                    color=0x2b2d31,
                    timestamp=interaction.created_at
                )
                new_log_embed.set_author(name=f"Issued By, {issuer.display_name}", icon_url=issuer.display_avatar.url)
                new_log_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1404567596698832967/1441637981231382690/ohio_new.png?ex=69232e3f&is=6921dcbf&hm=a7bdd936bd6e58212a137e557734944d94f56e0cf7588a9c9db322eb2eeb8487&")
                new_log_embed.set_footer(text=f"Case ID: {self.infraction['case_id']}", icon_url=staff.display_avatar.url)

                await message.edit(content=f"{staff.mention}", embed=new_log_embed)

            except Exception as e:
                print(f"Failed to update infraction log message: {e}")

@bot.tree.command(name="promote", description="Promote a staff member.")
@app_commands.describe(
    user="The user to promote",
    role="The new role to assign",
    reason="The reason for the promotion"
)
async def promote(interaction: discord.Interaction, user: discord.Member, role: discord.Role, reason: str = None):
    allowed_roles = {1421270212229206117, 1421270212367487139}
    if not any(role.id in allowed_roles for role in interaction.user.roles):
        return await interaction.response.send_message(f"{wx} You do not have permission to use this command.", ephemeral=True)

    embed = discord.Embed(
        title="Staff Promotion",
        description="The high-ranking team has decided to grant you a promotion! Congratulations!",
        color=0x2b2d31,
        timestamp=datetime.now()
    )
    embed.set_author(
        name=f"Promoted By, {interaction.user.nick or interaction.user.name}",
        icon_url=interaction.user.display_avatar.url
    )
    embed.add_field(name="Staff Member:", value=user.mention, inline=False)
    embed.add_field(name="New Rank:", value=role.mention, inline=False)
    embed.add_field(name="Reason:", value=reason or "No reason provided.", inline=False)
    embed.set_thumbnail(url=user.display_avatar.url)

    channel = interaction.guild.get_channel(1421280352608976936)
    if channel is None:
        return await interaction.response.send_message(f"{wx} Promotion channel not found.", ephemeral=True)

    await channel.send(content=user.mention, embed=embed)
    await interaction.response.send_message(f"{wc} Promotion successfully issued!", ephemeral=True)

@bot.tree.command(name="embed", description="Send embed(s) via raw JSON to a channel.")
@app_commands.describe(channel="Channel to send the embed", json_data="Embed JSON (must contain 'embeds')")
async def embed(interaction: discord.Interaction, channel: discord.TextChannel, json_data: str):
    REQUIRED_ROLE_ID = 1423448883182174259

    if not any(role.id == REQUIRED_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message(f"{wx} You don't have permission to use this command.", ephemeral=True)

    try:
        data = json.loads(json_data)
    except json.JSONDecodeError:
        return await interaction.response.send_message(f"{wx} Invalid JSON.", ephemeral=True)

    embeds_raw = []
    if isinstance(data, dict) and "embeds" in data:
        embeds_raw = data["embeds"]
    elif isinstance(data, list):
        embeds_raw = data
    else:
        return await interaction.response.send_message(f"{wx} Embed JSON must include an 'embeds' list or be a list.", ephemeral=True)

    embeds = []
    try:
        for entry in embeds_raw:
            embeds.append(discord.Embed.from_dict(entry))
    except Exception as e:
        return await interaction.response.send_message(f"{wx} Error parsing embeds: {e}", ephemeral=True)

    if isinstance(data, dict) and "content" in data:
        return await interaction.response.send_message(f"{wx} Content is not allowed.", ephemeral=True)

    view = None
    if "components" in data:
        try:
            view = discord.ui.View()
            for row in data["components"]:
                if row.get("type") != 1:
                    continue
                for component in row.get("components", []):
                    if component.get("type") == 2 and component.get("style") == 5:
                        button = discord.ui.Button(
                            label=component.get("label", "Click"),
                            url=component.get("url")
                        )
                        view.add_item(button)
        except Exception as e:
            return await interaction.response.send_message(f"{wx} Failed to parse components: {e}", ephemeral=True)

    try:
        await channel.send(embeds=embeds, view=view)
        await interaction.response.send_message(f"{wc} Embed(s) sent to {channel.mention}.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(f"{wx} Missing permissions to send to that channel.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"{wx} Failed to send embed: {e}", ephemeral=True)

BLACKLIST_FILE = "say_blacklist.json"

def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return []
    with open(BLACKLIST_FILE, "r") as f:
        data = json.load(f)
        return data.get("blacklisted", [])

def save_blacklist(user_ids):
    with open(BLACKLIST_FILE, "w") as f:
        json.dump({"blacklisted": user_ids}, f, indent=2)

@bot.command(name="saymute")
async def saymute(ctx, user: discord.User):
    if ctx.author.id not in ALLOWED_USERS:
        return await ctx.send(f"{wx} You do not have permission to use this command.")
    
    blacklist = load_blacklist()
    if user.id in blacklist:
        return await ctx.send(f"{wx} That user is already blacklisted.")
    blacklist.append(user.id)
    save_blacklist(blacklist)
    await ctx.send(f"{wc} **{user.name}** has been blacklisted from using say.")

ALLOWED_USERS = {1013837301450821702, 973619439822049330}

@bot.command(name="sayunmute")
async def sayunmute(ctx, user: discord.User):
    if ctx.author.id not in ALLOWED_USERS:
        return await ctx.send(f"{wx} You do not have permission to use this command.")
    
    blacklist = load_blacklist()
    if user.id not in blacklist:
        return await ctx.send(f"{wx} That user is not blacklisted.")
    blacklist.remove(user.id)
    save_blacklist(blacklist)
    await ctx.send(f"{wc} **{user.name}** has been removed from the blacklist.")

class SayModal(discord.ui.Modal, title="Send a Message as the Bot"):
    channel: discord.TextChannel

    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel
        self.message_input = discord.ui.TextInput(
            label="Message Content",
            style=discord.TextStyle.paragraph,
            placeholder="Type your message here (supports multiple lines)",
            required=True,
            max_length=2000
        )
        self.add_item(self.message_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await self.channel.send(self.message_input.value)
            await interaction.response.send_message(f"{wc} Message sent to {self.channel.mention}.", ephemeral=True)

            log_channel = interaction.client.get_channel(1433658863076249680)
            if log_channel:
                embed = discord.Embed(
                    title="Message Sent via /say",
                    description=f"**Channel:** {self.channel.mention}\n**Content:**\n{self.message_input.value}",
                    color=0x2b2d31
                )
                embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await log_channel.send(embed=embed)

        except discord.Forbidden:
            await interaction.response.send_message(f"{wx} I don't have peission to send messages to that channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"{wx} Failed to send message: {e}", ephemeral=True)

@bot.tree.command(name="say", description="Send a message as the bot to a specified channel.")
@app_commands.describe(channel="The channel to send the message in")
async def say(interaction: discord.Interaction, channel: discord.TextChannel):
    if interaction.user.id in load_blacklist():
        return await interaction.response.send_message(f"{wx} You are blacklisted from using this command.", ephemeral=True)

    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(f"{wx} You don't have permission to use this command.", ephemeral=True)
    await interaction.response.send_modal(SayModal(channel))

API_URL = "https://api.policeroleplay.community/v1/server/command"

REQUIRED_BASE_ROLES = [
    1421277606275452970,
    1434353486778339348
]

REQUIRED_ADMIN_ROLES = [
    1421270212229206117, 
    1421270212367487139,
    1434353486778339348
]
LOG_CHANNEL_ID = 1387975556322168833

@bot.tree.command(name="erlc", description="Execute an ER:LC server command")
@app_commands.describe(command="The ER:LC command to run")
async def erlc(interaction: discord.Interaction, command: str):
    user = interaction.user

    if not command.startswith(":"):
        command = f":{command}"

    user_role_ids = [role.id for role in user.roles]
    if not any(role in user_role_ids for role in REQUIRED_BASE_ROLES):
        return await interaction.response.send_message(
            f"{wx} You do not have permission to use this command.", ephemeral=True
        )

    sensitive_keywords = [":mod", ":admin", ":kick", ":ban", ":unmod", ":unadmin"]
    if any(keyword in command.lower() for keyword in sensitive_keywords):
        if not any(role in user_role_ids for role in REQUIRED_ADMIN_ROLES):
            return await interaction.response.send_message(
                f"{wx} You do not have permission to run the `{command}` command.", ephemeral=True
            )


    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            headers = {
                "Content-Type": "application/json",
                "server-key": API_KEY
            }
            payload = {"command": command}
            async with session.post(API_URL, json=payload, headers=headers) as response:
                text = await response.text()
                if response.status == 200:
                    print(f"[COMMAND LOG] {user} ran {command} (SUCCESS)")
                    await interaction.response.send_message(f"{wc} Command executed successfully.", ephemeral=True)
                else:
                    print(f"[COMMAND LOG] {user} ran {command} (FAILED) — Status: {response.status} — {text}")
                    await interaction.response.send_message(
                        f"{wx} Failed to execute command. Status: {response.status}\nResponse: {text}",
                        ephemeral=True
                    )
    except Exception as e:
        print(f"[COMMAND LOG] {user} ran {command} (ERROR) — {str(e)}")
        try:
            await interaction.response.send_message(f"{wx} Unexpected error: {str(e)}", ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send(f"{wx} Unexpected error: {str(e)}", ephemeral=True)

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(
            title="ER:LC Command Executed",
            description=f"`{command}`",
            color=0x2b2d31
        )
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.set_footer(text=f"User ID: {user.id}")
        await log_channel.send(embed=embed)


STATUS_URL = "https://status.roblox.com"
CATEGORY_ID = 1383846284611551263
CHANNEL_NAME = "roblox-status"
STATUS_PAGE_LINK = "https://status.roblox.com"

MESSAGE_TRACKER_FILE = "tracked_status_message.json"

def save_tracked_message_id(message_id):
    with open(MESSAGE_TRACKER_FILE, "w") as f:
        json.dump({"id": message_id}, f)

def load_tracked_message_id():
    if os.path.exists(MESSAGE_TRACKER_FILE):
        with open(MESSAGE_TRACKER_FILE, "r") as f:
            data = json.load(f)
            return data.get("id")
    return None

tracked_message_id = load_tracked_message_id()

def parse_incidents(soup):
    incidents = []
    times = soup.find_all("strong", class_="incident_time")
    messages = soup.find_all("span", class_="incident_message_details")

    for i in range(len(messages)):
        time_text = times[i].text.strip() if i < len(times) else "Unknown time"
        message_text = messages[i].text.strip() if i < len(messages) else "No message"
        status_tag = messages[i].find_previous_sibling("strong")
        status_text = status_tag.text.strip() if status_tag else "Unknown status"

        try:
            parsed_time = dateparser.parse(time_text)
        except Exception:
            parsed_time = None

        incidents.append({
            "time": time_text,
            "parsed_time": parsed_time,
            "status": status_text,
            "message": message_text
        })
    return incidents

@tasks.loop(seconds=20)
async def check_roblox_status():
    global tracked_message_id
    try:
        response = requests.get(STATUS_URL, timeout=10)
        if response.status_code != 200:
            print(f"Error fetching Roblox status: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        status_element = soup.find("strong", id="statusbar_text")
        if not status_element:
            print("Status element not found in page.")
            return

        status_text = status_element.text.strip()

        if status_text.lower() == "all systems operational":
            return

        incidents = parse_incidents(soup)
        if not incidents:
            print("No incidents found.")
            return

        today = datetime.now().date()
        incidents = [inc for inc in incidents if inc["parsed_time"] and inc["parsed_time"].date() == today]
        if not incidents:
            return

        guild = bot.get_guild(1421266702326435912)
        if not guild:
            print("Guild not found.")
            return

        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        if not category:
            print("Category not found.")
            return

        channel = discord.utils.get(category.channels, name=CHANNEL_NAME)
        if channel is None:
            channel = await guild.create_text_channel(CHANNEL_NAME, category=category)
            print(f"Created channel {CHANNEL_NAME}")

        embed = discord.Embed(
            title="⚠️ Roblox Incident Detected",
            description=f"Current Status: **{status_text}**",
            color=0xFF0000,
            url=STATUS_PAGE_LINK
        )

        for incident in incidents:
            embed.add_field(
                name=f"{incident['time']} {incident['status']}",
                value=incident['message'],
                inline=False
            )

        embed.set_footer(text="Roblox Status Monitor")

        view = discord.ui.View()
        emoji = discord.PartialEmoji(name="ROBLOX", id=1387990813346369566)
        view.add_item(discord.ui.Button(label="Status Page", url=STATUS_PAGE_LINK, emoji=emoji))

        if tracked_message_id:
            try:
                msg = await channel.fetch_message(tracked_message_id)
                await msg.edit(embed=embed, view=view)
                return
            except discord.NotFound:
                print("Tracked message not found, sending new one.")
            except Exception as e:
                print(f"Error editing message: {e}")

        msg = await channel.send(embed=embed, view=view)
        tracked_message_id = msg.id
        save_tracked_message_id(tracked_message_id)

    except Exception as e:
        print(f"Error checking Roblox status: {e}")


class DepartmentPaginatorView(discord.ui.View):
    def __init__(self, members, page=1):
        super().__init__(timeout=None)
        self.members = members
        self.page = page
        self.max_pages = (len(members) - 1) // 10 + 1
        self.first_button = discord.ui.Button(label="⏮️", style=discord.ButtonStyle.secondary, disabled=page == 1)
        self.left_button = discord.ui.Button(label="⬅️", style=discord.ButtonStyle.secondary, disabled=page == 1)
        self.right_button = discord.ui.Button(label="➡️", style=discord.ButtonStyle.secondary, disabled=page == self.max_pages)
        self.last_button = discord.ui.Button(label="⏭️", style=discord.ButtonStyle.secondary, disabled=page == self.max_pages)
        if self.max_pages > 1:
            self.add_item(self.first_button)
            self.add_item(self.left_button)
            self.add_item(self.right_button)
            self.add_item(self.last_button)
        self.first_button.callback = self.first_callback
        self.left_button.callback = self.left_callback
        self.right_button.callback = self.right_callback
        self.last_button.callback = self.last_callback

    async def first_callback(self, interaction):
        if self.page != 1:
            self.page = 1
            await self.update_embed(interaction)

    async def left_callback(self, interaction):
        if self.page > 1:
            self.page -= 1
            await self.update_embed(interaction)

    async def right_callback(self, interaction):
        if self.page < self.max_pages:
            self.page += 1
            await self.update_embed(interaction)

    async def last_callback(self, interaction):
        if self.page != self.max_pages:
            self.page = self.max_pages
            await self.update_embed(interaction)

    async def update_embed(self, interaction):
        start = (self.page - 1) * 10
        end = start + 10
        page_members = self.members[start:end]
        embed = discord.Embed(title=f"Department Members [{len(self.members)}]", color=0x2b2d31)
        for member in page_members:
            embed.add_field(
                name=member['roblox'],
                value=(
                    f"> **Username:** {member['roblox']}\n"
                    f"> **Department:** {member['department']}\n"
                    f"> **Rank:** {member['rank']}\n"
                    f"> **Associated Discord:** <@{member['discord']}>\n"
                    f"> **Join Date:** <t:{member['join_date']}:R>"
                ),
                inline=False
            )
        embed.set_footer(text=f"Page {self.page} of {self.max_pages}")
        await interaction.response.edit_message(embed=embed, view=self)

department_group = app_commands.Group(name="department", description="Department management commands")

def load_department():
        if not os.path.exists("department.json"):
            with open("department.json", "w") as f:
                json.dump([], f)
        with open("department.json", "r") as f:
            return json.load(f)

def save_department(data):
    with open("department.json", "w") as f:
        json.dump(data, f, indent=4)

@department_group.command(name="list", description="List department members")
async def department_list(interaction: discord.Interaction):
    data = load_department()
    if not data:
        return await interaction.response.send_message(f"{wx} No department members found.", ephemeral=True)
    view = DepartmentPaginatorView(data)
    embed = discord.Embed(title=f"Department Members [{len(data)}]", color=0x2b2d31)
    for member in data[:10]:
        embed.add_field(
            name=member['roblox'],
            value=(
                f"> **Username:** {member['roblox']}\n"
                f"> **Department:** {member['department']}\n"
                f"> **Rank:** {member['rank']}\n"
                f"> **Associated Discord:** <@{member['discord']}>\n"
                f"> **Join Date:** <t:{member['join_date']}:R>"
            ),
            inline=False
        )
    embed.set_footer(text="Page 1 of {}".format(view.max_pages))
    await interaction.response.send_message(embed=embed, view=view)

@department_group.command(name="add", description="Add a department member")
@app_commands.describe(roblox="Roblox username", discord_user="Discord user", department="Department", rank="Rank")
@app_commands.choices(department=[
    app_commands.Choice(name="Unknown", value="Unknown"),
    app_commands.Choice(name="Unknown", value="Unknown"),
    app_commands.Choice(name="Unknown", value="Unknown"),
    app_commands.Choice(name="Unknown", value="Unknown"),
    app_commands.Choice(name="Other", value="Other")
])
async def department_add(interaction: discord.Interaction, roblox: str, discord_user: discord.User, department: app_commands.Choice[str], rank: str):
    allowed_roles = [1379484725206454415, 1292502190442811564, 1364818988600660030]
    if not any(role.id in allowed_roles for role in interaction.user.roles):
        return await interaction.response.send_message(f"{wx} You do not have permission to use this command.", ephemeral=True)
    data = load_department()
    if any(m['roblox'].lower() == roblox.lower() for m in data):
        return await interaction.response.send_message(f"{wx} That user is already in the department database.", ephemeral=True)
    entry = {
        "roblox": roblox,
        "discord": discord_user.id,
        "department": department.value,
        "rank": rank,
        "join_date": int(time.time())
    }
    data.append(entry)
    save_department(data)
    await interaction.response.send_message(f"{wc} Added **{roblox}** (<@{discord_user.id}>) to the department.", ephemeral=True)

@department_group.command(name="remove", description="Remove a department member")
@app_commands.describe(roblox="Roblox username")
async def department_remove(interaction: discord.Interaction, roblox: str):
    allowed_roles = [1379484725206454415, 1292502190442811564, 1364818988600660030]
    if not any(role.id in allowed_roles for role in interaction.user.roles):
        return await interaction.response.send_message(f"{wx} You do not have permission to use this command.", ephemeral=True)
    data = load_department()
    filtered = [m for m in data if m['roblox'].lower() != roblox.lower()]
    if len(filtered) == len(data):
        return await interaction.response.send_message(f"{wx} That user is not in the department database.", ephemeral=True)
    save_department(filtered)
    await interaction.response.send_message(f"{wc} Removed **{roblox}** from the department.", ephemeral=True)

@department_group.command(name="view", description="View a department member")
@app_commands.describe(roblox="Roblox username")
async def department_view(interaction: discord.Interaction, roblox: str):
    data = load_department()
    member = next((m for m in data if m['roblox'].lower() == roblox.lower()), None)
    if not member:
        return await interaction.response.send_message(f"{wx} That user is not in the department database.", ephemeral=True)
    embed = discord.Embed(title=f"Department Member: {member['roblox']}", color=0x2b2d31)
    embed.add_field(name="Username", value=member['roblox'], inline=True)
    embed.add_field(name="Rank", value=member['rank'], inline=True)
    embed.add_field(name="Department", value=member['department'], inline=True)
    embed.add_field(name="Discord", value=f"<@{member['discord']}>", inline=True)
    embed.add_field(name="Join Date", value=f"<t:{member['join_date']}:R>", inline=True)
    await interaction.response.send_message(embed=embed)

bot.tree.add_command(department_group)

@bot.event
async def on_message(message):
    await results_ping(message)
    await bot.process_commands(message)

session_discord = "Offline"
non_discord_players = set()

@bot.event
async def on_ready():
    channel = bot.get_channel(1421268025323159693)
    if channel is None:
        print("Channel not found. Check the channel ID or bot permissions.")
        return
    print(f"\nConnected to {len(bot.guilds)} server(s):")
    for guild in bot.guilds:
        print(f" - {guild.name} (ID: {guild.id}) | Members: {guild.member_count}")
    print("\n" + '-' * 50)

    print(f"Logged in as {bot.user}")
    bot.add_view(VoteView())
    bot.add_view(LOAButtons())
    bot.add_view(LOAManageView())
    loa_data = load_loa_data()
    active_loas = [loa for loa in loa_data if loa["status"] == "accepted" and not loa.get("ended")]
    bot.add_view(LOAActiveView(active_loas))
    check_loa_expiry.start()
    bot.server_info_message = None
    check_roblox_status.start()

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} application command(s).")
        if synced:
            print("Slash commands:")
            for cmd in synced:
                print(f"- /{cmd.name}: {cmd.description}")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    await start_background_tasks()
    
    try:
        with open('server_info_message_id.txt', 'r') as f:
            message_id = int(f.read())
        channel = bot.get_channel(1421268025323159693)
        if channel is None:
            print(f"Error: Channel with ID {1421268025323159693} not found.")
            return

        try:
            bot.server_info_message = await channel.fetch_message(message_id)
        except discord.Forbidden:
            print("Error: Bot does not have permission to fetch the message.")
        except discord.HTTPException as e:
            print(f"Error fetching message: {e}")
    except Exception as e:
        print(f"Error while reading or fetching message ID: {e}")

    if not update_stats.is_running():
        update_stats.start()

ALLOWED_ROLE_IDS = [
    1421270212367487139,
    1436787230961303674,
    1436787223969136800
]

@bot.tree.command(name="globalban", description="Ban a user from all servers the bot is in")
@app_commands.describe(user="User to ban")
async def globalban(interaction: discord.Interaction, user: discord.User):
    if not any(role.id in ALLOWED_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message(f"{wx} You do not have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    results = []
    
    for guild in bot.guilds:
        if guild.name.lower() == "nathan's bot testing":
            continue
        
        member = guild.get_member(user.id)
        invoker = guild.get_member(interaction.user.id)
        
        if not invoker:
            results.append(f"{wx} {guild.name}: You are not in this server")
            continue
        
        if member and member.top_role >= invoker.top_role:
            results.append(f"{wx} {guild.name}: Cannot ban due to role hierarchy")
            continue
        
        try:
            await guild.ban(user, reason=f"Global ban by {interaction.user}")
            results.append(f"{wc} {guild.name}: Banned successfully")
        except discord.Forbidden:
            results.append(f"{wx} {guild.name}: Missing permissions")
        except Exception as e:
            results.append(f"{wx} {guild.name}: Failed - {str(e)}")
    
    await interaction.followup.send("\n".join(results), ephemeral=True)

async def results_ping(message):
    channel_id = 1421269122607612155
    role_ids = [
        1421269170506567850,
        1421269172502925362,
        1421270214183616642,
        1421277606275452970,
        1421981149818785903
    ]
    if message.channel.id != channel_id:
        return
    
    if "Staff" not in message.content:
        return
    
    for user in message.mentions:
        member = message.guild.get_member(user.id)
        if not member:
            continue
        roles = []
        for rid in role_ids:
            role = message.guild.get_role(rid)
            if role and role not in member.roles:
                roles.append(role)
        if roles:
            await member.add_roles(*roles, reason="Mentioned in results channel")

def clean_code(code: str):
    language_specifiers = [
        "python", "py", "javascript", "js", "html", "css", "php", "md", "markdown", "go", "golang",
        "c", "c++", "cpp", "c#", "cs", "csharp", "java", "ruby", "rb", "coffee-script", "coffeescript",
        "coffee", "bash", "shell", "sh", "json", "http", "pascal", "perl", "rust", "sql", "swift",
        "vim", "xml", "yaml"
    ]
    loops = 0
    while code.startswith("`"):
        code = code[1:]
        loops += 1
        if loops == 3:
            loops = 0
            break
    for language_specifier in language_specifiers:
        if code.startswith(language_specifier):
            code = code[len(language_specifier):].lstrip()
    while code.endswith("`"):
        code = code[:-1]
        loops += 1
        if loops == 3:
            break
    return code

@bot.command(name="eval", aliases=['e'])
@commands.check(lambda ctx: ctx.author.id in [973619439822049330, 877448869087178752])
async def eval(ctx, *, code):
    code = clean_code(code)
    has_return = "return" in code
    code = "\n".join(f"    {i}" for i in code.splitlines())
    code = f"async def eval_expr():\n{code}"
    def send(text):
        ctx.bot.loop.create_task(ctx.send(text))
    env = {
        "bot": ctx.bot,
        "client": ctx.bot,
        "ctx": ctx,
        "discord": discord,
        "print": send,
        "_author": ctx.author,
        "_message": ctx.message,
        "_channel": ctx.channel,
        "_guild": ctx.guild,
        "_me": ctx.me,
    }
    env.update(globals())
    try:
        start_time = time.time()
        exec(code, env)
        eval_expr = env["eval_expr"]
        result = await eval_expr()
        end_time = time.time()
        elapsed_time = end_time - start_time
        if has_return:
            response = f"**Output:**\n```{result}```\n**Time Taken:**\n```{elapsed_time:.6f}```"
            await ctx.send(response)
        else:
            await ctx.message.add_reaction("<:whitecheck:1444129744777117726>")
    except Exception:
        await ctx.send(f"```{traceback.format_exc()}```")

bot.run("MTMxOTY1NTE5NDU0NzU4OTE3MA.GM_nN0.hdSxtXxc41RFdBEvHDoFu6v2LlCXkB_xPFoKdk")