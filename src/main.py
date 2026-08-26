"""
Discord Bot - Main Entry Point
Tác giả: Builder_Phong
Version: 2.0.0
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Thêm src vào path
sys.path.insert(0, str(Path(__file__).parent))

# Import thư viện
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Import utils
from utils.logger import setup_logger
from utils.database import Database
from utils.config import Config

# Load biến môi trường
load_dotenv('config/.env')

# ===== CẤU HÌNH =====
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('BOT_PREFIX', '!')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Load config.json
config = Config()
bot_name = config.get('bot.name', 'Bot')
bot_version = config.get('bot.version', '1.0.0')
bot_activity = config.get('bot.activity', f'{PREFIX}help')
bot_activity_type = config.get('bot.activity_type', 'playing')

# Setup logger
logger = setup_logger(LOG_LEVEL)

# ===== KHỞI TẠO BOT =====
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None,
    description=bot_name
)

# Chia sẻ config chung cho tất cả cogs (dùng bot.config thay vì đọc lại file)
bot.config = config

# ===== LOAD EXTENSIONS =====
async def load_extensions():
    """Load tất cả cogs từ thư mục cogs dựa trên config"""
    cogs_dir = Path(__file__).parent / 'cogs'
    
    features = config.get('features', {})
    
    loaded_cogs = []
    failed_cogs = []
    
    # Map cog name với feature
    feature_map = {
        'music': 'music',
        'economy': 'economy',
        'moderation': 'auto_moderation',
        'welcome': 'welcome_message',
        'admin': None,
        'basic': None,
        'fun': None,
    }
    
    for file in cogs_dir.glob('*.py'):
        if file.name == '__init__.py':
            continue
        
        cog_name = file.stem
        feature_key = feature_map.get(cog_name)
        
        # Nếu feature check và feature tắt thì skip
        if feature_key and not features.get(feature_key, True):
            logger.info(f"⏭️ Skipped cog: {cog_name} (feature disabled)")
            continue
        
        try:
            extension_name = f'cogs.{cog_name}'
            await bot.load_extension(extension_name)
            loaded_cogs.append(cog_name)
            logger.info(f"✅ Loaded cog: {cog_name}")
        except Exception as e:
            failed_cogs.append(cog_name)
            logger.error(f"❌ Failed to load {cog_name}: {e}")
    
    return loaded_cogs, failed_cogs

# ===== TẠO HELP COMMAND =====
class CustomHelp(commands.HelpCommand):
    """
    Help command tùy chỉnh - mô tả hiển thị ngay bên cạnh lệnh
    LƯU Ý: discord.py 2.x KHÔNG có thuộc tính self.bot trong HelpCommand,
    phải lấy bot qua self.context.bot (fix lỗi AttributeError 'no attribute bot')
    """

    COG_ICONS = {
        'Basic': '🧩',
        'Fun': '🎉',
        'Economy': '💰',
        'Moderation': '🛡️',
        'Admin': '⚙️',
        'Music': '🎵',
    }

    @property
    def bot_ref(self):
        """Bot hiện tại (lấy từ context thay vì self.bot không tồn tại)"""
        return self.context.bot

    def get_color(self, color_name='primary'):
        color_hex = self.bot_ref.config.get(f'colors.{color_name}', '#7289DA')
        return discord.Color(int(color_hex.replace('#', ''), 16))

    @staticmethod
    def short_desc(command, limit=45):
        """Lấy dòng đầu tiên của help làm mô tả ngắn"""
        doc = (command.help or 'Không có mô tả').strip().split('\n')[0].strip()
        if len(doc) > limit:
            doc = doc[:limit - 1] + '…'
        return doc

    @staticmethod
    def aliases_text(command):
        if command.aliases:
            return ' *(alias: ' + ', '.join(f'`{a}`' for a in command.aliases) + ')*'
        return ''

    async def send_bot_help(self, mapping):
        """Hiển thị tất cả lệnh kèm mô tả bên cạnh"""
        b = self.bot_ref
        total = sum(
            1 for cog, cmds in mapping.items() for cmd in cmds if not cmd.hidden
        )

        embed = discord.Embed(
            title=f"📚 HƯỚNG DẪN SỬ DỤNG — {bot_name}",
            description=(
                f"> 🔹 Prefix: **`{PREFIX}`**  |  Slash: **`/poker`**\n"
                f"> 🔹 `{PREFIX}help <tên lệnh>` — xem chi tiết một lệnh\n"
                f"> 🔹 `{PREFIX}help <tên nhóm>` — xem chi tiết một nhóm lệnh\n"
                f"> 🔹 Gõ trực tiếp lệnh ở kênh chat là chạy được ngay!"
            ),
            color=self.get_color('primary'),
            timestamp=datetime.now()
        )

        for cog, commands_list in mapping.items():
            visible = sorted(
                [c for c in commands_list if not c.hidden],
                key=lambda c: c.name
            )
            if not visible:
                continue

            lines = [f"`{PREFIX}{cmd.name}` — {self.short_desc(cmd)}" for cmd in visible]
            if cog:
                cog_name = cog.qualified_name
                icon = self.COG_ICONS.get(cog_name, '📌')
            else:
                cog_name = 'Khác'
                icon = '📌'

            embed.add_field(
                name=f"{icon} {cog_name} ─ {len(visible)} lệnh",
                value='\n'.join(lines)[:1024],
                inline=False
            )

        if b.user is not None and b.user.avatar:
            embed.set_thumbnail(url=b.user.avatar.url)

        embed.set_footer(text=f"⚡ {total} lệnh • Version {bot_version} • Đang chạy trên {len(b.guilds)} servers")
        await self.get_destination().send(embed=embed)
    
    async def send_command_help(self, command):
        """Hiển thị chi tiết một lệnh"""
        icon = self.COG_ICONS.get(command.cog_name, '📌')
        embed = discord.Embed(
            title=f"📖 Lệnh: `{PREFIX}{command.name}`",
            description=command.help or "Không có mô tả",
            color=self.get_color('info')
        )

        usage = f"`{PREFIX}{command.name}"
        if command.signature:
            usage += f" {command.signature}"
        usage += "`"

        embed.add_field(name="📝 Cú pháp", value=usage, inline=False)
        embed.add_field(name=f"{icon} Nhóm", value=command.cog_name or "Khác", inline=True)

        if command.aliases:
            embed.add_field(
                name="🔗 Aliases",
                value=', '.join(f"`{alias}`" for alias in command.aliases),
                inline=True
            )

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        """Hiển thị các lệnh trong một nhóm"""
        visible = sorted(
            [c for c in cog.get_commands() if not c.hidden],
            key=lambda c: c.name
        )
        icon = self.COG_ICONS.get(cog.qualified_name, '📌')

        embed = discord.Embed(
            title=f"{icon} Nhóm lệnh: {cog.qualified_name}",
            description=cog.description or "Không có mô tả",
            color=self.get_color('primary')
        )

        lines = [
            f"`{PREFIX}{cmd.name}`{self.aliases_text(cmd)} — {self.short_desc(cmd)}"
            for cmd in visible
        ]
        embed.add_field(
            name=f"📋 {len(visible)} lệnh",
            value='\n'.join(lines)[:1024] if lines else "Không có lệnh nào",
            inline=False
        )
        embed.set_footer(text=f"Dùng `{PREFIX}help <tên lệnh>` để xem chi tiết")
        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error):
        """Khi không tìm thấy lệnh/nhóm trong help"""
        embed = discord.Embed(
            title="❌ Không tìm thấy!",
            description=f"{error}\nDùng `{PREFIX}help` để xem toàn bộ lệnh.",
            color=self.get_color('error')
        )
        await self.get_destination().send(embed=embed)

bot.help_command = CustomHelp()

# ===== SỰ KIỆN =====
@bot.event
async def on_ready():
    """Khi bot sẵn sàng"""
    logger.info(f"✅ Bot online: {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"📊 Hoạt động trên {len(bot.guilds)} servers")
    logger.info(f"🏠 Tên: {bot_name} | Version: {bot_version}")
    
    # Set activity từ config
    activity_types = {
        'playing': discord.ActivityType.playing,
        'watching': discord.ActivityType.watching,
        'listening': discord.ActivityType.listening,
        'streaming': discord.ActivityType.streaming,
    }
    
    activity_type = activity_types.get(bot_activity_type, discord.ActivityType.playing)
    
    await bot.change_presence(
        activity=discord.Activity(
            type=activity_type,
            name=bot_activity
        ),
        status=discord.Status.online
    )
    
    # Log thông tin cogs
    logger.info(f"📦 Loaded {len(bot.cogs)} cogs")
    
    # Log features - CHỈ LOG FEATURES BẬT
    features = config.get('features', {})
    enabled_features = [f for f, e in features.items() if e]
    
    if enabled_features:
        logger.info(f"✅ Features bật: {', '.join(enabled_features)}")
    
    # Sync slash commands (chạy 1 lần mỗi phiên)
    if not getattr(bot, 'slash_synced', False):
        try:
            synced = await bot.tree.sync()
            logger.info(f"🔄 Đã đồng bộ {len(synced)} slash commands")
            bot.slash_synced = True
        except Exception as e:
            logger.error(f"❌ Lỗi sync slash commands: {e}")

@bot.event
async def on_guild_join(guild):
    """Khi bot tham gia server mới"""
    logger.info(f"📥 Bot tham gia server: {guild.name} (ID: {guild.id})")
    
    try:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                embed = discord.Embed(
                    title=f"👋 Xin chào! Tôi là {bot_name}",
                    description=f"Cảm ơn đã mời tôi vào server!\nPrefix: `{PREFIX}`\nDùng `{PREFIX}help` để xem lệnh",
                    color=discord.Color(int(config.get('colors.primary', '#7289DA').replace('#', ''), 16))
                )
                await channel.send(embed=embed)
                break
    except:
        pass

@bot.event
async def on_guild_remove(guild):
    """Khi bot rời server"""
    logger.info(f"📤 Bot rời server: {guild.name} (ID: {guild.id})")

@bot.event
async def on_command_error(ctx, error):
    """Xử lý lỗi toàn cục"""
    from handlers.error_handler import handle_error
    await handle_error(ctx, error)

@bot.event
async def on_message(message):
    """Xử lý tin nhắn"""
    if message.author.bot:
        return
    
    if not message.guild:
        return
    
    await bot.process_commands(message)

# ===== COMMANDS =====
@bot.command(name='reloadconfig', hidden=True)
@commands.is_owner()
async def reload_config(ctx):
    """🔄 Reload config.json"""
    config.load()
    await ctx.send("✅ Đã reload config.json!")
    logger.info("🔄 Reloaded config.json")

# ===== MAIN =====
async def main():
    """Hàm chính"""
    async with bot:
        # Khởi tạo database
        try:
            db = Database()
            await db.initialize()
            bot.db = db
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
        
        # Load extensions
        loaded, failed = await load_extensions()
        logger.info(f"📦 Loaded {len(loaded)} cogs, {len(failed)} failed")
        
        # Chạy bot
        try:
            await bot.start(TOKEN)
        except discord.LoginFailure:
            logger.error("❌ Token không hợp lệ!")
        except discord.PrivilegedIntentsRequired:
            logger.error("❌ Cần bật Privileged Intents trong Discord Developer Portal!")
        except Exception as e:
            logger.error(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot đã dừng bởi người dùng")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")