import discord
import os
import asyncio
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from mangadex_tracker import (
    load_observed_series,
    remove_series_by_title,
    list_tracked_series,
    show_latest_chapter,
    search_manga_title,
    show_manga_info,
    check_for_updates,
    search_manga_titles_for_tracking,
    finalize_tracking,
    confirm_remove_by_index,
)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
user_pending_searches = {}
user_pending_removals = {}

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

observed_series = load_observed_series()


async def start_polling(channel):
    observed_series = load_observed_series()
    await channel.send("👀 Manga tracker is watching for updates...")

    while True:
        print("🔄 Checking for chapter updates...")
        messages = check_for_updates(observed_series, return_messages=True)

        for msg in messages:
            await channel.send(msg)

        await asyncio.sleep(10)


@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {client.user}")

    channel_id = 1326213968527753340
    channel = client.get_channel(channel_id)

    if channel:
        await channel.send("✅ MangaDex bot is online!")
        client.loop.create_task(start_polling(channel))
    else:
        print("❌ Failed to find the update channel. Check channel ID.")


@tree.command(name="track", description="Search for a manga to track")
@app_commands.describe(title="Title of the manga you want to track")
async def track(interaction: discord.Interaction, title: str):
    await interaction.response.defer(thinking=True)  # ⏳ Gives you more time

    message, choices = search_manga_titles_for_tracking(title)
    if choices:
        user_pending_searches[interaction.user.id] = choices

    await interaction.followup.send(message)


@tree.command(name="select", description="Select a manga from the last search to track")
@app_commands.describe(
    number="The number of the manga from the previous search results"
)
async def select(interaction: discord.Interaction, number: int):
    choices = user_pending_searches.get(interaction.user.id)
    if not choices:
        await interaction.response.send_message(
            "⚠️ No active search found. Use /track first."
        )
        return

    index = number - 1
    if not (0 <= index < len(choices)):
        await interaction.response.send_message("❌ Invalid selection.")
        return

    message = finalize_tracking(index, choices, observed_series)
    await interaction.response.send_message(message)
    user_pending_searches.pop(interaction.user.id, None)


@tree.command(name="untrack", description="Untrack a manga by title")
@app_commands.describe(title="Title of the manga to stop tracking")
async def untrack(interaction: discord.Interaction, title: str):
    result = remove_series_by_title(title, observed_series)
    if isinstance(result, str):
        await interaction.response.send_message(result)
    else:
        user_pending_removals[interaction.user.id] = result["options"]
        await interaction.response.send_message(result["prompt"])


@tree.command(
    name="confirm_remove", description="Confirm which manga to remove from tracked list"
)
@app_commands.describe(index="The number from the previous untrack result")
async def confirm_remove(interaction: discord.Interaction, index: int):
    options = user_pending_removals.get(interaction.user.id)
    if not options:
        await interaction.response.send_message(
            "⚠️ No pending removal selection. Use /untrack first."
        )
        return

    message = confirm_remove_by_index(index - 1, options, observed_series)
    await interaction.response.send_message(message)
    user_pending_removals.pop(interaction.user.id, None)


@tree.command(name="list", description="List all tracked manga")
async def list_tracked(interaction: discord.Interaction):
    message = list_tracked_series(observed_series)
    await interaction.response.send_message(message)


@tree.command(name="latest", description="Show the latest tracked chapter for a manga")
@app_commands.describe(title="Title of the manga")
async def latest(interaction: discord.Interaction, title: str):
    message = show_latest_chapter(title, observed_series)
    await interaction.response.send_message(message)


@tree.command(name="search", description="Search MangaDex for a manga")
@app_commands.describe(title="Title to search for on MangaDex")
async def search(interaction: discord.Interaction, title: str):
    message = search_manga_title(title)
    await interaction.response.send_message(message)


@tree.command(name="info", description="Show info for a tracked manga")
@app_commands.describe(title="Title of the tracked manga")
async def info(interaction: discord.Interaction, title: str):
    message = show_manga_info(title, observed_series)
    await interaction.response.send_message(message)


@tree.command(
    name="recheck", description="Manually check all tracked manga for updates"
)
async def recheck(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🔄 Manually checking for chapter updates..."
    )
    check_for_updates(observed_series, return_messages=True)
    await interaction.followup.send("✅ Recheck complete")


client.run(TOKEN)
