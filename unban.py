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

unban_stop = False

wc = "<:Accepted:1434344224211472527>"
wx = "<:Denied:1434345307336085647>"

API_BASE_URL = "https://api.policeroleplay.community/v1"
API_KEY = "PFHOvZACmfJtWCfEjDNZ-KiIsPZrapOxntYLKfXBkmKmXrKDVxjgeECvtFPmE"

API_BANS_URL = f"{API_BASE_URL}/server/bans"

def get_prefix(bot, message):
    return ['-', f'<@{bot.user.id}>']

bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, intents=discord.Intents.all())

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

async def input_erlc_command(command: str):
    try:
        api_url = "https://api.policeroleplay.community/v1/server/command"
        payload = {"command": command}
        headers = {
            "Content-Type": "application/json",
            "server-key": "PFHOvZACmfJtWCfEjDNZ-KiIsPZrapOxntYLKfXBkmKmXrKDVxjgeECvtFPmE"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return f"{wc} Command executed successfully"
                else:
                    return f"{wx} Error executing command. Status: {response.status}, Response: {await response.text()}"
    except Exception as e:
        return f"{wx} Error executing command: {str(e)}"
    
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
    allowed = (973619439822049330, 1293204271302447254)
    if ctx.author.id not in allowed:
        return await ctx.send(f"{wx} You do not have permission to use this command.")

    global unban_stop
    unban_stop = False

    bans = await fetch_erlc_bans()
    if not bans:
        return await ctx.send(f"{wx} No bans found.")

    amount_of_bans = len(bans)
    now = int(time.time())
    estimated_finish = now + (amount_of_bans * 6)

    await ctx.send(f"{wc} Starting unban process... This should be done <t:{estimated_finish}:R>")

    for player_id in bans:
        if unban_stop:
            return await ctx.send(f"{wx} Unban process stopped.")
        await unban_player(player_id)

    await ctx.send(f"{wc} Unban process finished.")

@bot.command(name="stopunban")
async def stop_unban(ctx):
    allowed = (973619439822049330, 1293204271302447254)
    if ctx.author.id not in allowed:
        return await ctx.send(f"{wx} You do not have permission to use this command.")

    global unban_stop
    unban_stop = True
    await ctx.send(f"{wc} Stopping unban process.")

async def fetch_and_print_bans():
    headers = {"server-key": API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(API_BANS_URL, headers=headers) as response:
            data = await response.json()
            print(data)

@bot.command(name="printbans")
async def print_bans(ctx):
    if ctx.author.id != 1293204271302447254:
        return await ctx.send(f"{wx} You do not have permission to use this command.")
    
    headers = {"server-key": API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(API_BANS_URL, headers=headers) as response:
            data = await response.json()
            print(data)

@bot.event
async def on_ready():
    print("Bot is online.")
    print(f"Logged in as {bot.user.name}")
    print(f"ID {bot.user.id}")

bot.run("MTQ0NDAyMjI3MTEwMTYzNjc3MA.GyrUjx.YR_wExz-K4cutvn5W6dc_0IO1clch-J1FKK3Bg")