"""
COGS: Admin Commands
Lệnh admin: kick, ban, unban, clear, slowmode, lock, unlock, reload, load, unload, shutdown, setlog
"""

import discord
from discord.ext import commands
from datetime import datetime
import asyncio

class Admin(commands.Cog):
    """Lệnh admin cho server"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def get_color(self, color_name='primary'):
        """Lấy màu từ config chung của bot"""
        color_hex = self.bot.config.get(f'colors.{color_name}', '#7289DA')
        return discord.Color(int(color_hex.replace('#', ''), 16))
    
    # ==========================================
    # LỆNH KICK
    # ==========================================
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="Không có lý do"):
        """👢 Kick thành viên khỏi server"""
        if member == ctx.author:
            await ctx.send("❌ Bạn không thể tự kick chính mình!")
            return
        if member.bot:
            await ctx.send("❌ Không thể kick bot!")
            return
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ Bạn không đủ quyền để kick người này!")
            return
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ Bot không đủ quyền để kick người này!")
            return
        
        try:
            await member.kick(reason=f"Kick bởi {ctx.author}: {reason}")
            embed = discord.Embed(
                title="👢 Đã Kick",
                description=f"**{member}** đã bị kick khỏi server",
                color=self.get_color('error'),
                timestamp=datetime.now()
            )
            embed.add_field(name="📝 Lý do", value=reason, inline=True)
            embed.add_field(name="👮 Bởi", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Lỗi khi kick: {str(e)}")
    
    # ==========================================
    # LỆNH BAN
    # ==========================================
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="Không có lý do"):
        """🔨 Ban thành viên khỏi server"""
        if member == ctx.author:
            await ctx.send("❌ Bạn không thể tự ban chính mình!")
            return
        if member.bot:
            await ctx.send("❌ Không thể ban bot!")
            return
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ Bạn không đủ quyền để ban người này!")
            return
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ Bot không đủ quyền để ban người này!")
            return
        
        try:
            await member.ban(reason=f"Ban bởi {ctx.author}: {reason}", delete_message_days=7)
            embed = discord.Embed(
                title="🔨 Đã Ban",
                description=f"**{member}** đã bị ban khỏi server",
                color=self.get_color('error'),
                timestamp=datetime.now()
            )
            embed.add_field(name="📝 Lý do", value=reason, inline=True)
            embed.add_field(name="👮 Bởi", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Lỗi khi ban: {str(e)}")
    
    # ==========================================
    # LỆNH UNBAN
    # ==========================================
    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        """🔓 Unban thành viên bằng ID"""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"Unban bởi {ctx.author}")
            embed = discord.Embed(
                title="🔓 Đã Unban",
                description=f"**{user}** đã được unban",
                color=self.get_color('success'),
                timestamp=datetime.now()
            )
            embed.add_field(name="👮 Bởi", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("❌ Không tìm thấy user với ID này!")
        except Exception as e:
            await ctx.send(f"❌ Lỗi khi unban: {str(e)}")
    
    # ==========================================
    # LỆNH CLEAR
    # ==========================================
    @commands.command(name='clear', aliases=['purge'])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 10, member: discord.Member = None):
        """🗑️ Xóa tin nhắn: !clear 10 hoặc !clear 10 @user"""
        if amount < 1 or amount > 100:
            await ctx.send("❌ Số lượng phải từ 1 đến 100!")
            return
        
        await ctx.message.delete()
        
        if member:
            def check(msg):
                return msg.author == member
            deleted = await ctx.channel.purge(limit=amount, check=check)
        else:
            deleted = await ctx.channel.purge(limit=amount)
        
        msg = await ctx.send(f"✅ Đã xóa `{len(deleted)}` tin nhắn!")
        await asyncio.sleep(3)
        await msg.delete()
    
    # ==========================================
    # LỆNH SLOWMODE
    # ==========================================
    @commands.command(name='slowmode')
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = 0):
        """🐌 Bật/tắt slowmode"""
        if seconds < 0 or seconds > 21600:
            await ctx.send("❌ Thời gian phải từ 0 đến 21600 giây!")
            return
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send("✅ Đã tắt slowmode!")
        else:
            await ctx.send(f"✅ Đã bật slowmode: {seconds} giây!")
    
    # ==========================================
    # LỆNH LOCK/UNLOCK
    # ==========================================
    @commands.command(name='lock')
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """🔒 Khóa kênh"""
        if not channel:
            channel = ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(f"🔒 Đã khóa kênh {channel.mention}!")
    
    @commands.command(name='unlock')
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """🔓 Mở khóa kênh"""
        if not channel:
            channel = ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send(f"🔓 Đã mở khóa kênh {channel.mention}!")
    
    # ==========================================
    # LỆNH SET LOG
    # ==========================================
    @commands.command(name='setlog')
    @commands.has_permissions(administrator=True)
    async def set_log(self, ctx, channel: discord.TextChannel = None):
        """📝 Set kênh log"""
        if not channel:
            log_channel_id = self.bot.config.get('channels.mod_log_channel')
            if log_channel_id:
                log_channel = ctx.guild.get_channel(log_channel_id)
                await ctx.send(f"📝 Kênh log hiện tại: {log_channel.mention if log_channel else 'Không tìm thấy'}")
            else:
                await ctx.send("❌ Chưa set kênh log! Dùng: `!setlog #kênh`")
            return
        self.bot.config.set('channels.mod_log_channel', channel.id)
        await ctx.send(f"✅ Đã set kênh log: {channel.mention}")
    
    # ==========================================
    # LỆNH RELOAD COG
    # ==========================================
    @commands.command(name='reload')
    @commands.is_owner()
    async def reload(self, ctx, cog: str = None):
        """🔄 Reload cog"""
        if not cog:
            loaded_cogs = list(self.bot.extensions.keys())
            success = 0
            failed = 0
            for cog_name in loaded_cogs:
                try:
                    await self.bot.reload_extension(cog_name)
                    success += 1
                except:
                    failed += 1
            await ctx.send(f"✅ Reload: `{success}` cog\n❌ Lỗi: `{failed}` cog")
            return
        try:
            await self.bot.reload_extension(f'cogs.{cog}')
            await ctx.send(f"✅ Đã reload cog `{cog}`!")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {str(e)}")
    
    # ==========================================
    # LỆNH LOAD COG
    # ==========================================
    @commands.command(name='load')
    @commands.is_owner()
    async def load(self, ctx, cog: str):
        """📥 Load cog"""
        try:
            await self.bot.load_extension(f'cogs.{cog}')
            await ctx.send(f"✅ Đã load cog `{cog}`!")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {str(e)}")
    
    # ==========================================
    # LỆNH UNLOAD COG
    # ==========================================
    @commands.command(name='unload')
    @commands.is_owner()
    async def unload(self, ctx, cog: str):
        """📤 Unload cog"""
        try:
            await self.bot.unload_extension(f'cogs.{cog}')
            await ctx.send(f"✅ Đã unload cog `{cog}`!")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {str(e)}")
    
    # ==========================================
    # LỆNH SHUTDOWN
    # ==========================================
    @commands.command(name='shutdown')
    @commands.is_owner()
    async def shutdown(self, ctx):
        """🔴 Tắt bot"""
        await ctx.send("🔴 Bot đang tắt...")
        await self.bot.close()

async def setup(bot):
    await bot.add_cog(Admin(bot))