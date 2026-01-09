import discord
from discord.ext import commands
from discord import app_commands
import json, os, re
from datetime import datetime, timezone, timedelta

# ================== CONFIG ==================
TOKEN = os.getenv("DISCORD_TOKEN")
RANK_CHANNEL_ID = int(os.getenv("RANK_CHANNEL_ID", "0"))

VN_TZ = timezone(timedelta(hours=7))
RANK_FILE = "ranking.json"
DAILY_FILE = "daily_logs.json"

# ================== BOT ==================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================== UTILS ==================
def load(file, default):
    if not os.path.exists(file):
        return default
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def is_admin(member: discord.Member):
    return member.guild_permissions.administrator

# ================== READY ==================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot online & slash synced: {bot.user}")

# ================== PARSE BẢNG RANK ==================
def parse_ranking_message(content: str):
    lines = [l.strip() for l in content.splitlines() if l.strip()]

    crews, levels, points = [], [], []
    mode = None

    for line in lines:
        if "Tên Crew" in line:
            mode = "crew"; continue
        if "Cấp độ" in line:
            mode = "level"; continue
        if "Điểm" in line:
            mode = "point"; continue

        if mode == "crew" and "[" in line:
            crews.append(line)
        elif mode == "level" and line.isdigit():
            levels.append(int(line))
        elif mode == "point" and line.isdigit():
            points.append(int(line))

    results = []
    for i in range(min(len(crews), len(points))):
        m = re.match(r"\d+\s+\[(\w+)\]\s+(.+)", crews[i])
        if not m:
            continue
        results.append({
            "tag": m.group(1),
            "name": m.group(2),
            "level": levels[i] if i < len(levels) else 0,
            "point": points[i]
        })
    return results

# ================== AUTO NHẬN BẢNG ==================
@bot.event
async def on_message(msg: discord.Message):
    if msg.author.bot:
        return

    if msg.channel.id != RANK_CHANNEL_ID:
        return

    if not is_admin(msg.author):
        return

    parsed = parse_ranking_message(msg.content)
    if not parsed:
        return

    ranking = load(RANK_FILE, {})
    daily = load(DAILY_FILE, {})

    today = datetime.now(VN_TZ).strftime("%Y-%m-%d")
    daily[today] = []

    for item in parsed:
        tag = item["tag"]
        if tag not in ranking:
            ranking[tag] = {
                "name": item["name"],
                "total": 0
            }
        ranking[tag]["total"] += item["point"]
        daily[today].append(item)

    save(RANK_FILE, ranking)
    save(DAILY_FILE, daily)

    desc = ""
    for i, c in enumerate(parsed, start=1):
        desc += f"**{i}. [{c['tag']}] {c['name']}** — +{c['point']} điểm\n"

    embed = discord.Embed(
        title="✅ ĐÃ GHI NHẬN BẢNG XẾP HẠNG NGÀY",
        description=desc,
        color=0x2ecc71
    )
    await msg.reply(embed=embed)

    await bot.process_commands(msg)

# ================== SLASH COMMANDS ==================

# /top
@bot.tree.command(name="top", description="Xem TOP 10 crew tổng điểm cao nhất")
@app_commands.checks.has_permissions(administrator=True)
async def slash_top(interaction: discord.Interaction):
    ranking = load(RANK_FILE, {})
    if not ranking:
        return await interaction.response.send_message(
            "❌ Chưa có dữ liệu.", ephemeral=True
        )

    top10 = sorted(
        ranking.items(),
        key=lambda x: x[1]["total"],
        reverse=True
    )[:10]

    desc = ""
    for i, (tag, data) in enumerate(top10, start=1):
        desc += f"**{i}. [{tag}] {data['name']}** — **{data['total']:,}** điểm\n"

    embed = discord.Embed(
        title="🏆 TOP 10 CREW – TỔNG ĐIỂM",
        description=desc,
        color=0xf1c40f
    )

    await interaction.response.send_message(embed=embed)

# /fullbxh
@bot.tree.command(name="fullbxh", description="Xem FULL bảng xếp hạng crew")
@app_commands.checks.has_permissions(administrator=True)
async def slash_fullbxh(interaction: discord.Interaction):
    ranking = load(RANK_FILE, {})
    if not ranking:
        return await interaction.response.send_message(
            "❌ Chưa có dữ liệu.", ephemeral=True
        )

    sorted_all = sorted(
        ranking.items(),
        key=lambda x: x[1]["total"],
        reverse=True
    )

    desc = ""
    embeds = []

    for i, (tag, data) in enumerate(sorted_all, start=1):
        desc += f"**{i}. [{tag}] {data['name']}** — {data['total']:,} điểm\n"

        if i % 20 == 0:
            embeds.append(discord.Embed(
                title="📊 BẢNG XẾP HẠNG CREW",
                description=desc,
                color=0x3498db
            ))
            desc = ""

    if desc:
        embeds.append(discord.Embed(
            title="📊 BẢNG XẾP HẠNG CREW",
            description=desc,
            color=0x3498db
        ))

    await interaction.response.send_message(embeds=embeds)

# /resetbxh (confirm YES)
@bot.tree.command(name="resetbxh", description="RESET toàn bộ điểm crew (confirm YES)")
@app_commands.describe(confirm="Nhập YES để xác nhận reset")
@app_commands.checks.has_permissions(administrator=True)
async def slash_resetbxh(interaction: discord.Interaction, confirm: str):
    if confirm != "YES":
        return await interaction.response.send_message(
            "❌ Bạn phải nhập **YES** để xác nhận reset.",
            ephemeral=True
        )

    save(RANK_FILE, {})

    embed = discord.Embed(
        title="♻️ RESET BẢNG XẾP HẠNG",
        description="Toàn bộ điểm crew đã được **reset về 0**.",
        color=0xe74c3c
    )
    await interaction.response.send_message(embed=embed)

# ================== RUN ==================
bot.run(TOKEN)
