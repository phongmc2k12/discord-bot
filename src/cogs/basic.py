"""
COGS: Basic Commands
Lệnh cơ bản: ping, hello, info, uptime, goodbye, invite, server
"""

import discord
from discord.ext import commands
from datetime import datetime
import platform
import psutil

class Basic(commands.Cog):
    """Lệnh cơ bản cho bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.now()
    
    def get_color(self, color_name='primary'):
        """Lấy màu từ config chung của bot"""
        color_hex = self.bot.config.get(f'colors.{color_name}', '#7289DA')
        return discord.Color(int(color_hex.replace('#', ''), 16))
    
    # ==========================================
    # 📌 LỆNH PING - Kiểm tra độ trễ
    # ==========================================
    @commands.command(name='ping')
    async def ping(self, ctx):
        """
        🏓 Kiểm tra độ trễ của bot
        
        Cách dùng: `!ping`
        """
        latency = round(self.bot.latency * 1000)
        
        if latency < 100:
            color = self.get_color('success')
            status = "🟢 Tốt"
        elif latency < 200:
            color = self.get_color('warning')
            status = "🟡 Trung bình"
        else:
            color = self.get_color('error')
            status = "🔴 Chậm"
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Độ trễ: `{latency}ms`",
            color=color
        )
        embed.add_field(name="📊 Trạng thái", value=status, inline=True)
        embed.add_field(name="🌐 WebSocket", value=f"`{latency}ms`", inline=True)
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}")
        
        await ctx.send(embed=embed)
    
    # ==========================================
    # 👋 LỆNH HELLO - Bot chào bạn
    # ==========================================
    @commands.command(name='hello', aliases=['hi', 'chao', 'xin_chao'])
    async def hello(self, ctx):
        """
        👋 Bot chào bạn
        
        Cách dùng: `!hello` hoặc `!hi` hoặc `!chao`
        """
        avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
        
        embed = discord.Embed(
            title="👋 Xin chào!",
            description=f"Chào bạn **{ctx.author.name}**! Rất vui được gặp bạn!",
            color=self.get_color('primary')
        )
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(
            name="📊 Thông tin",
            value=f"Bạn là thành viên thứ `{ctx.guild.member_count}` của server",
            inline=False
        )
        embed.set_footer(text=f"ID: {ctx.author.id}")
        embed.timestamp = datetime.now()
        
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🤖 LỆNH INFO - Thông tin bot
    # ==========================================
    @commands.command(name='info', aliases=['about'])
    async def info(self, ctx):
        """
        🤖 Hiển thị thông tin chi tiết về bot
        
        Cách dùng: `!info`
        """
        # Tính uptime
        delta = datetime.now() - self.start_time
        days, remainder = divmod(int(delta.total_seconds()), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            uptime = f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            uptime = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            uptime = f"{minutes}m {seconds}s"
        else:
            uptime = f"{seconds}s"
        
        # Lấy thông tin từ config chung
        bot_name = self.bot.config.get('bot.name', self.bot.user.name)
        bot_version = self.bot.config.get('bot.version', '1.0.0')
        
        embed = discord.Embed(
            title=f"🤖 Thông tin {bot_name}",
            color=self.get_color('primary'),
            timestamp=datetime.now()
        )
        
        # Thông tin cơ bản
        embed.add_field(name="📌 Tên", value=bot_name, inline=True)
        embed.add_field(name="🆔 ID", value=f"`{self.bot.user.id}`", inline=True)
        embed.add_field(name="📋 Version", value=f"`{bot_version}`", inline=True)
        embed.add_field(name="📌 Prefix", value=f"`{self.bot.command_prefix}`", inline=True)
        
        # Thông tin server
        embed.add_field(name="🏰 Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="👥 Users", value=str(len(self.bot.users)), inline=True)
        embed.add_field(name="⏱️ Uptime", value=uptime, inline=True)
        
        # Thông tin kỹ thuật
        embed.add_field(name="🐍 Python", value=platform.python_version(), inline=True)
        embed.add_field(name="📦 discord.py", value=discord.__version__, inline=True)
        
        # RAM usage
        try:
            ram_usage = psutil.Process().memory_info().rss / 1024 ** 2
            embed.add_field(name="💾 RAM", value=f"{ram_usage:.1f} MB", inline=True)
        except:
            embed.add_field(name="💾 RAM", value="N/A", inline=True)
        
        # CPU usage
        try:
            cpu_usage = psutil.cpu_percent()
            embed.add_field(name="⚡ CPU", value=f"{cpu_usage}%", inline=True)
        except:
            embed.add_field(name="⚡ CPU", value="N/A", inline=True)
        
        # Avatar và footer
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}")
        
        await ctx.send(embed=embed)
    
    # ==========================================
    # ⏰ LỆNH UPTIME - Thời gian hoạt động
    # ==========================================
    @commands.command(name='uptime')
    async def uptime(self, ctx):
        """
        ⏰ Hiển thị thời gian bot đã hoạt động
        
        Cách dùng: `!uptime`
        """
        delta = datetime.now() - self.start_time
        
        days, remainder = divmod(int(delta.total_seconds()), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        total_hours = int(delta.total_seconds() / 3600)
        bar_length = 20
        filled = min(bar_length, total_hours % 24)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        if days < 1:
            color = self.get_color('success')
            status = "🟢 Mới khởi động"
        elif days < 7:
            color = self.get_color('warning')
            status = "🟡 Đã hoạt động vài ngày"
        else:
            color = self.get_color('error')
            status = "🔴 Hoạt động lâu dài"
        
        embed = discord.Embed(
            title="⏰ Thời gian hoạt động",
            color=color,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📊 Chi tiết",
            value=(
                f"```\n"
                f"📅 Ngày   : {days}\n"
                f"⏰ Giờ    : {hours}\n"
                f"⏱️ Phút   : {minutes}\n"
                f"⏲️ Giây   : {seconds}\n"
                f"```"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📈 Trạng thái",
            value=f"`{bar}`\n`{filled}/{bar_length}`\n{status}",
            inline=False
        )
        
        embed.add_field(
            name="🔄 Lần khởi động",
            value=f"<t:{int(self.start_time.timestamp())}:R>",
            inline=False
        )
        
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}")
        
        await ctx.send(embed=embed)
    
    # ==========================================
    # 👋 LỆNH GOODBYE (Tạm biệt)
    # ==========================================
    @commands.command(name='goodbye', aliases=['bye', 'tam_biet'])
    async def goodbye(self, ctx):
        """
        👋 Bot tạm biệt bạn
        
        Cách dùng: `!goodbye`
        """
        embed = discord.Embed(
            title="👋 Tạm biệt!",
            description=f"Tạm biệt **{ctx.author.name}**! Hẹn gặp lại bạn sau!",
            color=self.get_color('primary')
        )
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.set_footer(text="Bot luôn sẵn sàng giúp đỡ bạn!")
        
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🔗 LỆNH INVITE - Link mời bot
    # ==========================================
    @commands.command(name='invite')
    async def invite(self, ctx):
        """
        🔗 Lấy link mời bot vào server
        
        Cách dùng: `!invite`
        """
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=discord.Permissions.all(),
            scopes=["bot", "applications.commands"]
        )
        
        embed = discord.Embed(
            title="🔗 Mời bot vào server của bạn!",
            description=f"[📥 Nhấn vào đây để mời bot]({invite_url})",
            color=self.get_color('success')
        )
        
        embed.add_field(
            name="📋 Hướng dẫn",
            value=(
                "1. Nhấn vào link trên\n"
                "2. Chọn server của bạn\n"
                "3. Cấp quyền cho bot\n"
                "4. Xác nhận và hoàn tất"
            ),
            inline=False
        )
        
        embed.set_footer(text="Bot được tạo với ❤️")
        
        await ctx.send(embed=embed)
    
    # ==========================================
    # 📊 LỆNH SERVER - Thông tin server
    # ==========================================
    @commands.command(name='server', aliases=['serverinfo', 'si'])
    async def server_info(self, ctx):
        """
        🏰 Hiển thị thông tin server
        
        Cách dùng: `!server`
        """
        guild = ctx.guild
        
        members = guild.members
        online = sum(1 for m in members if m.status != discord.Status.offline)
        idle = sum(1 for m in members if m.status == discord.Status.idle)
        dnd = sum(1 for m in members if m.status == discord.Status.dnd)
        offline = sum(1 for m in members if m.status == discord.Status.offline)
        bots = sum(1 for m in members if m.bot)
        humans = len(members) - bots
        
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed = discord.Embed(
            title=f"🏰 {guild.name}",
            color=self.get_color('primary'),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="🆔 ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="📅 Tạo lúc", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
        
        embed.add_field(
            name="👥 Thành viên",
            value=(
                f"Tổng: **{len(members)}**\n"
                f"🟢 Online: **{online}**\n"
                f"🟡 Idle: **{idle}**\n"
                f"🔴 DND: **{dnd}**\n"
                f"⚫ Offline: **{offline}**\n"
                f"🤖 Bot: **{bots}**\n"
                f"👤 Human: **{humans}**"
            ),
            inline=True
        )
        
        embed.add_field(
            name="📊 Kênh",
            value=(
                f"💬 Text: **{text_channels}**\n"
                f"🔊 Voice: **{voice_channels}**\n"
                f"📁 Categories: **{categories}**"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🚀 Boost",
            value=(
                f"Cấp: **{guild.premium_tier}**\n"
                f"Số: **{guild.premium_subscription_count}**"
            ),
            inline=True
        )
        
        embed.add_field(name="🎭 Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="😊 Emoji", value=f"Tổng: **{len(guild.emojis)}**", inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}")
        
        await ctx.send(embed=embed)

# ==========================================
# 📌 SETUP - Load cog
# ==========================================
async def setup(bot):
    await bot.add_cog(Basic(bot))