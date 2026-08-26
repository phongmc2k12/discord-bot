"""
Logger Utility
Ghi log hệ thống với màu sắc và format đẹp
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Tạo thư mục logs nếu chưa có
Path('logs').mkdir(exist_ok=True)


class ColoredFormatter(logging.Formatter):
    """Formatter với màu sắc cho console"""
    
    # Mã màu ANSI
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m'  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Thêm màu cho level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        # Format message
        return super().format(record)


def setup_logger(level='INFO'):
    """
    Thiết lập logger với console và file
    
    Args:
        level (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging.Logger: Logger đã được cấu hình
    """
    
    # Tạo logger
    logger = logging.getLogger('discord_bot')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Xóa handlers cũ nếu có (tránh duplicate)
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # ===== CONSOLE HANDLER (Có màu) =====
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    console_format = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # ===== FILE HANDLER - BOT LOG (Tất cả log) =====
    file_handler = logging.FileHandler(
        'logs/bot.log',
        encoding='utf-8',
        mode='a'  # Append mode
    )
    file_handler.setLevel(logging.DEBUG)
    
    file_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    # ===== FILE HANDLER - ERROR LOG (Chỉ lỗi) =====
    error_handler = logging.FileHandler(
        'logs/error.log',
        encoding='utf-8',
        mode='a'  # Append mode
    )
    error_handler.setLevel(logging.ERROR)
    
    error_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_handler.setFormatter(error_format)
    logger.addHandler(error_handler)
    
    return logger


# ===== CÁC HÀM TIỆN ÍCH =====

def log_command(ctx, command_name, args=None):
    """Ghi log khi có lệnh được thực thi"""
    logger = logging.getLogger('discord_bot')
    
    user = ctx.author
    guild = ctx.guild
    channel = ctx.channel
    
    log_msg = (
        f"📝 Command: {command_name} | "
        f"User: {user.name}#{user.discriminator} (ID: {user.id}) | "
        f"Server: {guild.name if guild else 'DM'} | "
        f"Channel: #{channel.name if hasattr(channel, 'name') else 'DM'}"
    )
    
    if args:
        log_msg += f" | Args: {args}"
    
    logger.info(log_msg)


def log_error(error, context=None):
    """Ghi log lỗi chi tiết"""
    logger = logging.getLogger('discord_bot')
    
    error_msg = f"❌ Error: {error}"
    if context:
        error_msg += f" | Context: {context}"
    
    logger.error(error_msg)


def log_event(event_type, data=None):
    """Ghi log sự kiện (member join/leave, etc)"""
    logger = logging.getLogger('discord_bot')
    
    log_msg = f"📢 Event: {event_type}"
    if data:
        log_msg += f" | Data: {data}"
    
    logger.info(log_msg)


# ===== LOGGER ĐƠN GIẢN (Dùng cho các module khác) =====

class SimpleLogger:
    """Wrapper đơn giản cho logging"""
    
    def __init__(self, name='discord_bot'):
        self.logger = logging.getLogger(name)
    
    def debug(self, msg):
        self.logger.debug(msg)
    
    def info(self, msg):
        self.logger.info(msg)
    
    def warning(self, msg):
        self.logger.warning(msg)
    
    def error(self, msg):
        self.logger.error(msg)
    
    def critical(self, msg):
        self.logger.critical(msg)


# ===== TEST =====
if __name__ == "__main__":
    # Test logger
    logger = setup_logger('DEBUG')
    
    logger.debug("🔍 Debug message")
    logger.info("ℹ️ Info message")
    logger.warning("⚠️ Warning message")
    logger.error("❌ Error message")
    logger.critical("💀 Critical message")
    
    print("\n✅ Logger test completed! Check logs/bot.log and logs/error.log")