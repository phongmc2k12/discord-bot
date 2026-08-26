"""
COGS: Economy Commands
Lệnh kinh tế: balance, work, daily, gamble, bet, slots, coinflip, poker, taixiu, deposit, withdraw, give, leaderboard
Poker: hybrid command (!poker và /poker) - xem bài qua ephemeral (slash) hoặc DM (prefix)
"""

import discord
from discord import app_commands
from discord.ext import commands
import random
import json
from datetime import datetime, timedelta
from pathlib import Path

class Economy(commands.Cog):
    """Lệnh kinh tế cho bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.daily_cooldown = {}
        self.work_cooldown = {}
        self.poker_games = {}
        self.data_path = Path(__file__).parent.parent / 'data' / 'economy.json'
        self.load_data()
    
    def load_data(self):
        """Load dữ liệu economy từ file"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.economy_data = json.load(f)
        except:
            self.economy_data = {}
            self.save_data()
    
    def save_data(self):
        """Lưu dữ liệu economy ra file"""
        try:
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.economy_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Lỗi lưu economy: {e}")
    
    def get_user_data(self, user_id):
        """Lấy dữ liệu user"""
        user_id = str(user_id)
        if user_id not in self.economy_data:
            self.economy_data[user_id] = {
                'balance': 1000,
                'bank': 0,
                'items': [],
                'last_daily': None,
                'last_work': None
            }
            self.save_data()
        return self.economy_data[user_id]
    
    # ==========================================
    # 💰 LỆNH BALANCE
    # ==========================================
    @commands.command(name='balance', aliases=['bal', 'money'])
    async def balance(self, ctx, member: discord.Member = None):
        """💰 Xem số tiền của bạn hoặc người khác"""
        if not member:
            member = ctx.author
        
        data = self.get_user_data(member.id)
        
        embed = discord.Embed(
            title=f"💰 Số dư của {member.name}",
            color=discord.Color.gold()
        )
        embed.add_field(name="💵 Tiền mặt", value=f"`{data['balance']:,}` xu", inline=True)
        embed.add_field(name="🏦 Ngân hàng", value=f"`{data['bank']:,}` xu", inline=True)
        embed.add_field(name="📊 Tổng", value=f"`{data['balance'] + data['bank']:,}` xu", inline=True)
        
        if data['items']:
            embed.add_field(name="🎒 Vật phẩm", value=", ".join(data['items']), inline=False)
        
        await ctx.send(embed=embed)
    
    # ==========================================
    # 📅 LỆNH DAILY
    # ==========================================
    @commands.command(name='daily')
    async def daily(self, ctx):
        """📅 Nhận tiền hàng ngày"""
        data = self.get_user_data(ctx.author.id)
        
        if data['last_daily']:
            last_daily = datetime.fromisoformat(data['last_daily'])
            time_left = datetime.now() - last_daily
            if time_left < timedelta(hours=24):
                remaining = timedelta(hours=24) - time_left
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                await ctx.send(f"⏰ Đã nhận daily! Chờ `{hours}h {minutes}m` nữa.")
                return
        
        amount = random.randint(500, 2000)
        data['balance'] += amount
        data['last_daily'] = datetime.now().isoformat()
        self.save_data()
        
        embed = discord.Embed(
            title="📅 Daily Reward",
            description=f"✅ Bạn đã nhận `{amount:,}` xu!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    # ==========================================
    # 💼 LỆNH WORK
    # ==========================================
    @commands.command(name='work')
    async def work(self, ctx):
        """💼 Đi làm kiếm tiền"""
        data = self.get_user_data(ctx.author.id)
        
        if data['last_work']:
            last_work = datetime.fromisoformat(data['last_work'])
            time_left = datetime.now() - last_work
            if time_left < timedelta(hours=1):
                remaining = timedelta(hours=1) - time_left
                minutes = int(remaining.total_seconds() // 60)
                await ctx.send(f"⏰ Đã làm việc! Chờ `{minutes}` phút nữa.")
                return
        
        jobs = [
            ("💻 Lập trình viên", 200, 500),
            ("👨‍🍳 Đầu bếp", 150, 400),
            ("🚀 Kỹ sư", 300, 700),
            ("📚 Giáo viên", 100, 300),
            ("🎵 Ca sĩ", 250, 600),
            ("🏥 Bác sĩ", 400, 800),
        ]
        
        job, min_salary, max_salary = random.choice(jobs)
        amount = random.randint(min_salary, max_salary)
        
        if random.random() < 0.1:
            amount *= 2
            bonus_text = "🎉 BONUS X2!"
        else:
            bonus_text = ""
        
        data['balance'] += amount
        data['last_work'] = datetime.now().isoformat()
        self.save_data()
        
        embed = discord.Embed(
            title="💼 Đi làm",
            description=f"Bạn làm **{job}** và kiếm được `{amount:,}` xu!",
            color=discord.Color.blue()
        )
        if bonus_text:
            embed.add_field(name="🎉 Bonus", value=bonus_text, inline=False)
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🎰 LỆNH GAMBLE
    # ==========================================
    @commands.command(name='gamble', aliases=['g'])
    async def gamble(self, ctx, amount: str = None):
        """🎰 Đánh bạc: !gamble <số tiền hoặc all/half>"""
        data = self.get_user_data(ctx.author.id)
        
        if not amount:
            await ctx.send("❌ Cách dùng: `!gamble <số tiền>` hoặc `!gamble all`")
            return
        
        if amount.lower() == 'all':
            bet = data['balance']
        elif amount.lower() == 'half':
            bet = data['balance'] // 2
        else:
            try:
                bet = int(amount)
            except:
                await ctx.send("❌ Số tiền không hợp lệ!")
                return
        
        if bet <= 0 or bet > data['balance']:
            await ctx.send(f"❌ Số tiền phải từ 1 đến `{data['balance']:,}`!")
            return
        
        result = random.random()
        
        if result < 0.4:
            win_amount = bet * 2
            data['balance'] += win_amount - bet
            self.save_data()
            embed = discord.Embed(title="🎰 Gambling", description=f"🎉 THẮNG! Nhận `{win_amount:,}` xu!", color=discord.Color.green())
        elif result < 0.6:
            embed = discord.Embed(title="🎰 Gambling", description=f"😅 HÒA! Nhận lại `{bet:,}` xu!", color=discord.Color.gold())
        else:
            data['balance'] -= bet
            self.save_data()
            embed = discord.Embed(title="🎰 Gambling", description=f"😢 THUA! Mất `{bet:,}` xu!", color=discord.Color.red())
        
        embed.add_field(name="💰 Số dư", value=f"`{data['balance']:,}` xu", inline=True)
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🎲 LỆNH BET
    # ==========================================
    @commands.command(name='bet')
    async def bet(self, ctx, amount: str = None):
        """🎲 Cược 50/50: !bet <số tiền>"""
        data = self.get_user_data(ctx.author.id)
        
        if not amount:
            await ctx.send("❌ Cách dùng: `!bet <số tiền>`")
            return
        
        if amount.lower() == 'all':
            bet = data['balance']
        else:
            try:
                bet = int(amount)
            except:
                await ctx.send("❌ Số tiền không hợp lệ!")
                return
        
        if bet <= 0 or bet > data['balance']:
            await ctx.send(f"❌ Số tiền phải từ 1 đến `{data['balance']:,}`!")
            return
        
        if random.random() < 0.5:
            data['balance'] += bet
            self.save_data()
            embed = discord.Embed(title="🎲 Cược 50/50", description=f"🎉 THẮNG! Nhận `{bet:,}` xu!", color=discord.Color.green())
        else:
            data['balance'] -= bet
            self.save_data()
            embed = discord.Embed(title="🎲 Cược 50/50", description=f"😢 THUA! Mất `{bet:,}` xu!", color=discord.Color.red())
        
        embed.add_field(name="💰 Số dư", value=f"`{data['balance']:,}` xu", inline=True)
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🎰 LỆNH SLOTS
    # ==========================================
    @commands.command(name='slots')
    async def slots(self, ctx, amount: str = None):
        """🎰 Máy đánh bạc: !slots <số tiền>"""
        data = self.get_user_data(ctx.author.id)
        
        if not amount:
            await ctx.send("❌ Cách dùng: `!slots <số tiền>`")
            return
        
        if amount.lower() == 'all':
            bet = data['balance']
        else:
            try:
                bet = int(amount)
            except:
                await ctx.send("❌ Số tiền không hợp lệ!")
                return
        
        if bet <= 0 or bet > data['balance']:
            await ctx.send(f"❌ Số tiền phải từ 1 đến `{data['balance']:,}`!")
            return
        
        emojis = ['🍒', '🍋', '🍊', '🍇', '💎', '7️⃣', '⭐', '🔔']
        slot1 = random.choice(emojis)
        slot2 = random.choice(emojis)
        slot3 = random.choice(emojis)
        
        if slot1 == slot2 == slot3:
            win_multiplier = 10
            result = "🎉 JACKPOT!"
        elif slot1 == slot2 or slot2 == slot3 or slot1 == slot3:
            win_multiplier = 3
            result = "✨ Cặp đôi!"
        else:
            win_multiplier = 0
            result = "❌ Thua!"
        
        if win_multiplier > 0:
            win_amount = bet * win_multiplier
            data['balance'] += win_amount - bet
            color = discord.Color.green()
        else:
            data['balance'] -= bet
            win_amount = 0
            color = discord.Color.red()
        
        self.save_data()
        
        embed = discord.Embed(title="🎰 Slots", description=f"```\n[{slot1}] [{slot2}] [{slot3}]\n```\n{result}", color=color)
        if win_amount > 0:
            embed.add_field(name="💰 Thắng", value=f"`{win_amount:,}` xu", inline=True)
        else:
            embed.add_field(name="💸 Mất", value=f"`{bet:,}` xu", inline=True)
        embed.add_field(name="💵 Số dư", value=f"`{data['balance']:,}` xu", inline=True)
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🪙 LỆNH COINFLIP
    # ==========================================
    @commands.command(name='coinflip', aliases=['cf'])
    async def coinflip(self, ctx, amount: str = None, choice: str = None):
        """🪙 Tung đồng xu: !coinflip <số tiền> <h/t>"""
        data = self.get_user_data(ctx.author.id)
        
        if not amount or not choice:
            await ctx.send("❌ Cách dùng: `!coinflip <số tiền> <h/t>`")
            return
        
        if amount.lower() == 'all':
            bet = data['balance']
        else:
            try:
                bet = int(amount)
            except:
                await ctx.send("❌ Số tiền không hợp lệ!")
                return
        
        if bet <= 0 or bet > data['balance']:
            await ctx.send(f"❌ Số tiền phải từ 1 đến `{data['balance']:,}`!")
            return
        
        choice = choice.lower()
        if choice not in ['h', 't', 'heads', 'tails']:
            await ctx.send("❌ Chọn `h` hoặc `t`!")
            return
        
        result = random.choice(['h', 't'])
        
        if choice.startswith(result):
            data['balance'] += bet
            self.save_data()
            result_text = "🪙 Mặt ngửa" if result == 'h' else "🪙 Mặt sấp"
            embed = discord.Embed(title="🪙 Coinflip", description=f"{result_text}\n🎉 THẮNG! Nhận `{bet:,}` xu!", color=discord.Color.green())
        else:
            data['balance'] -= bet
            self.save_data()
            result_text = "🪙 Mặt ngửa" if result == 'h' else "🪙 Mặt sấp"
            embed = discord.Embed(title="🪙 Coinflip", description=f"{result_text}\n😢 THUA! Mất `{bet:,}` xu!", color=discord.Color.red())
        
        embed.add_field(name="💰 Số dư", value=f"`{data['balance']:,}` xu", inline=True)
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🎴 LỆNH POKER (hybrid: !poker + /poker)
    # ==========================================
    
    RANK_ORDER = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
        '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }
    
    @classmethod
    def hand_rank(cls, hand):
        """Xếp hạng bài 2 lá: (2, rank) = Đôi | (1, cao, thấp) = Mậu thầu"""
        ranks = sorted((cls.RANK_ORDER[r] for r, _ in hand), reverse=True)
        if ranks[0] == ranks[1]:
            return (2, ranks[0])
        return (1, ranks[0], ranks[1])
    
    @staticmethod
    def new_deck():
        """Tạo bộ bài 52 lá đã xáo"""
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [(rank, suit) for suit in suits for rank in ranks]
        random.shuffle(deck)
        return deck
    
    @staticmethod
    def format_hand(hand):
        """Format bài poker"""
        return " ".join([f"{rank}{suit}" for rank, suit in hand])
    
    async def send_private(self, ctx, embed):
        """
        Gửi tin nhắn riêng tư:
        - Slash command (/poker) -> ephemeral (chỉ người dùng thấy)
        - Prefix command (!poker) -> gửi qua DM
        - Nếu DM thất bại -> KHÔNG đăng bài công khai (tránh lộ bài)
        """
        if getattr(ctx, 'interaction', None) is not None:
            await ctx.send(embed=embed, ephemeral=True)
            return
        try:
            await ctx.author.send(embed=embed)
            await ctx.send(f"📥 **{ctx.author.name}**, bài của bạn đã được gửi qua DM!")
        except discord.Forbidden:
            await ctx.send(
                f"🔒 **{ctx.author.name}**, tôi không gửi DM được cho bạn! "
                f"Hãy mở DM cho bot trong server này hoặc dùng `/poker check` để xem bài riêng tư."
            )
    
    @commands.hybrid_command(name='poker', description='🎴 Chơi poker với bạn bè')
    @app_commands.guild_only()
    @app_commands.describe(
        action='Hành động muốn thực hiện',
        amount='Số tiền cược (dùng cho start / raise)'
    )
    @app_commands.choices(action=[
        app_commands.Choice(name='start - Tạo bàn mới', value='start'),
        app_commands.Choice(name='join - Tham gia bàn', value='join'),
        app_commands.Choice(name='check - Xem bài của bạn', value='check'),
        app_commands.Choice(name='call - Theo cược', value='call'),
        app_commands.Choice(name='raise - Tố thêm', value='raise'),
        app_commands.Choice(name='fold - Bỏ bài', value='fold'),
        app_commands.Choice(name='showdown - Lật bài phân định thắng thua', value='showdown'),
        app_commands.Choice(name='end - Host giải tán bàn (hoàn tiền)', value='end'),
    ])
    async def poker(self, ctx, action: str = None, amount: int = None):
        """🎴 Poker multiplayer
        
        Cách dùng:
        `!poker start <số tiền>` - Tạo bàn poker
        `!poker join` - Tham gia bàn
        `!poker check` - Xem bài (riêng tư: ephemeral/DM)
        `!poker call` - Theo cược
        `!poker raise <số tiền>` - Tố thêm
        `!poker fold` - Bỏ bài
        `!poker showdown` - Lật bài, người mạnh nhất ăn pot
        `!poker end` - Host giải tán bàn và hoàn tiền
        """
        
        if not action:
            await ctx.send(
                "🎴 **Poker Commands**\n"
                f"`{ctx.prefix}poker start <tiền>` - Tạo bàn\n"
                f"`{ctx.prefix}poker join` - Tham gia\n"
                f"`{ctx.prefix}poker check` - Xem bài (riêng tư)\n"
                f"`{ctx.prefix}poker call` - Theo cược\n"
                f"`{ctx.prefix}poker raise <tiền>` - Tố thêm\n"
                f"`{ctx.prefix}poker fold` - Bỏ bài\n"
                f"`{ctx.prefix}poker showdown` - Lật bài phân định thắng thua\n"
                f"`{ctx.prefix}poker end` - Host giải tán bàn (hoàn tiền)"
            )
            return
        
        action = action.lower()
        game = self.poker_games.get(ctx.guild.id)
        
        # ===== START =====
        if action == 'start':
            if amount is None or amount <= 0:
                await ctx.send("❌ Cách dùng: `!poker start <số tiền cược>`")
                return
            
            data = self.get_user_data(ctx.author.id)
            if amount > data['balance']:
                await ctx.send(f"❌ Bạn chỉ có `{data['balance']:,}` xu!")
                return
            
            if game:
                await ctx.send("❌ Đã có bàn poker trong server này! Dùng `!poker end` để giải tán.")
                return
            
            deck = self.new_deck()
            hand = [deck.pop(), deck.pop()]
            
            self.poker_games[ctx.guild.id] = {
                'host': ctx.author.id,
                'players': {ctx.author.id: {'bet': amount, 'hand': hand, 'folded': False}},
                'deck': deck,
                'pot': amount,
                'current_bet': amount,
                'active': True
            }
            
            data['balance'] -= amount
            self.save_data()
            
            embed = discord.Embed(
                title="🎴 Poker",
                description=(
                    f"**{ctx.author.name}** đã tạo bàn poker!\n"
                    f"Buy-in: `{amount:,}` xu\n\n"
                    f"Dùng `{ctx.prefix}poker join` để tham gia!"
                ),
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Host: {ctx.author.name} | Tối đa 6 người")
            await ctx.send(embed=embed)
            
        # ===== JOIN =====
        elif action == 'join':
            if not game or not game['active']:
                await ctx.send("❌ Không có bàn poker nào!")
                return
            
            if ctx.author.id in game['players']:
                await ctx.send("❌ Bạn đã trong bàn rồi!")
                return
            
            if len(game['players']) >= 6:
                await ctx.send("❌ Bàn đã đầy (tối đa 6 người)!")
                return
            
            data = self.get_user_data(ctx.author.id)
            buy_in = game['current_bet']
            if buy_in > data['balance']:
                await ctx.send(f"❌ Bạn cần `{buy_in:,}` xu để tham gia!")
                return
            
            data['balance'] -= buy_in
            hand = [game['deck'].pop(), game['deck'].pop()]
            game['players'][ctx.author.id] = {'bet': buy_in, 'hand': hand, 'folded': False}
            game['pot'] += buy_in
            self.save_data()
            
            embed = discord.Embed(
                title="🎴 Poker",
                description=f"**{ctx.author.name}** đã tham gia!",
                color=discord.Color.blue()
            )
            embed.add_field(name="💰 Pot", value=f"`{game['pot']:,}` xu", inline=True)
            embed.add_field(name="👥 Số người", value=f"`{len(game['players'])}/6`", inline=True)
            await ctx.send(embed=embed)
            
        # ===== CHECK (xem bài riêng tư) =====
        elif action == 'check':
            if not game or ctx.author.id not in game['players']:
                await ctx.send("❌ Bạn không trong bàn poker!")
                return
            
            player = game['players'][ctx.author.id]
            if player['folded']:
                await ctx.send("❌ Bạn đã bỏ bài!")
                return
            
            hand_text = self.format_hand(player['hand'])
            
            embed = discord.Embed(
                title="🎴 Bài của bạn",
                description=f"```\n{hand_text}\n```",
                color=discord.Color.gold()
            )
            embed.set_footer(text="🔒 Chỉ bạn thấy tin nhắn này!")
            
            await self.send_private(ctx, embed)
            
        # ===== FOLD =====
        elif action == 'fold':
            if not game or ctx.author.id not in game['players']:
                await ctx.send("❌ Bạn không trong bàn poker!")
                return
            
            game['players'][ctx.author.id]['folded'] = True
            await ctx.send(f"🙅 **{ctx.author.name}** đã bỏ bài!")
            
            # Nếu chỉ còn 1 người chưa bỏ -> người đó thắng cả pot
            alive = [uid for uid, p in game['players'].items() if not p['folded']]
            if len(alive) == 1:
                winner_id = alive[0]
                winnings = game['pot']
                self.get_user_data(winner_id)['balance'] += winnings
                self.save_data()
                del self.poker_games[ctx.guild.id]
                
                embed = discord.Embed(
                    title="🏆 Poker - Kết thúc",
                    description=f"<@{winner_id}> thắng vì là người cuối cùng chưa bỏ bài!",
                    color=discord.Color.gold()
                )
                embed.add_field(name="💰 Thắng", value=f"`{winnings:,}` xu", inline=True)
                await ctx.send(embed=embed)
            
        # ===== CALL =====
        elif action == 'call':
            if not game or ctx.author.id not in game['players']:
                await ctx.send("❌ Bạn không trong bàn poker!")
                return
            
            player = game['players'][ctx.author.id]
            if player['folded']:
                await ctx.send("❌ Bạn đã bỏ bài!")
                return
            
            extra = game['current_bet'] - player['bet']
            if extra > 0:
                data = self.get_user_data(ctx.author.id)
                pay = min(extra, data['balance'])
                data['balance'] -= pay
                player['bet'] += pay
                game['pot'] += pay
                self.save_data()
                await ctx.send(f"✅ **{ctx.author.name}** đã theo cược thêm `{pay:,}` xu! Pot: `{game['pot']:,}` xu")
            else:
                await ctx.send(f"✅ **{ctx.author.name}** đã check (đang ở mức cược cao nhất)!")
            
        # ===== RAISE =====
        elif action == 'raise':
            if not game or ctx.author.id not in game['players']:
                await ctx.send("❌ Bạn không trong bàn poker!")
                return
            
            player = game['players'][ctx.author.id]
            if player['folded']:
                await ctx.send("❌ Bạn đã bỏ bài!")
                return
            
            if amount is None or amount <= 0:
                await ctx.send("❌ Cách dùng: `!poker raise <số tiền>`")
                return
            
            data = self.get_user_data(ctx.author.id)
            if amount > data['balance']:
                await ctx.send(f"❌ Bạn chỉ có `{data['balance']:,}` xu!")
                return
            
            data['balance'] -= amount
            player['bet'] += amount
            game['pot'] += amount
            game['current_bet'] = max(game['current_bet'], player['bet'])
            self.save_data()
            
            await ctx.send(f"📈 **{ctx.author.name}** đã tố thêm `{amount:,}` xu! Pot: `{game['pot']:,}` xu")
            
        # ===== SHOWDOWN =====
        elif action == 'showdown':
            if not game:
                await ctx.send("❌ Không có bàn poker nào!")
                return
            
            alive = [(uid, p) for uid, p in game['players'].items() if not p['folded']]
            if len(alive) < 2:
                await ctx.send("❌ Cần ít nhất 2 người chưa bỏ bài để showdown!")
                return
            
            scored = sorted(alive, key=lambda up: self.hand_rank(up[1]['hand']), reverse=True)
            best_rank = self.hand_rank(scored[0][1]['hand'])
            winners = [up for up in scored if self.hand_rank(up[1]['hand']) == best_rank]
            
            pot = game['pot']
            share = pot // len(winners)
            
            winner_ids = {uid for uid, _ in winners}
            
            # Lật bài tất cả người chơi
            lines = []
            for uid, p in sorted(game['players'].items(), key=lambda kv: kv[1]['folded']):
                status = "🙅 Đã bỏ bài" if p['folded'] else f"`{self.format_hand(p['hand'])}`"
                marker = "👑" if uid in winner_ids else "▫️"
                lines.append(f"{marker} <@{uid}>: {status}")
            
            for uid, _ in winners:
                self.get_user_data(uid)['balance'] += share
            self.save_data()
            del self.poker_games[ctx.guild.id]
            
            win_names = ", ".join(f"<@{uid}>" for uid, _ in winners)
            result_text = "ĐÔI!" if best_rank[0] == 2 else "MẬU THẦU!"
            
            embed = discord.Embed(
                title="🎴 Poker - Showdown!",
                description="\n".join(lines),
                color=discord.Color.gold()
            )
            embed.add_field(name="🏆 Người thắng", value=win_names, inline=False)
            embed.add_field(name="🎖️ Bài mạnh nhất", value=result_text, inline=True)
            embed.add_field(name="💰 Giải thưởng", value=f"`{share:,}` xu mỗi người", inline=True)
            await ctx.send(embed=embed)
            
        # ===== END (host giải tán, hoàn tiền) =====
        elif action == 'end':
            if not game:
                await ctx.send("❌ Không có bàn poker nào!")
                return
            
            if ctx.author.id != game['host']:
                await ctx.send("❌ Chỉ host mới được giải tán bàn!")
                return
            
            refunded = []
            for uid, p in game['players'].items():
                self.get_user_data(uid)['balance'] += p['bet']
                refunded.append(p['bet'])
            self.save_data()
            del self.poker_games[ctx.guild.id]
            
            embed = discord.Embed(
                title="🚪 Poker - Đã giải tán bàn",
                description=f"**{ctx.author.name}** đã giải tán bàn. Hoàn lại tiền cho `{len(refunded)}` người chơi!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            
        else:
            await ctx.send("❌ Hành động không hợp lệ! Xem: `!poker`")
    
    # ==========================================
    # 🎲 LỆNH TÀI XỈU
    # ==========================================
    @commands.command(name='taixiu', aliases=['tx'])
    async def taixiu(self, ctx, choice: str = None, amount: str = None):
        """🎲 Tài Xỉu: !taixiu <tài/xỉu> <số tiền>"""
        
        if not choice or not amount:
            await ctx.send(
                "🎲 **Tài Xỉu**\n"
                "Cách dùng: `!taixiu <tài/xỉu> <số tiền>`\n"
                "• Tài: 11-17 điểm\n"
                "• Xỉu: 4-10 điểm"
            )
            return
        
        choice = choice.lower()
        if choice not in ['tài', 'xỉu', 'tai', 'xiu', 't', 'x']:
            await ctx.send("❌ Chọn `tài` hoặc `xỉu`!")
            return
        
        data = self.get_user_data(ctx.author.id)
        
        if amount.lower() == 'all':
            bet = data['balance']
        else:
            try:
                bet = int(amount)
            except:
                await ctx.send("❌ Số tiền không hợp lệ!")
                return
        
        if bet <= 0 or bet > data['balance']:
            await ctx.send(f"❌ Số tiền phải từ 1 đến `{data['balance']:,}`!")
            return
        
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        dice3 = random.randint(1, 6)
        total = dice1 + dice2 + dice3
        
        if total >= 11:
            result = 'tài'
            result_text = "TÀI"
        else:
            result = 'xỉu'
            result_text = "XỈU"
        
        user_choice = 'tài' if choice.startswith('t') else 'xỉu'
        
        if user_choice == result:
            win_amount = bet * 2
            data['balance'] += win_amount - bet
            self.save_data()
            win = True
        else:
            data['balance'] -= bet
            self.save_data()
            win = False
        
        dice_emoji = {1: '⚀', 2: '⚁', 3: '⚂', 4: '⚃', 5: '⚄', 6: '⚅'}
        
        if win:
            embed = discord.Embed(
                title="🎲 Tài Xỉu",
                description=f"```\n{dice_emoji[dice1]} {dice_emoji[dice2]} {dice_emoji[dice3]}\n```\nTổng: **{total}** → **{result_text}**\n🎉 THẮNG! Nhận `{win_amount:,}` xu!",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="🎲 Tài Xỉu",
                description=f"```\n{dice_emoji[dice1]} {dice_emoji[dice2]} {dice_emoji[dice3]}\n```\nTổng: **{total}** → **{result_text}**\n😢 THUA! Mất `{bet:,}` xu!",
                color=discord.Color.red()
            )
        
        embed.add_field(name="💰 Số dư", value=f"`{data['balance']:,}` xu", inline=True)
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🏦 LỆNH DEPOSIT
    # ==========================================
    @commands.command(name='deposit', aliases=['dep'])
    async def deposit(self, ctx, amount: str = None):
        """🏦 Gửi tiền vào ngân hàng"""
        data = self.get_user_data(ctx.author.id)
        
        if not amount:
            await ctx.send("❌ Cách dùng: `!deposit <số tiền>` hoặc `!deposit all`")
            return
        
        if amount.lower() == 'all':
            dep_amount = data['balance']
        else:
            try:
                dep_amount = int(amount)
            except:
                await ctx.send("❌ Số tiền không hợp lệ!")
                return
        
        if dep_amount <= 0 or dep_amount > data['balance']:
            await ctx.send(f"❌ Số tiền phải từ 1 đến `{data['balance']:,}`!")
            return
        
        data['balance'] -= dep_amount
        data['bank'] += dep_amount
        self.save_data()
        
        embed = discord.Embed(
            title="🏦 Đã gửi tiền",
            description=f"Đã gửi `{dep_amount:,}` xu vào ngân hàng!",
            color=discord.Color.green()
        )
        embed.add_field(name="💵 Tiền mặt", value=f"`{data['balance']:,}` xu", inline=True)
        embed.add_field(name="🏦 Ngân hàng", value=f"`{data['bank']:,}` xu", inline=True)
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🏧 LỆNH WITHDRAW
    # ==========================================
    @commands.command(name='withdraw', aliases=['with'])
    async def withdraw(self, ctx, amount: str = None):
        """🏧 Rút tiền từ ngân hàng"""
        data = self.get_user_data(ctx.author.id)
        
        if not amount:
            await ctx.send("❌ Cách dùng: `!withdraw <số tiền>` hoặc `!withdraw all`")
            return
        
        if amount.lower() == 'all':
            with_amount = data['bank']
        else:
            try:
                with_amount = int(amount)
            except:
                await ctx.send("❌ Số tiền không hợp lệ!")
                return
        
        if with_amount <= 0 or with_amount > data['bank']:
            await ctx.send(f"❌ Số tiền phải từ 1 đến `{data['bank']:,}`!")
            return
        
        data['bank'] -= with_amount
        data['balance'] += with_amount
        self.save_data()
        
        embed = discord.Embed(
            title="🏧 Đã rút tiền",
            description=f"Đã rút `{with_amount:,}` xu từ ngân hàng!",
            color=discord.Color.green()
        )
        embed.add_field(name="💵 Tiền mặt", value=f"`{data['balance']:,}` xu", inline=True)
        embed.add_field(name="🏦 Ngân hàng", value=f"`{data['bank']:,}` xu", inline=True)
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🎁 LỆNH GIVE
    # ==========================================
    @commands.command(name='give')
    async def give(self, ctx, member: discord.Member, amount: int):
        """🎁 Tặng tiền cho người khác"""
        if member == ctx.author:
            await ctx.send("❌ Không thể tặng tiền cho chính mình!")
            return
        
        if member.bot:
            await ctx.send("❌ Không thể tặng tiền cho bot!")
            return
        
        if amount <= 0:
            await ctx.send("❌ Số tiền phải lớn hơn 0!")
            return
        
        data = self.get_user_data(ctx.author.id)
        
        if amount > data['balance']:
            await ctx.send(f"❌ Bạn chỉ có `{data['balance']:,}` xu!")
            return
        
        data['balance'] -= amount
        target_data = self.get_user_data(member.id)
        target_data['balance'] += amount
        self.save_data()
        
        embed = discord.Embed(
            title="🎁 Đã tặng tiền",
            description=f"**{ctx.author.name}** đã tặng `{amount:,}` xu cho **{member.name}**!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🏆 LỆNH LEADERBOARD
    # ==========================================
    @commands.command(name='leaderboard', aliases=['top', 'lb'])
    async def leaderboard(self, ctx):
        """🏆 Xem bảng xếp hạng người giàu"""
        if not self.economy_data:
            await ctx.send("❌ Chưa có dữ liệu!")
            return
        
        sorted_users = sorted(
            self.economy_data.items(),
            key=lambda x: x[1]['balance'] + x[1]['bank'],
            reverse=True
        )[:10]
        
        embed = discord.Embed(
            title="🏆 Bảng xếp hạng người giàu",
            color=discord.Color.gold()
        )
        
        for i, (user_id, data) in enumerate(sorted_users, 1):
            total = data['balance'] + data['bank']
            user = self.bot.get_user(int(user_id))
            name = user.name if user else f"User {user_id}"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            embed.add_field(
                name=f"{medal} {name}",
                value=f"`{total:,}` xu",
                inline=False
            )
        
        await ctx.send(embed=embed)

# ==========================================
# 📌 SETUP - Load cog
# ==========================================
async def setup(bot):
    await bot.add_cog(Economy(bot))