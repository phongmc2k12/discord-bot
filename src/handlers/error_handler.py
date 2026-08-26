"""
Error Handler
Xử lý lỗi toàn cục cho bot
"""

import discord
from discord.ext import commands
import traceback

async def handle_error(ctx, error):
    """Xử lý lỗi và gửi thông báo phù hợp"""
    
    # Lỗi lệnh không tồn tại
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❌ Lệnh không tồn tại! Dùng `{ctx.prefix}help` để xem danh sách.")
        return
    
    # Lỗi thiếu quyền
    if isinstance(error, commands.MissingPermissions):
        missing = ", ".join(error.missing_permissions)
        await ctx.send(f"❌ Bạn thiếu quyền: `{missing}`")
        return
    
    # Lỗi thiếu tham số
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Thiếu tham số: `{error.param.name}`")
        return
    
    # Lỗi tham số sai
    if isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Tham số không hợp lệ! Xem hướng dẫn với `{ctx.prefix}help {ctx.command.name}`")
        return
    
    # Lỗi cooldown
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏰ Lệnh đang trong thời gian chờ! Thử lại sau `{error.retry_after:.1f}` giây.")
        return
    
    # Lỗi khác (log lại)
    error_msg = f"❌ Đã xảy ra lỗi: {str(error)}"
    await ctx.send(error_msg)
    
    # In traceback để debug
    print(f"Lỗi trong lệnh `{ctx.command}` của {ctx.author}:")
    traceback.print_exc()