# type:ignore
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from miku import chamada_toque, chamada_conversa
import asyncio
import yt_dlp


def hatsune_miku():
	load_dotenv()
	TOKEN = os.getenv("DISCORD_API_KEY")

	FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
	YDL_OPTIONS = {"format": "bestaudio/best", "noplaylist": True}
	queue = []
	ytdl = yt_dlp.YoutubeDL(YDL_OPTIONS)

	intents = discord.Intents.all()
	bot = commands.Bot("miku ", intents=intents)

	def play_next(ctx):
		if queue:
			voice_client = ctx.voice_client
			if not voice_client:
				return
			
			info_musica = queue.pop(0)
			url_musica = info_musica['url']
			source = discord.FFmpegPCMAudio(url_musica, **FFMPEG_OPTIONS)

			voice_client.play(source, after=lambda e: play_next(ctx))

			embed = discord.Embed(title="🎤 Tocando Agora", description=info_musica['title'], color=discord.Color.green())
			bot.loop.create_task(ctx.send(embed=embed))

		else:
			embed = discord.Embed(description="A fila de músicas terminou! 👋", color=discord.Color.blue())
			bot.loop.create_task(ctx.send(embed=embed))


	@bot.event
	async def on_ready():
		print("bot iniciado")

	@bot.event
	async def on_message(message: discord.Message):
		if message.author == bot.user:
			return

		await bot.process_commands(message)
		
		ctx = await bot.get_context(message)

		if not ctx.valid and 'miku' in message.content.lower():
			print(f"Miku foi mencionada por {message.author.name} (não é um comando). Gerando resposta...")
			
			async with message.channel.typing():
				try:
					resposta_ia = await asyncio.to_thread(chamada_conversa, message.content)
					await message.reply(f'{resposta_ia}')
				except Exception as e:
					print(f"Ocorreu um erro ao gerar a resposta da IA: {e}")
					await message.reply("Desculpe, não consegui pensar em uma resposta agora. 😥")

	@bot.command(name="toque")
	async def toque(ctx:commands.Context, *, musica:str):

		if not ctx.author.voice:
			return await ctx.send("Você precisa estar em um canal de voz para eu poder cantar! 🎤")
		
		await ctx.send(f"Preparando tudo para tocar '{musica}'... Um momento! 🎵")


		print("DIAGNÓSTICO: Buscando música no yt-dlp...")
		try:
			with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
				info = ydl.extract_info(f"ytsearch:{musica}", download=False)['entries'][0]
		except Exception as e:
				print(f"Erro no yt-dlp: {e}")
				return await ctx.send("Desculpe, não consegui encontrar essa música. 😥")
		print(f"DIAGNÓSTICO: Música encontrada: {info['title']}")


		print("DIAGNÓSTICO: Chamando a IA (Groq)...")
		try:
			resposta_ia = await asyncio.to_thread(chamada_toque, musica)
		except Exception as e:
			print(f"Ocorreu um erro ao gerar a resposta da IA: {e}")
			resposta_ia = "Não consegui pensar em uma resposta agora, mas aqui está sua música! 😥"
			print("DIAGNÓSTICO: IA respondeu.")


		print("DIAGNÓSTICO: Conectando ao canal de voz...")
		channel = ctx.author.voice.channel
		voice_client = ctx.voice_client

		if not voice_client:
			voice_client = await channel.connect()
		elif voice_client.channel != channel:
			await voice_client.move_to(channel)
			print("DIAGNÓSTICO: Conectado com sucesso.")

		queue.append(info)
		await ctx.send(f"**Adicionado à fila:** {info['title']}")

		if not voice_client.is_playing():
			play_next(ctx)

		await ctx.reply(resposta_ia)

	@bot.command(name="fila")
	async def fila(ctx: commands.Context):
		if not queue:
			embed_vazia = discord.Embed(
				description="A fila de músicas está vazia! Adicione uma com `miku toque <nome da música>`.",
				color=discord.Color.orange()
			)
			await ctx.send(embed=embed_vazia)
			return

		lista_musicas = ""
		for idx, musica in enumerate(queue):
			lista_musicas += f"**{idx + 1}.** {musica['title']}\n"


		embed_fila = discord.Embed(
			title="🎶 Fila de Músicas",
			description=lista_musicas,
			color=discord.Color.blue()
		)
		embed_fila.set_footer(text=f"{len(queue)} músicas na fila.")

		await ctx.send(embed=embed_fila)


	@bot.command(name="sair")
	async def sair(ctx: commands.Context):
		channel = ctx.author.voice.channel
		voice_client = ctx.voice_client

		if voice_client.channel == channel:
			await ctx.voice_client.disconnect()
		
		else:
			await ctx.replay("Não estou nessa call")


	bot.run(f'{TOKEN}') 