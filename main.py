import os
from asyncio import sleep
from threading import Thread
from flask import Flask
import discord
from discord.ext import tasks

# --- Keep-alive web server ---
app = Flask('')


@app.route('/')
def home():
    return "Bot is alive!"


def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))


def keep_alive():
    t = Thread(target=run)
    t.start()


keep_alive()
# ----------------------------

# Guilds where the bot will run
GUILD_IDS = [1188506977408667718]

WORK_WAIT = 10  # Minutes between work command
COLLECT_WAIT = 55  # Minutes between collect command


@tasks.loop(minutes=WORK_WAIT)
async def auto_work(work_cmd, channel, deposit_cmd):
    await work_cmd.__call__(channel=channel)
    await deposit(deposit_cmd, channel)


@tasks.loop(minutes=COLLECT_WAIT)
async def auto_collect(collect_cmd, channel, deposit_cmd):
    await sleep(2)
    await collect_cmd.__call__(channel=channel)
    await deposit(deposit_cmd, channel)


async def deposit(deposit_cmd, channel):
    await sleep(1)
    await deposit_cmd.__call__(channel=channel, amount="all")


client = discord.Client()


@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")


@client.event
async def on_message(message):
    if not message.guild or message.guild.id not in GUILD_IDS:
        return
    if message.author.id != client.user.id:
        return

    if message.content == "!start":
        await message.delete()
        application_commands = await message.channel.application_commands()
        deposit_cmd = collect_cmd = work_cmd = None

        for cmd in application_commands:
            if cmd.type == discord.ApplicationCommandType.chat_input:
                if cmd.id == 901118136529588275:
                    deposit_cmd = cmd
                elif cmd.id == 901118136529588278:
                    collect_cmd = cmd
                elif cmd.id == 901118136529588281:
                    work_cmd = cmd

        if not all([deposit_cmd, collect_cmd, work_cmd]):
            await message.channel.send(
                "❌ One or more commands not found! Check IDs.")
            return

        if auto_work.is_running() and auto_collect.is_running():
            auto_work.restart(work_cmd, message.channel, deposit_cmd)
            auto_collect.restart(collect_cmd, message.channel, deposit_cmd)
        else:
            auto_work.start(work_cmd, message.channel, deposit_cmd)
            auto_collect.start(collect_cmd, message.channel, deposit_cmd)

    elif message.content == "!stop":
        await message.delete()
        auto_work.stop()
        auto_collect.stop()


# Pull token from Replit Secrets
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("⚠️ TOKEN not found in Replit Secrets!")

client.run(TOKEN)
