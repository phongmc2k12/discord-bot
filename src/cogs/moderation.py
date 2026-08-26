"""
COGS: Moderation Commands
Lệnh kiểm duyệt: warn, mute, unmute, antispam, check
Chống spam: Tự động mute khi gửi quá nhiều tin nhắn
Mute: dùng Discord Timeout - Discord tự gỡ khi hết hạn (không sợ bot restart)
Lịch sử warn/mute lưu vào SQLite
Cấp độ mute (auto): 5p -> 1h -> 3h -> 10h -> 24h -> 3d
"""

import discord
from discord.ext import commands
from datetime import datetime, timedelta
import time
import json

MAX_TIMEOUT = 28 * 86400  # Discord giới hạn timeout tối đa 28 ngày

class Moderation(commands.Cog):
    """Lệnh kiểm duyệt cho server"""
    
    def __init__(self, bot):
        self.bot = bot
        self.message_data = {}
        self.antispam_enabled = {}
        self.spam_settings = {
            'max_messages': 7,
            'time_window': 10,
        }
        self.mute_levels = [300, 3600, 10800, 36000, 86400, 259200]
    
    # ==========================================
    # DATABASE & CONFIG HELPERS
    # ==========================================
    @property
    def db(self):
        """Lấy database từ bot"""
        return getattr(self.bot, 'db', None)
    
    def db_ok(self):
        """Kiểm tra database sẵn sàng"""
        return self.db is not None and self.db.is_ready
    
    def get_color(self, color_name='primary'):
        """Lấy màu từ config chung của bot"""
        color_hex = self.bot.config.get(f'colors.{color_name}', '#7289DA')
        return discord.Color(int(color_hex.replace('#', ''), 16))
    
    # ==========================================
    # ÁP DỤNG MUTE (dùng chung: lệnh, spam, đủ warn)
    # ==========================================
    async def apply_mute(self, guild, member, duration_seconds, reason, muted_by=None):
        """
        Mute bằng Discord Timeout + ghi lịch sử vào DB
        Trả về (thành_công, số_lần_bị_mute) - thất bại nếu đang bị mute
        """
        if member.is_timed_out():
            return False, 0
        
        duration_seconds = min(int(duration_seconds), MAX_TIMEOUT)
        mute_count = await self.db.get_mute_count(guild.id, member.id) + 1
        until = datetime.now() + timedelta(seconds=duration_seconds)
        
        await member.timeout(until, reason=reason[:500])
        await self.db.add_mute(
            guild.id, member.id,
            unmute_at=time.time() + duration_seconds,
            muted_by=muted_by,
            reason=reason[:500]
        )
        
        return True, mute_count
    
    # ==========================================
    # LẤY THỜI GIAN MUTE (dựa trên lịch sử trong DB)
    # ==========================================
    async def get_mute_duration(self, guild_id, member_id):
        """Lấy thời gian mute theo cấp độ (số lần bị mute trước đó)"""
        mute_count = await self.db.get_mute_count(guild_id, member_id)
        duration = self.mute_levels[mute_count] if mute_count < len(self.mute_levels) else self.mute_levels[-1]
        return duration
    
    def format_duration(self, seconds):
        """Format thời gian"""
        if seconds < 60:
            return f"{seconds} giây"
        elif seconds < 3600:
            return f"{seconds // 60} phút"
        elif seconds < 86400:
            return f"{seconds // 3600} giờ"
        else:
            return f"{seconds // 86400} ngày"
    
    # ==========================================
    # CHỐNG SPAM
    # ==========================================
    @commands.Cog.listener()
    async def on_message(self, message):
        """Lắng nghe tin nhắn để chống spam"""
        if message.author.bot or not message.guild:
            return
        if not self.antispam_enabled.get(message.guild.id, True):
            return
        if not self.db_ok():
            return
        await self.check_spam(message)
    
    async def check_spam(self, message):
        """Kiểm tra số lượng tin nhắn"""
        guild_id = message.guild.id
        author_id = message.author.id
        
        if guild_id not in self.message_data:
            self.message_data[guild_id] = {}
        if author_id not in self.message_data[guild_id]:
            self.message_data[guild_id][author_id] = []
        
        now = datetime.now()
        user_messages = self.message_data[guild_id][author_id]
        user_messages = [t for t in user_messages if (now - t).total_seconds() < self.spam_settings['time_window']]
        user_messages.append(now)
        self.message_data[guild_id][author_id] = user_messages
        
        if len(user_messages) >= self.spam_settings['max_messages']:
            self.message_data[guild_id][author_id] = []
            await self.mute_spammer(message)
    
    async def mute_spammer(self, message):
        """Mute người spam"""
        try:
            member = message.author
            guild = message.guild
            mute_duration = await self.get_mute_duration(guild.id, member.id)
            
            applied, mute_count = await self.apply_mute(
                guild, member,
                duration_seconds=mute_duration,
                reason="Spam tin nhắn"
            )
            
            if not applied:
                return
            
            embed = discord.Embed(
                title="🚨 Chống Spam",
                description=f"**{member.mention}** đã bị mute vì gửi quá nhiều tin nhắn!",
                color=self.get_color('error')
            )
            embed.add_field(name="📝 Lý do", value=f"Gửi {self.spam_settings['max_messages']} tin trong {self.spam_settings['time_window']} giây", inline=False)
            embed.add_field(name="⏱️ Thời gian mute", value=self.format_duration(mute_duration), inline=True)
            embed.add_field(name="📊 Số lần vi phạm", value=f"Lần thứ {mute_count}", inline=True)
            
            await message.channel.send(embed=embed)
        except Exception as e:
            print(f"❌ Lỗi mute spam: {e}")
    
    # ==========================================
    # LỆNH ANTISPAM
    # ==========================================
    @commands.command(name='antispam')
    @commands.has_permissions(administrator=True)
    async def antispam(self, ctx, option: str = None):
        """🛡️ Bật/tắt chống spam"""
        if not option:
            status = self.antispam_enabled.get(ctx.guild.id, True)
            await ctx.send(f"🛡️ Chống spam: **{'✅ Bật' if status else '❌ Tắt'}**\nCài đặt: `{self.spam_settings['max_messages']}` tin / `{self.spam_settings['time_window']}s`")
            return
        if option.lower() == 'on':
            self.antispam_enabled[ctx.guild.id] = True
            await ctx.send("✅ Đã bật chống spam!")
        elif option.lower() == 'off':
            self.antispam_enabled[ctx.guild.id] = False
            await ctx.send("❌ Đã tắt chống spam!")
        else:
            await ctx.send("Dùng: `!antispam on` hoặc `!antispam off`")
    
    @commands.command(name='antispamset')
    @commands.has_permissions(administrator=True)
    async def antispam_set(self, ctx, max_messages: int = 7, time_window: int = 10):
        """⚙️ Cài đặt: !antispamset <số tin> <giây>"""
        if max_messages < 2:
            await ctx.send("❌ Số tin nhắn phải từ 2 trở lên!")
            return
        if time_window < 3:
            await ctx.send("❌ Thời gian phải từ 3 giây trở lên!")
            return
        self.spam_settings['max_messages'] = max_messages
        self.spam_settings['time_window'] = time_window
        await ctx.send(f"✅ Đã cài đặt: {max_messages} tin / {time_window} giây")
    
    # ==========================================
    # LỆNH MUTE
    # ==========================================
    @commands.command(name='mute')
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, duration: str, *, reason="Không có lý do"):
        """🔇 Mute thành viên: !mute @user 1h lý do"""
        if member == ctx.author:
            await ctx.send("❌ Bạn không thể tự mute chính mình!")
            return
        if member.bot:
            await ctx.send("❌ Không thể mute bot!")
            return
        if member == ctx.guild.owner:
            await ctx.send("❌ Không thể mute chủ server!")
            return
        if member.top_role >= ctx.guild.me.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ Bạn không đủ quyền mute người này!")
            return
        if not self.db_ok():
            await ctx.send("❌ Database chưa sẵn sàng!")
            return
        
        time_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
        try:
            duration_num = int(duration[:-1])
            duration_unit = duration[-1].lower()
            total_seconds = duration_num * time_map.get(duration_unit, 3600)
        except:
            await ctx.send("❌ Sai định dạng! Dùng: `5m`, `1h`, `3h`, `10h`, `1d`, `7d`")
            return
        
        if total_seconds <= 0 or total_seconds > MAX_TIMEOUT:
            await ctx.send(f"❌ Thời gian mute tối đa là `{self.format_duration(MAX_TIMEOUT)}`!")
            return
        
        applied, _ = await self.apply_mute(
            ctx.guild, member,
            duration_seconds=total_seconds,
            reason=f"Mute bởi {ctx.author}: {reason}",
            muted_by=ctx.author.id
        )
        
        if not applied:
            await ctx.send(f"❌ **{member}** đã bị mute rồi!")
            return
        
        unmute_ts = int(time.time() + total_seconds)
        embed = discord.Embed(
            title="🔇 Đã Mute",
            description=f"**{member}** đã bị mute",
            color=self.get_color('error')
        )
        embed.add_field(name="📝 Lý do", value=reason, inline=True)
        embed.add_field(name="⏱️ Thời gian", value=self.format_duration(total_seconds), inline=True)
        embed.add_field(name="⏰ Hết mute", value=f"<t:{unmute_ts}:R>", inline=True)
        embed.add_field(name="👮 Bởi", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name='unmute')
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        """🔊 Unmute thành viên"""
        if not member.is_timed_out():
            await ctx.send(f"❌ **{member}** không bị mute!")
            return
        await member.timeout(None, reason=f"Unmute bởi {ctx.author}")
        await ctx.send(f"✅ Đã unmute **{member}**!")
    
    # ==========================================
    # LỆNH WARN (lưu vào SQLite)
    # ==========================================
    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason="Không có lý do"):
        """⚠️ Cảnh cáo thành viên"""
        if member == ctx.author:
            await ctx.send("❌ Bạn không thể tự cảnh cáo chính mình!")
            return
        if member.bot:
            await ctx.send("❌ Không thể cảnh cáo bot!")
            return
        if not self.db_ok():
            await ctx.send("❌ Database chưa sẵn sàng!")
            return
        
        await self.db.add_warning(ctx.guild.id, member.id, reason, ctx.author.id)
        warn_id = await self.db.get_warn_count(ctx.guild.id, member.id)
        
        await ctx.send(f"⚠️ Đã cảnh cáo **{member}** lần {warn_id}: {reason}")
        
        auto_mute_after = self.bot.config.get('moderation.auto_mute_after_warns', 3)
        if warn_id >= auto_mute_after and not member.is_timed_out():
            try:
                mute_duration = await self.get_mute_duration(ctx.guild.id, member.id)
                applied, _ = await self.apply_mute(
                    ctx.guild, member,
                    duration_seconds=mute_duration,
                    reason=f"Đủ {auto_mute_after} cảnh cáo",
                    muted_by=ctx.author.id
                )
                if applied:
                    await ctx.send(
                        f"⚠️ **{member.mention}** bị mute vì đủ {auto_mute_after} cảnh cáo! "
                        f"(⏱️ {self.format_duration(mute_duration)})"
                    )
            except Exception as e:
                print(f"❌ Lỗi auto-mute sau warn: {e}")
    
    @commands.command(name='warnings', aliases=['warns'])
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx, member: discord.Member):
        """📋 Xem cảnh cáo"""
        if not self.db_ok():
            await ctx.send("❌ Database chưa sẵn sàng!")
            return
        
        warns = await self.db.get_warnings(ctx.guild.id, member.id)
        if not warns:
            await ctx.send(f"**{member}** không có cảnh cáo!")
            return
        
        embed = discord.Embed(
            title=f"📋 Cảnh cáo của {member}",
            description=f"Tổng: {len(warns)} cảnh cáo",
            color=self.get_color('warning')
        )
        for warn in warns[-10:]:
            embed.add_field(
                name=f"⚠️ Lần {warn[0]}",
                value=f"Lý do: {warn[1]}\nBởi: <@{warn[2]}> | ⏰ {warn[3]}",
                inline=False
            )
        await ctx.send(embed=embed)
    
    @commands.command(name='clearwarn', aliases=['clearwarns'])
    @commands.has_permissions(manage_messages=True)
    async def clear_warn(self, ctx, member: discord.Member):
        """🗑️ Xóa cảnh cáo"""
        if not self.db_ok():
            await ctx.send("❌ Database chưa sẵn sàng!")
            return
        
        count = await self.db.get_warn_count(ctx.guild.id, member.id)
        if count == 0:
            await ctx.send(f"❌ **{member}** không có cảnh cáo!")
            return
        
        await self.db.clear_warnings(ctx.guild.id, member.id)
        await ctx.send(f"✅ Đã xóa `{count}` cảnh cáo của **{member}**!")
    
    # ==========================================
    # LỆNH CHECK (đọc từ SQLite + trạng thái timeout)
    # ==========================================
    @commands.command(name='check')
    @commands.has_permissions(manage_messages=True)
    async def check(self, ctx, member: discord.Member):
        """📊 Xem thông tin moderation của thành viên"""
        if not self.db_ok():
            await ctx.send("❌ Database chưa sẵn sàng!")
            return
        
        warn_count = await self.db.get_warn_count(ctx.guild.id, member.id)
        mute_count = await self.db.get_mute_count(ctx.guild.id, member.id)
        
        is_muted = member.is_timed_out()
        timed_out_until = None
        if is_muted and member.timed_out_until:
            timed_out_until = int(member.timed_out_until.timestamp())
        
        embed = discord.Embed(
            title=f"📊 Moderation Check: {member}",
            color=self.get_color('primary')
        )
        embed.add_field(name="⚠️ Cảnh cáo", value=f"`{warn_count}` lần", inline=True)
        embed.add_field(name="🔇 Số lần mute", value=f"`{mute_count}` lần", inline=True)
        if is_muted and timed_out_until:
            embed.add_field(name="🔇 Hết mute", value=f"<t:{timed_out_until}:R>", inline=True)
        else:
            embed.add_field(name="🔇 Đang bị mute", value="❌ Không", inline=True)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
