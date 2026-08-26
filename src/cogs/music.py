"""
COGS: Music Commands
Lệnh phát nhạc: play, pause, resume, stop, skip, queue, nowplaying, volume, loop
Hỗ trợ: YouTube + SoundCloud (tự động làm sạch URL)
Fix: dùng chung bot.config (không đọc lại file), link hỏng khi thiếu webpage_url,
radio link youtu.be, format thời lượng > 1h, delete tin nhắn an toàn (tránh 404)
"""

import discord
from discord.ext import commands
import asyncio
import yt_dlp
import re
import os
import sys
import shutil
import random
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qs

# ==========================================
# TÌM FFMPEG TỰ ĐỘNG
# (không đọc config.json ở đây - Music.__init__ sẽ lấy đường dẫn
#  từ bot.config chung của bot, tránh đọc trùng lặp file config)
# ==========================================

def find_ffmpeg():
    """Tìm FFmpeg theo thứ tự ưu tiên"""
    env_ffmpeg = os.getenv('FFMPEG_PATH')
    if env_ffmpeg and Path(env_ffmpeg).exists():
        return env_ffmpeg

    system_ffmpeg = shutil.which('ffmpeg')
    if system_ffmpeg:
        return system_ffmpeg

    if sys.platform == 'win32':
        common_paths = [
            Path(r'C:\ffmpeg-bot\bin\ffmpeg.exe'),
            Path(r'C:\ffmpeg\bin\ffmpeg.exe'),
        ]
        for path in common_paths:
            if path.exists():
                return str(path)

    return 'ffmpeg'

FFMPEG_PATH = find_ffmpeg()
print(f"🎵 FFmpeg: {FFMPEG_PATH}")

# Cấu hình yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extractaudio': True,
    'audioformat': 'mp3',
    'prefer_ffmpeg': True,
    'extract_flat': False,
}

ffmpeg_options = {
    'options': '-vn -b:a 192k -ar 48000 -ac 2',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'executable': FFMPEG_PATH
}

if not os.path.exists('downloads'):
    os.makedirs('downloads')

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


def clean_url(url):
    """
    Làm sạch URL trước khi xử lý
    - Bỏ các tham số thừa (?ref=, &si=, &utm_source=, v.v.)
    - Giữ nguyên phần path chính
    """
    if not url.startswith('http'):
        return url

    parsed = urlparse(url)

    # Giữ lại các tham số cần thiết
    keep_params = []

    # YouTube cần 'v' và 'list'
    if 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc:
        params = parse_qs(parsed.query)
        keep_params = []
        if 'v' in params:
            keep_params.append(f"v={params['v'][0]}")
        if 'list' in params:
            keep_params.append(f"list={params['list'][0]}")

    # SoundCloud không cần tham số phụ
    elif 'soundcloud.com' in parsed.netloc or 'snd.sc' in parsed.netloc:
        keep_params = []

    # Tạo URL mới
    new_query = '&'.join(keep_params) if keep_params else ''

    clean = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        ''  # Bỏ fragment
    ))

    return clean


async def safe_delete(message):
    """Xóa tin nhắn an toàn - không crash nếu tin nhắn đã bị xóa (404)"""
    try:
        await message.delete()
    except (discord.NotFound, discord.Forbidden):
        pass
    except Exception:
        pass


def format_duration(seconds):
    """Format thời lượng: 65s -> 1:05, 4500s -> 1:15:00"""
    if not seconds or seconds <= 0:
        return None
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


class YTDLSource(discord.PCMVolumeTransformer):
    """Class xử lý audio"""

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.uploader = data.get('uploader')
        self.webpage_url = data.get('webpage_url')
        self.extractor = data.get('extractor', 'unknown')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()

        # Làm sạch URL trước khi xử lý
        url = clean_url(url)

        if not cls.is_supported_url(url) and not url.startswith('http'):
            url = f"ytsearch:{url}"

        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

            if data is None:
                raise ValueError("Không có dữ liệu")

            if 'entries' in data:
                entries = [e for e in data['entries'] if e is not None]
                if not entries:
                    raise ValueError("Không tìm thấy audio hợp lệ")
                data = entries[0]

            if not data or not data.get('url'):
                raise ValueError("Không lấy được URL audio")

            filename = data['url'] if stream else ytdl.prepare_filename(data)

            audio_source = discord.FFmpegPCMAudio(filename, **ffmpeg_options)
            return cls(audio_source, data=data)

        except Exception as e:
            print(f"❌ Lỗi khi tải nhạc: {e}")
            raise

    @staticmethod
    def is_youtube_url(url):
        youtube_patterns = [r'(youtube\.com)', r'(youtu\.be)', r'(m\.youtube\.com)']
        return any(re.search(pattern, url) for pattern in youtube_patterns)

    @staticmethod
    def is_soundcloud_url(url):
        soundcloud_patterns = [r'(soundcloud\.com)', r'(snd\.sc)']
        return any(re.search(pattern, url) for pattern in soundcloud_patterns)

    @staticmethod
    def is_supported_url(url):
        return YTDLSource.is_youtube_url(url) or YTDLSource.is_soundcloud_url(url)

    @staticmethod
    def is_playlist_url(url):
        if 'list=' in url or 'playlist' in url.lower():
            return True
        if '/sets/' in url:
            return True
        return False


class Music(commands.Cog):
    """Lệnh phát nhạc (YouTube + SoundCloud)"""

    def __init__(self, bot):
        self.bot = bot

        # Ưu tiên đường dẫn ffmpeg từ config chung của bot (nếu tồn tại thật)
        config_ffmpeg = bot.config.get('music.ffmpeg_path')
        if config_ffmpeg and Path(str(config_ffmpeg)).exists():
            ffmpeg_options['executable'] = str(config_ffmpeg)
            print(f"🎵 FFmpeg từ config: {config_ffmpeg}")

        self.queue = {}
        self.now_playing = {}
        self.volume = {}
        self.loop = {}
        self.playlist_loading = {}
        print("🎵 Music cog loaded! Hỗ trợ: YouTube + SoundCloud")

    def get_color(self, color_name='primary'):
        """Lấy màu từ config chung của bot"""
        color_hex = self.bot.config.get(f'colors.{color_name}', '#7289DA')
        return discord.Color(int(color_hex.replace('#', ''), 16))

    def get_default_volume(self):
        vol = self.bot.config.get('music.default_volume', 50)
        return vol / 100

    async def get_queue(self, guild_id):
        if guild_id not in self.queue:
            self.queue[guild_id] = []
        return self.queue[guild_id]

    async def get_voice_client(self, ctx):
        if not ctx.author.voice:
            await ctx.send("❌ Bạn phải ở trong voice channel để dùng lệnh này!")
            return None

        voice_channel = ctx.author.voice.channel
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if voice_client is None:
            voice_client = await voice_channel.connect()
            await ctx.send(f"✅ Đã kết nối vào **{voice_channel.name}**!")
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)
            await ctx.send(f"✅ Đã di chuyển vào **{voice_channel.name}**!")

        return voice_client

    async def search_artist_songs(self, artist_name, limit=10):
        videos = []
        try:
            search_query = f"ytsearch{limit}:{artist_name}"
            search_opts = {
                'extract_flat': True,
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
            }
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: ydl.extract_info(search_query, download=False)
                )
                if info and 'entries' in info:
                    for entry in info['entries']:
                        if entry and entry.get('id'):
                            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                            videos.append(video_url)
        except:
            pass
        return videos

    async def search_artist_album(self, artist_name, limit=20):
        videos = []
        try:
            search_queries = [
                f"ytsearch{limit}:{artist_name} full album",
                f"ytsearch{limit}:{artist_name} playlist",
            ]
            search_opts = {
                'extract_flat': True,
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
            }
            for sq in search_queries:
                try:
                    with yt_dlp.YoutubeDL(search_opts) as ydl:
                        info = await asyncio.get_event_loop().run_in_executor(
                            None, lambda: ydl.extract_info(sq, download=False)
                        )
                        if info and 'entries' in info:
                            for entry in info['entries']:
                                if entry and entry.get('id'):
                                    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                                    if video_url not in videos:
                                        videos.append(video_url)
                except:
                    continue
            if not videos:
                videos = await self.search_artist_songs(artist_name, limit)
        except:
            pass
        return videos

    async def extract_playlist_videos(self, playlist_url):
        videos = []
        try:
            playlist_url = clean_url(playlist_url)
            playlist_opts = {
                'extract_flat': True,
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
            }
            with yt_dlp.YoutubeDL(playlist_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: ydl.extract_info(playlist_url, download=False)
                )
                if info and 'entries' in info:
                    playlist_title = info.get('title', 'Playlist')
                    for entry in info['entries']:
                        if entry and entry.get('id'):
                            if entry.get('webpage_url'):
                                video_url = entry['webpage_url']
                            elif entry.get('url'):
                                video_url = entry['url']
                            else:
                                video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                            videos.append(video_url)
                    return videos, playlist_title
        except:
            pass
        return [], None

    # ==========================================
    # 🎵 LỆNH PLAY
    # ==========================================
    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx, *, query: str):
        """▶️ Phát nhạc từ YouTube hoặc SoundCloud"""

        voice_client = await self.get_voice_client(ctx)
        if not voice_client:
            return

        # Làm sạch URL nếu là link
        if query.startswith('http'):
            query = clean_url(query)

        # Xử lý radio URL (bắt cả watch?v=... lẫn youtu.be/...)
        if 'list=RD' in query or 'start_radio=1' in query:
            match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', query)
            if match:
                video_id = match.group(1)
                query = f"https://www.youtube.com/watch?v={video_id}"

        # Kiểm tra URL
        if query.startswith('http'):
            if YTDLSource.is_playlist_url(query):
                await self._handle_playlist(ctx, query, voice_client)
                return
            if not YTDLSource.is_supported_url(query):
                await ctx.send("❌ Chỉ hỗ trợ link YouTube và SoundCloud!")
                return

        # Tìm kiếm
        if not query.startswith('http'):
            embed = discord.Embed(
                title="🔍 Tìm kiếm",
                description=f"Bạn muốn tìm gì với: **{query}**?",
                color=self.get_color('primary')
            )
            embed.add_field(name="1️⃣", value="Phát 1 bài (tìm nhanh)", inline=False)
            embed.add_field(name="2️⃣", value="Phát 5 bài liên tiếp", inline=False)
            embed.add_field(name="3️⃣", value="Phát 10 bài liên tiếp", inline=False)
            embed.set_footer(text="React để chọn (30 giây)")

            msg = await ctx.send(embed=embed)
            reactions = ['1️⃣', '2️⃣', '3️⃣']
            for reaction in reactions:
                await msg.add_reaction(reaction)

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in reactions and reaction.message.id == msg.id

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)

                if str(reaction.emoji) == '1️⃣':
                    limit = 1
                elif str(reaction.emoji) == '2️⃣':
                    limit = 5
                else:
                    limit = 10

                await safe_delete(msg)
                loading_msg = await ctx.send(f"🔄 Đang tìm {limit} bài cho: **{query}**...")
                videos = await self.search_artist_songs(query, limit)

                if not videos:
                    await safe_delete(loading_msg)
                    await ctx.send("❌ Không tìm thấy bài hát nào!")
                    return

                queue = await self.get_queue(ctx.guild.id)
                queue.extend(videos)

                await safe_delete(loading_msg)
                embed = discord.Embed(
                    title="✅ Đã thêm vào hàng chờ",
                    description=f"Tìm thấy `{len(videos)}` bài cho: **{query}**",
                    color=self.get_color('success')
                )
                embed.set_footer(text=f"Tổng queue: {len(queue)} bài")
                await ctx.send(embed=embed)

                if not voice_client.is_playing():
                    await self._play_next(ctx, voice_client)
                return

            except asyncio.TimeoutError:
                await safe_delete(msg)
                await ctx.send("⏰ Hết thời gian chọn!")
                return

        # Phát 1 bài
        queue = await self.get_queue(ctx.guild.id)
        queue.append(query)

        if voice_client.is_playing():
            embed = discord.Embed(
                title="✅ Đã thêm vào hàng chờ",
                description=f"**{query}**",
                color=self.get_color('primary')
            )
            embed.set_footer(text=f"Vị trí #{len(queue)} trong hàng chờ")
            await ctx.send(embed=embed)
            return

        await self._play_next(ctx, voice_client)

    # ==========================================
    # 🎵 LỆNH PLAYALBUM
    # ==========================================
    @commands.command(name='playalbum', aliases=['album', 'pa'])
    async def play_album(self, ctx, *, artist_name: str):
        """🎵 Phát full album của ca sĩ"""

        voice_client = await self.get_voice_client(ctx)
        if not voice_client:
            return

        embed = discord.Embed(
            title="🎵 Phát Full Album",
            description=f"Bạn muốn phát bao nhiêu bài của: **{artist_name}**?",
            color=self.get_color('primary')
        )
        embed.add_field(name="1️⃣", value="10 bài", inline=False)
        embed.add_field(name="2️⃣", value="20 bài", inline=False)
        embed.add_field(name="3️⃣", value="30 bài", inline=False)
        embed.set_footer(text="React để chọn (30 giây)")

        msg = await ctx.send(embed=embed)
        reactions = ['1️⃣', '2️⃣', '3️⃣']
        for reaction in reactions:
            await msg.add_reaction(reaction)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in reactions and reaction.message.id == msg.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)

            if str(reaction.emoji) == '1️⃣':
                limit = 10
            elif str(reaction.emoji) == '2️⃣':
                limit = 20
            else:
                limit = 30

            await safe_delete(msg)
            loading_msg = await ctx.send(f"🔄 Đang tìm full album của: **{artist_name}**...")
            videos = await self.search_artist_album(artist_name, limit)

            if not videos:
                await safe_delete(loading_msg)
                await ctx.send(f"❌ Không tìm thấy bài hát nào của: **{artist_name}**")
                return

            queue = await self.get_queue(ctx.guild.id)
            queue.extend(videos)

            await safe_delete(loading_msg)
            embed = discord.Embed(
                title="✅ Đã thêm album vào hàng chờ",
                description=f"Tìm thấy `{len(videos)}` bài của: **{artist_name}**",
                color=self.get_color('success')
            )
            embed.set_footer(text="Bot sẽ tự động phát liên tục!")
            await ctx.send(embed=embed)

            if not voice_client.is_playing():
                await self._play_next(ctx, voice_client)

        except asyncio.TimeoutError:
            await safe_delete(msg)
            await ctx.send(f"⏰ Hết thời gian chọn!")

    async def _handle_playlist(self, ctx, playlist_url, voice_client):
        """Xử lý thêm playlist vào queue"""

        if self.playlist_loading.get(ctx.guild.id, False):
            await ctx.send("⏳ Đang tải playlist khác, vui lòng đợi...")
            return

        self.playlist_loading[ctx.guild.id] = True
        loading_msg = await ctx.send("🔄 Đang tải playlist...")

        try:
            videos, playlist_title = await self.extract_playlist_videos(playlist_url)

            if not videos:
                await safe_delete(loading_msg)
                await ctx.send("❌ Không thể tải playlist!")
                return

            queue = await self.get_queue(ctx.guild.id)
            queue.extend(videos)

            embed = discord.Embed(
                title="✅ Đã thêm playlist",
                color=self.get_color('success')
            )
            embed.add_field(name="📋 Tên", value=(playlist_title or "Unknown")[:256], inline=False)
            embed.add_field(name="🎵 Số bài", value=f"`{len(videos)}` bài", inline=True)
            embed.add_field(name="📊 Tổng queue", value=f"`{len(queue)}` bài", inline=True)

            await safe_delete(loading_msg)
            await ctx.send(embed=embed)

            if not voice_client.is_playing():
                await self._play_next(ctx, voice_client)

        except Exception as e:
            await safe_delete(loading_msg)
            await ctx.send(f"❌ Lỗi: {str(e)}")
        finally:
            self.playlist_loading[ctx.guild.id] = False

    async def _play_next(self, ctx, voice_client):
        queue = await self.get_queue(ctx.guild.id)

        if not queue:
            return

        max_attempts = 5
        attempts = 0

        while attempts < max_attempts and queue:
            query = queue.pop(0)
            attempts += 1

            try:
                loading_msg = await ctx.send(f"🔄 Đang tải: **{query[:80]}**...")

                player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)

                if not player.title:
                    await safe_delete(loading_msg)
                    await ctx.send(f"⚠️ Bỏ qua bài lỗi")
                    continue

                # Fallback link: tránh tạo markdown [tên](None) khi thiếu webpage_url
                link = player.webpage_url or player.url or query

                self.now_playing[ctx.guild.id] = {
                    'title': player.title,
                    'url': query,
                    'webpage_url': player.webpage_url,
                    'duration': player.duration,
                    'thumbnail': player.thumbnail,
                    'uploader': player.uploader,
                    'requested_by': ctx.author,
                    'extractor': player.extractor
                }

                vol = self.volume.get(ctx.guild.id, self.get_default_volume())
                player.volume = vol

                await safe_delete(loading_msg)

                if 'soundcloud' in player.extractor.lower():
                    source_icon = "🎧 SoundCloud"
                else:
                    source_icon = "▶️ YouTube"

                embed = discord.Embed(
                    title=f"{source_icon} - Đang phát",
                    description=f"**[{player.title}]({link})**",
                    color=self.get_color('success')
                )

                if player.thumbnail:
                    embed.set_thumbnail(url=player.thumbnail)

                duration_text = format_duration(player.duration)
                if duration_text:
                    embed.add_field(name="⏱️ Thời lượng", value=duration_text, inline=True)

                embed.add_field(name="👤 Yêu cầu", value=ctx.author.mention, inline=True)

                if player.uploader:
                    embed.add_field(name="📢 Kênh", value=player.uploader, inline=True)

                if queue:
                    embed.add_field(name="📋 Còn lại", value=f"`{len(queue)}` bài", inline=True)

                await ctx.send(embed=embed)

                def after_play(error):
                    if error:
                        print(f"❌ Lỗi: {error}")
                        asyncio.run_coroutine_threadsafe(self._play_next(ctx, voice_client), self.bot.loop)
                    else:
                        asyncio.run_coroutine_threadsafe(self._after_play(ctx, voice_client), self.bot.loop)

                voice_client.play(player, after=after_play)
                print(f"✅ Đang phát: {player.title}")
                return

            except Exception as e:
                await safe_delete(loading_msg)
                print(f"❌ Lỗi: {e}")
                await ctx.send(f"⚠️ Bỏ qua bài lỗi")
                continue

        if not queue:
            await ctx.send("✅ Đã phát hết các bài!")
        else:
            await ctx.send(f"⚠️ Quá nhiều bài lỗi liên tiếp, dừng phát! (còn `{len(queue)}` bài trong queue)")

    async def _after_play(self, ctx, voice_client):
        if self.loop.get(ctx.guild.id, False):
            if ctx.guild.id in self.now_playing:
                queue = await self.get_queue(ctx.guild.id)
                queue.insert(0, self.now_playing[ctx.guild.id]['url'])
        await self._play_next(ctx, voice_client)

    # ==========================================
    # PAUSE / RESUME / STOP / SKIP
    # ==========================================
    @commands.command(name='pause')
    async def pause(self, ctx):
        """⏸️ Tạm dừng nhạc"""
        voice_client = ctx.voice_client
        if not voice_client or not voice_client.is_playing():
            await ctx.send("❌ Không có nhạc đang phát!")
            return
        voice_client.pause()
        await ctx.send("⏸️ Đã tạm dừng!")

    @commands.command(name='resume')
    async def resume(self, ctx):
        """▶️ Tiếp tục phát nhạc"""
        voice_client = ctx.voice_client
        if not voice_client or not voice_client.is_paused():
            await ctx.send("❌ Nhạc không bị tạm dừng!")
            return
        voice_client.resume()
        await ctx.send("▶️ Đã tiếp tục!")

    @commands.command(name='stop')
    async def stop(self, ctx):
        """⏹️ Dừng nhạc và xóa hàng chờ"""
        voice_client = ctx.voice_client
        if not voice_client:
            await ctx.send("❌ Bot không ở trong voice channel!")
            return
        if ctx.guild.id in self.queue:
            self.queue[ctx.guild.id] = []
        voice_client.stop()
        await ctx.send("⏹️ Đã dừng!")

    @commands.command(name='skip')
    async def skip(self, ctx):
        """⏭️ Skip bài đang phát"""
        voice_client = ctx.voice_client
        if not voice_client or not voice_client.is_playing():
            await ctx.send("❌ Không có nhạc đang phát!")
            return
        voice_client.stop()
        await ctx.send("⏭️ Đã skip!")

    # ==========================================
    # QUEUE / SHUFFLE / REMOVE / CLEAR
    # ==========================================
    @commands.command(name='queue', aliases=['q'])
    async def queue_list(self, ctx):
        """📋 Xem hàng chờ"""
        queue = await self.get_queue(ctx.guild.id)
        if not queue:
            await ctx.send("📋 Hàng chờ trống!")
            return
        embed = discord.Embed(title="📋 Hàng chờ", color=self.get_color('primary'))
        song_list = ""
        for i, song in enumerate(queue[:10], 1):
            display_name = song if len(song) <= 50 else song[:47] + "..."
            song_list += f"`{i}.` {display_name}\n"
        if len(queue) > 10:
            song_list += f"... và {len(queue) - 10} bài khác"
        embed.add_field(name=f"📌 {len(queue)} bài", value=song_list[:1024], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def shuffle_queue(self, ctx):
        """🔀 Trộn hàng chờ"""
        queue = await self.get_queue(ctx.guild.id)
        if not queue:
            await ctx.send("❌ Hàng chờ trống!")
            return
        random.shuffle(queue)
        await ctx.send(f"🔀 Đã trộn `{len(queue)}` bài!")

    @commands.command(name='remove')
    async def remove_song(self, ctx, position: int):
        """🗑️ Xóa bài theo vị trí trong queue"""
        queue = await self.get_queue(ctx.guild.id)
        if not queue:
            await ctx.send("❌ Hàng chờ trống!")
            return
        if position < 1 or position > len(queue):
            await ctx.send(f"❌ Vị trí phải từ 1 đến {len(queue)}!")
            return
        removed = queue.pop(position - 1)
        await ctx.send(f"🗑️ Đã xóa: `{removed[:60]}`")

    @commands.command(name='clearqueue', aliases=['cq'])
    async def clear_queue(self, ctx):
        """🧹 Xóa sạch hàng chờ"""
        queue = await self.get_queue(ctx.guild.id)
        if not queue:
            await ctx.send("❌ Hàng chờ trống!")
            return
        self.queue[ctx.guild.id] = []
        await ctx.send("🧹 Đã xóa hàng chờ!")

    # ==========================================
    # LOOP / NP / VOLUME / LEAVE
    # ==========================================
    @commands.command(name='loop')
    async def loop_toggle(self, ctx):
        """🔁 Bật/tắt lặp lại bài hiện tại"""
        current = self.loop.get(ctx.guild.id, False)
        self.loop[ctx.guild.id] = not current
        status = "bật" if self.loop[ctx.guild.id] else "tắt"
        await ctx.send(f"🔁 Đã {status} lặp lại!")

    @commands.command(name='nowplaying', aliases=['np'])
    async def now_playing_cmd(self, ctx):
        """📊 Xem bài đang phát"""
        song = self.now_playing.get(ctx.guild.id)
        voice_client = ctx.voice_client
        if not song or not voice_client or not voice_client.is_playing():
            await ctx.send("📊 Không có bài nào đang phát!")
            return
        embed = discord.Embed(
            title="📊 Đang phát",
            description=f"**[{song['title']}]({song.get('webpage_url') or song['url']})**",
            color=self.get_color('success')
        )
        if song.get('thumbnail'):
            embed.set_thumbnail(url=song['thumbnail'])
        duration_text = format_duration(song.get('duration'))
        if duration_text:
            embed.add_field(name="⏱️ Thời lượng", value=duration_text, inline=True)
        if song.get('uploader'):
            embed.add_field(name="📢 Kênh", value=song['uploader'], inline=True)
        queue = await self.get_queue(ctx.guild.id)
        if queue:
            embed.add_field(name="📋 Còn lại", value=f"`{len(queue)}` bài", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name='volume', aliases=['vol'])
    async def volume_cmd(self, ctx, volume: int = None):
        """🔈 Xem/chỉnh âm lượng (0-100)"""
        voice_client = ctx.voice_client
        if not voice_client:
            await ctx.send("❌ Bot không ở trong voice channel!")
            return
        if volume is None:
            current_vol = self.volume.get(ctx.guild.id, self.get_default_volume()) * 100
            await ctx.send(f"🔈 Âm lượng: `{int(current_vol)}%`")
            return
        if volume < 0 or volume > 100:
            await ctx.send("❌ Âm lượng phải từ 0 đến 100!")
            return
        vol = volume / 100
        self.volume[ctx.guild.id] = vol
        if voice_client.source:
            voice_client.source.volume = vol
        await ctx.send(f"🔈 Đã chỉnh: `{volume}%`")

    @commands.command(name='leave', aliases=['disconnect'])
    async def leave(self, ctx):
        """📤 Rời voice channel"""
        voice_client = ctx.voice_client
        if not voice_client:
            await ctx.send("❌ Bot không ở trong voice channel!")
            return
        if ctx.guild.id in self.queue:
            self.queue[ctx.guild.id] = []
        self.now_playing.pop(ctx.guild.id, None)
        self.loop.pop(ctx.guild.id, None)
        await voice_client.disconnect()
        await ctx.send("📤 Đã rời voice channel!")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id == self.bot.user.id and before.channel and not after.channel:
            gid = before.channel.guild.id
            if gid in self.queue:
                self.queue[gid] = []
            self.now_playing.pop(gid, None)

async def setup(bot):
    await bot.add_cog(Music(bot))
