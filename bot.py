import discord
from discord.ext import commands
import json, os, re
from datetime import datetime, timezone, timedelta

#================== CONFIG ================== 
TOKEN = os.getenv("DISCORD_TOKEN")
RANK_CHANNEL_ID = int(os.getenv("RANK_CHANNEL_ID", "0"))

VN_TZ = timezone(timedalta(hours=7))
RANK_FILE = "ranking.json"
DAILY_FILE = "daily_logs.json"

#================== BOT ================== 
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

#================== UT ================== 
def load(file, default):
  if not os.path.exists(file):
    return default
    with open(file, "r" , encoding="utf-8") as f:
      return json.load(f)

def save(file, data)
