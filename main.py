import discord
import requests
import json
import os
from dotenv import load_dotenv
import openai
import re
from typing import Literal

#https://weather.tsukumijima.net/

testmsg = ""

Bot_Token = os.getenv("DISCORD_BOT_TOKEN")
if Bot_Token == None:
  load_dotenv()
  Bot_Token = os.getenv("DISCORD_BOT_TOKEN")
else:
  from server import keep_alive
  keep_alive()

openai.api_key = os.getenv("OPENAI_API_KEY")
Guild_Id = os.getenv("GUILD_ID")
int_Guild_Id = int(Guild_Id)

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)

tree = discord.app_commands.CommandTree(client)

tokyo_tenki_url = "https://weather.tsukumijima.net/api/forecast/city/130010"
Daily_dani_url = "https://anime.dmkt-sp.jp/animestore/rest/WS000103?rankingType=01"
Weekly_dani_url = "https://anime.dmkt-sp.jp/animestore/rest/WS000103?rankingType=02"

gpt_log = ""


@tree.command(name="help", description="コマンドリストが見れます")
@discord.app_commands.guilds(int_Guild_Id)
async def help(interaction: discord.Interaction):
  sendmessage = "```"
  sendmessage += "/help：コマンドリストを返す\n"
  sendmessage += "/tenki：東京の天気や降水確率を明後日まで取得できる(未対応\"$tenki\"使ってね)\n"
  sendmessage += "/animeranking：dアニメストアランキング\n"
  sendmessage += "/chatgpt：チャットGPTと話そう"
  sendmessage += "```"
  await interaction.response.send_message(sendmessage)


message_log_withgpt = []


@tree.command(name="chatgpt", description="chatGPTと話す")
@discord.app_commands.describe(system_text="事前情報", input_text="本文")
@discord.app_commands.guilds(int_Guild_Id)
async def GPT(interaction: discord.Interaction,
              input_text: str,
              system_text: str = ""):
  global message_log_withgpt
  print(message_log_withgpt)

  if system_text != "" and len(message_log_withgpt) == 0:
    system = {"role": "system", "content": system_text}
    message_log_withgpt.append(system)

  input = {"role": "user", "content": input_text}
  message_log_withgpt.append(input)

  await interaction.response.defer()

  gpt_text = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                          messages=message_log_withgpt)
  gpt_log = {
    "role": "assistant",
    "content": gpt_text["choices"][0]["message"]["content"]
  }

  print(gpt_log)
  print(type(gpt_log))

  message_log_withgpt.append(gpt_log)

  print(message_log_withgpt)

  sendmessage = "```"
  sendmessage += "事前情報:" + system_text + "\n"
  sendmessage += "入力:" + "\n" + input_text + "\n\n"
  sendmessage += "出力:" + gpt_text["choices"][0]["message"]["content"]
  sendmessage += "```"

  while (gpt_text != None):
    await interaction.followup.send(sendmessage)
    await interaction.followup.send(message_log_withgpt)
    break


@tree.command(name="clearmemory", description="chatGPTの記憶を消去")
@discord.app_commands.guilds(int_Guild_Id)
async def clearmemory(interaction: discord.Interaction):
  global message_log_withgpt
  message_log_withgpt.clear()
  await interaction.response.send_message("記憶を失いました")


@tree.command(name="animeranking", description="Dアニメストアのランキングを取得")
@discord.app_commands.describe(duration="daily or weekly", top="何位まで、デフォルトは10")
@discord.app_commands.guilds(int_Guild_Id)
async def anime_ranking(interaction: discord.Interaction,
                        duration: Literal["daily", "weekly"],
                        top: int = 10):
  sendmessage = "```"
  sendmessage += duration + " TOP" + str(top) + "(Dアニメストア)\n\n"
  sendmessage += get_Dani_ranking(count=top, duration=duration)
  sendmessage += "\n```"

  await interaction.response.send_message(sendmessage)


@client.event
async def on_ready():
  print("こんにちは")
  await tree.sync(guild=discord.Object(int_Guild_Id))


@client.event
async def on_message(message):

  if message.content.startswith("$help"):
    sendmessage = "```"
    sendmessage += "$help：コマンドリストを返す\n"
    sendmessage += "$tenki：東京の天気や降水確率を明後日まで取得できる\n"
    sendmessage += "$daniD：今日のdアニメストアランキング\n"
    sendmessage += "$daniW：今週のdアニメストアランキング\n"
    sendmessage += "```"
    await message.channel.send(sendmessage)

  if message.content.startswith("$GPT"):
    str_message = message.content
    pattern = f"\$GPT[ \"\*'](.*)"
    inputmessage = re.findall(pattern, str_message)
    inputmessage = inputmessage[0]

    response = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                            messages=[{
                                              "role":
                                              "system",
                                              "content":
                                              "あなたはdiscordで使われるチャットボットです。"
                                            }, {
                                              "role": "user",
                                              "content": inputmessage
                                            }])

    sendmessage = "```"
    sendmessage += response["choices"][0]["message"]["content"]
    sendmessage += "```"

    await message.channel.send(sendmessage)

  if message.content.startswith("$tenki"):
    okd = await message.channel.send(
      "```おはよう！いつの天気が知りたいかをリアクションで教えて\n　　今日：1\n　　明日：2\n　明後日：3 ```")
    await okd.add_reaction("1️⃣")
    await okd.add_reaction("2️⃣")
    await okd.add_reaction("3️⃣")

  if message.content.startswith("$daniD"):
    sendmessage = "```"
    sendmessage += "デイリーランキングTOP10(Dアニメストア)\n\n"
    sendmessage += get_Dani_ranking()
    sendmessage += "\n"
    sendmessage += "さらに知りたい時は👌"
    sendmessage += "```"

    msg = await message.channel.send(sendmessage)
    await msg.add_reaction("👌")

  if message.content.startswith("$daniW"):
    sendmessage = "```"
    sendmessage += "ウィークリーランキングTOP10(Dアニメストア)\n\n"
    sendmessage += get_Dani_ranking(Weekly=True)
    sendmessage += "\n"
    sendmessage += "さらに知りたい時は👌"
    sendmessage += "```"

    msg = await message.channel.send(sendmessage)
    await msg.add_reaction("👌")


@client.event
async def on_reaction_add(reaction, user):
  if user.bot:
    return

  if reaction.message.content.startswith("```デイリーランキング"):
    if reaction.emoji == "👌":
      sendmessage = "```"
      sendmessage += "デイリーランキングTOP10(Dアニメストア)\n\n"
      sendmessage += get_Dani_ranking(count=30)
      sendmessage += "```"

      await reaction.message.channel.send(sendmessage)

  if reaction.message.content.startswith("```ウィークリーランキング"):
    if reaction.emoji == "👌":
      sendmessage = "```"
      sendmessage += "ウィークリーランキングTOP10(Dアニメストア)\n\n"
      sendmessage += get_Dani_ranking(count=30, Weekly=True)
      sendmessage += "```"

      await reaction.message.channel.send(sendmessage)

  if reaction.message.content.startswith("```おはよう！いつの"):
    if reaction.emoji == "1️⃣":
      i = 0
    elif reaction.emoji == "2️⃣":
      i = 1
    elif reaction.emoji == "3️⃣":
      i = 2
    else:
      return

    response = requests.get(tokyo_tenki_url).json()
    title = response["title"]
    date = response["forecasts"][i]["date"]
    date = date[-5:]
    dateLabel = response["forecasts"][i]["dateLabel"]
    weather = response["forecasts"][i]["telop"]
    min_temperature = response["forecasts"][i]["temperature"]["min"]["celsius"]
    max_temperature = response["forecasts"][i]["temperature"]["max"]["celsius"]
    T00_06__chanceofRain = response["forecasts"][i]["chanceOfRain"]["T00_06"]
    T06_12__chanceofRain = response["forecasts"][i]["chanceOfRain"]["T06_12"]
    T12_18__chanceofRain = response["forecasts"][i]["chanceOfRain"]["T12_18"]
    T18_24__chanceofRain = response["forecasts"][i]["chanceOfRain"]["T18_24"]

    sendMessage = "```"
    sendMessage += title + "\n"
    sendMessage += dateLabel + "(" + date + ")\n"
    sendMessage += "　天気：" + weather + "\n"
    sendMessage += "　気温：\n"
    sendMessage += "　　　最低　" + min_temperature + "℃\n"
    sendMessage += "　　　最高　" + max_temperature + "℃\n"
    sendMessage += "　降水確率：\n"
    sendMessage += "　　　早朝　" + T00_06__chanceofRain + "\n"
    sendMessage += "　　　午前　" + T06_12__chanceofRain + "\n"
    sendMessage += "　　　午後　" + T12_18__chanceofRain + "\n"
    sendMessage += "　　　夜　　" + T18_24__chanceofRain
    sendMessage += "```"

    await reaction.message.channel.send(sendMessage)


def get_Dani_ranking(count: int = 10, duration="daily"):
  if duration == "daily":
    response = requests.get(Daily_dani_url)
  else:
    response = requests.get(Weekly_dani_url)

  ranking_json = json.loads(response.text)
  ranking = ""

  for i in range(count):
    ranking_title = ranking_json["data"]["workList"][i]["workInfo"][
      "workTitle"]
    ranking_favoritecount = ranking_json["data"]["workList"][i]["workInfo"][
      "favoriteCount"]
    ranking += str(i + 1) + "." + ranking_title + "　" + str(
      ranking_favoritecount) + "いいね\n"

  print(ranking)
  return ranking


client.run(Bot_Token)
