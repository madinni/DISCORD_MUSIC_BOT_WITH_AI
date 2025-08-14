import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from miku import chamada  # Função da IA
import asyncio
import yt_dlp

load_dotenv()
TOKEN = os.getenv("DISCORD_API_KEY") # Garanta que o nome no .env é DISCORD_TOKEN

# CORREÇÃO 1: FFMPEG_OPTIONS precisa de ser um dicionário (dict).
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}

# CORREÇÃO 2: Definido o prefixo do comando para "miku "
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="miku ", intents=intents)

@bot.event
async def on_ready():
    print("bot iniciado")

# O comando agora é "toque"
@bot.command(name="toque")
async def _toque(ctx: commands.Context, *, musica: str):
    canal_voz = ctx.author.voice.channel if ctx.author.voice else None
    if not canal_voz:
        return await ctx.send("Por favor, entre em um canal de voz primeiro! 🎶")
    
    voice_client = ctx.voice_client
    if not voice_client:
        voice_client = await canal_voz.connect()
    elif voice_client.is_playing():
        voice_client.stop()

    await ctx.send(f"Procurando por '{musica}'... 🔍")

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(f'ytsearch:{musica}', download=False)['entries'][0]
            url = info['url']
            title = info['title']
        except Exception:
            return await ctx.send("Desculpe, não consegui encontrar essa música. 😥")

    # --- LÓGICA PARA TOCAR A MÚSICA (A PARTE QUE FALTAVA) ---
    # CORREÇÃO 3: Adicionada a criação da fonte de áudio e o comando .play()
    source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
    voice_client.play(source)

    await ctx.send(f"**Tocando agora:** {title}")

    # --- CHAMADA PARA A IA (OPCIONAL) ---
    # Agora que a música está a tocar, a Miku pode dar a sua opinião.
    try:
        resposta_miku = await asyncio.to_thread(chamada, musica)
        # Envia a resposta da Miku como uma mensagem separada
        await ctx.send(resposta_miku)
    except Exception as e:
        # Se a IA falhar, não impede a música de tocar.
        print(f"Ocorreu um erro ao chamar a IA: {e}")


# CORREÇÃO 4: Removido o 'self' do comando, pois não está numa classe.
@bot.command(name="sair")
async def _sair(ctx: commands.Context):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("Até mais! 👋")
    else:
        await ctx.send("Eu não estou em um canal de voz.")

if TOKEN:
    bot.run(TOKEN)
else:
    print("Erro: Token do Discord não encontrado no arquivo .env")