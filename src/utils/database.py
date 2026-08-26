"""
Database Utility
Kết nối và thao tác database (SQLite)
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    """Quản lý kết nối database"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or 'database/bot.db'
        self.connection = None
        
        # Tạo thư mục database nếu chưa có
        Path('database').mkdir(exist_ok=True)
    
    async def initialize(self):
        """Khởi tạo database"""
        try:
            # Import SQLite
            import sqlite3
            import aiosqlite
            
            # Tạo connection
            self.connection = await aiosqlite.connect(self.db_path)
            
            # Tạo bảng
            await self.create_tables()
            
            logger.info(f"✅ Database initialized: {self.db_path}")
            
        except ImportError:
            logger.warning("⚠️ aiosqlite chưa được cài đặt! Dùng pip install aiosqlite")
        except Exception as e:
            logger.error(f"❌ Database init error: {e}")
    
    async def create_tables(self):
        """Tạo các bảng cần thiết"""
        if not self.connection:
            return
        
        # Bảng users
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                discord_tag TEXT,
                coins INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                experience INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bảng warnings
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                guild_id INTEGER,
                reason TEXT,
                warned_by INTEGER,
                warned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bảng guilds
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS guilds (
                id INTEGER PRIMARY KEY,
                name TEXT,
                owner_id INTEGER,
                prefix TEXT DEFAULT '!',
                welcome_channel INTEGER,
                log_channel INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bảng mutes (vừa là lịch sử vừa là trạng thái mute đang hiệu lực)
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS mutes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                guild_id INTEGER,
                muted_by INTEGER,
                reason TEXT,
                muted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                unmute_at REAL,
                unmuted INTEGER DEFAULT 0
            )
        ''')
        
        await self.connection.commit()
    
    @property
    def is_ready(self):
        """Kiểm tra connection đã sẵn sàng"""
        return self.connection is not None
    
    # ==========================================
    # WARNINGS
    # ==========================================
    
    async def add_warning(self, guild_id, user_id, reason, warned_by):
        """Thêm cảnh cáo cho thành viên"""
        if not self.is_ready:
            return
        await self.connection.execute(
            'INSERT INTO warnings (user_id, guild_id, reason, warned_by) VALUES (?, ?, ?, ?)',
            (user_id, guild_id, reason, warned_by)
        )
        await self.connection.commit()
    
    async def get_warnings(self, guild_id, user_id):
        """Lấy danh sách cảnh cáo của thành viên"""
        if not self.is_ready:
            return []
        cursor = await self.connection.execute(
            'SELECT id, reason, warned_by, warned_at FROM warnings '
            'WHERE guild_id = ? AND user_id = ? ORDER BY id',
            (guild_id, user_id)
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return rows
    
    async def get_warn_count(self, guild_id, user_id):
        """Đếm số cảnh cáo của thành viên"""
        if not self.is_ready:
            return 0
        cursor = await self.connection.execute(
            'SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?',
            (guild_id, user_id)
        )
        row = await cursor.fetchone()
        await cursor.close()
        return row[0] if row else 0
    
    async def clear_warnings(self, guild_id, user_id):
        """Xóa toàn bộ cảnh cáo của thành viên"""
        if not self.is_ready:
            return
        await self.connection.execute(
            'DELETE FROM warnings WHERE guild_id = ? AND user_id = ?',
            (guild_id, user_id)
        )
        await self.connection.commit()
    
    # ==========================================
    # MUTES (chỉ lưu lịch sử để tăng cấp độ mute -
    # việc mute/unmute thực tế do Discord Timeout tự xử lý)
    # ==========================================
    
    async def add_mute(self, guild_id, user_id, unmute_at, muted_by=None, reason=None):
        """Ghi nhận một lần mute (unmute_at là unix timestamp)"""
        if not self.is_ready:
            return
        await self.connection.execute(
            'INSERT INTO mutes (user_id, guild_id, muted_by, reason, unmute_at, unmuted) VALUES (?, ?, ?, ?, ?, 1)',
            (user_id, guild_id, muted_by, reason, unmute_at)
        )
        await self.connection.commit()
    
    async def get_mute_count(self, guild_id, user_id):
        """Đếm tổng số lần bị mute (dùng để tăng cấp độ mute)"""
        if not self.is_ready:
            return 0
        cursor = await self.connection.execute(
            'SELECT COUNT(*) FROM mutes WHERE guild_id = ? AND user_id = ?',
            (guild_id, user_id)
        )
        row = await cursor.fetchone()
        await cursor.close()
        return row[0] if row else 0
    
    async def close(self):
        """Đóng kết nối database"""
        if self.connection:
            await self.connection.close()
            logger.info("✅ Database closed")