"""
COGS: Fun Commands
Lệnh giải trí: roll, flip, 8ball, meme, rps, joke, fact, quote, cat, dog, fox, anime, hug, kiss, slap, pat, kill, ship, rate, say, reverse, mock, clap, emojify
"""

import discord
from discord.ext import commands
import random
import aiohttp
import asyncio
from typing import Optional

class Fun(commands.Cog):
    """Lệnh giải trí cho bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.session = None
    
    def get_color(self, color_name='primary'):
        """Lấy màu từ config chung của bot"""
        color_hex = self.bot.config.get(f'colors.{color_name}', '#7289DA')
        return discord.Color(int(color_hex.replace('#', ''), 16))
    
    async def get_session(self):
        """Lấy hoặc tạo session mới"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        """Đóng session khi bot tắt"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    def cog_unload(self):
        """Khi cog bị unload, đóng session"""
        asyncio.create_task(self.close_session())
    
    # ==========================================
    # 🎲 LỆNH ROLL
    # ==========================================
    @commands.command(name='roll')
    async def roll(self, ctx, dice: str = "1d6"):
        """🎲 Lắc xí ngầu: !roll 2d6"""
        try:
            rolls, limit = map(int, dice.split('d'))
            
            if rolls > 100:
                await ctx.send("❌ Chỉ được lắc tối đa 100 xí ngầu!")
                return
            
            results = [random.randint(1, limit) for _ in range(rolls)]
            total = sum(results)
            
            embed = discord.Embed(
                title="🎲 Kết quả xí ngầu",
                color=self.get_color('primary')
            )
            embed.add_field(
                name=f"🎯 {rolls} xí ngầu {limit} mặt",
                value=" + ".join(map(str, results[:20])),
                inline=False
            )
            embed.add_field(name="📊 Tổng", value=f"**{total}**", inline=True)
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}")
            
            await ctx.send(embed=embed)
            
        except ValueError:
            await ctx.send("❌ Sai cú pháp! Dùng: `!roll 2d6`")
    
    # ==========================================
    # 🪙 LỆNH FLIP
    # ==========================================
    @commands.command(name='flip')
    async def flip(self, ctx):
        """🪙 Tung đồng xu"""
        result = random.choice(['heads', 'tails'])
        emoji = '🦅' if result == 'heads' else '🪙'
        
        embed = discord.Embed(
            title="🪙 Tung đồng xu!",
            color=self.get_color('warning')
        )
        embed.add_field(name="Kết quả", value=f"{emoji} **{result.upper()}**", inline=False)
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🎱 LỆNH 8BALL
    # ==========================================
    @commands.command(name='8ball')
    async def eight_ball(self, ctx, *, question):
        """🎱 Hỏi bóng ma thuật"""
        responses = [
            "Chắc chắn rồi! 🟢", "Chắc chắn! 🟢",
            "Có vẻ như vậy 🟡", "Rất có thể 🟡",
            "Hỏi lại sau 🟠", "Không thể trả lời 🟠",
            "Đừng mong chờ 🔴", "Chắc chắn là không 🔴"
        ]
        
        embed = discord.Embed(
            title="🎱 Bóng ma thuật",
            color=self.get_color('primary')
        )
        embed.add_field(name="❓ Câu hỏi", value=f"`{question}`", inline=False)
        embed.add_field(name="🔮 Trả lời", value=random.choice(responses), inline=False)
        embed.set_footer(text=f"Hỏi bởi {ctx.author.name}")
        
        await ctx.send(embed=embed)
    
    # ==========================================
    # 📸 LỆNH MEME
    # ==========================================
    @commands.command(name='meme')
    async def meme(self, ctx, subreddit: Optional[str] = None):
        """🖼️ Lấy meme ngẫu nhiên từ Reddit"""
        
        subreddits = {
            'memes': 'Memes tổng hợp',
            'dankmemes': 'Dank Memes',
            'wholesomememes': 'Meme tích cực',
            'ProgrammerHumor': 'Meme lập trình viên',
            'me_irl': 'Me irl',
            'funny': 'Hài hước'
        }
        
        if subreddit:
            subreddit = subreddit.lower()
            if subreddit not in subreddits:
                embed = discord.Embed(
                    title="❌ Subreddit không hợp lệ!",
                    description="Chọn một trong các subreddit sau:",
                    color=self.get_color('error')
                )
                sub_list = "\n".join([f"• `{key}` - {value}" for key, value in list(subreddits.items())])
                embed.add_field(name="📋 Danh sách", value=sub_list, inline=False)
                await ctx.send(embed=embed)
                return
        else:
            subreddit = random.choice(list(subreddits.keys()))
        
        loading_msg = await ctx.send(f"🔄 Đang tìm meme từ **r/{subreddit}**...")
        
        session = None
        
        try:
            session = aiohttp.ClientSession()
            api_url = f"https://meme-api.com/gimme/{subreddit}"
            
            async with session.get(api_url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    embed = discord.Embed(
                        title=f"🖼️ Meme từ r/{subreddit}",
                        url=data.get('postLink', ''),
                        color=discord.Color.random()
                    )
                    
                    if data.get('title'):
                        embed.description = f"**{data.get('title')}**"
                    
                    embed.set_image(url=data.get('url', ''))
                    embed.set_footer(
                        text=f"👍 {data.get('ups', 0):,} | 💬 {data.get('comments', 0):,}"
                    )
                    
                    await loading_msg.delete()
                    await ctx.send(embed=embed)
                    
                else:
                    await loading_msg.delete()
                    await self._send_fallback_meme(ctx)
                    
        except Exception:
            await loading_msg.delete()
            await self._send_fallback_meme(ctx)
            
        finally:
            if session and not session.closed:
                await session.close()
    
    async def _send_fallback_meme(self, ctx):
        """Gửi meme dự phòng"""
        fallback_memes = [
            "https://i.imgur.com/5P4P5YF.png",
            "https://i.imgur.com/6M7M8YG.jpg",
            "https://i.imgur.com/7N8N9ZH.png",
            "https://i.imgur.com/8O9OAI.png"
        ]
        
        embed = discord.Embed(
            title="🖼️ Meme dự phòng",
            description="⚠️ API meme tạm thời không hoạt động",
            color=self.get_color('warning')
        )
        embed.set_image(url=random.choice(fallback_memes))
        
        await ctx.send(embed=embed)
    
    # ==========================================
    # ✊🖐️✌️ LỆNH RPS
    # ==========================================
    @commands.command(name='rps')
    async def rps(self, ctx, choice: str):
        """✊🖐️✌️ Oán tù tì với bot"""
        choices = {
            'rock': '🪨 Đá',
            'paper': '📄 Giấy',
            'scissors': '✂️ Kéo'
        }
        
        choice = choice.lower()
        if choice not in choices:
            await ctx.send("❌ Chọn: `rock`, `paper`, hoặc `scissors`")
            return
        
        bot_choice = random.choice(list(choices.keys()))
        
        if choice == bot_choice:
            result = "🤝 Hòa!"
            color = self.get_color('warning')
        elif (choice == 'rock' and bot_choice == 'scissors') or \
             (choice == 'paper' and bot_choice == 'rock') or \
             (choice == 'scissors' and bot_choice == 'paper'):
            result = "🎉 Bạn thắng!"
            color = self.get_color('success')
        else:
            result = "😢 Bot thắng!"
            color = self.get_color('error')
        
        embed = discord.Embed(title="✊🖐️✌️ Oán tù tì", color=color)
        embed.add_field(name="👤 Bạn", value=choices[choice], inline=True)
        embed.add_field(name="🤖 Bot", value=choices[bot_choice], inline=True)
        embed.add_field(name="📊 Kết quả", value=f"**{result}**", inline=False)
        
        await ctx.send(embed=embed)
    
    # ==========================================
    # 😂 LỆNH JOKE
    # ==========================================
    @commands.command(name='joke')
    async def joke(self, ctx):
        """😂 Lấy joke ngẫu nhiên"""
        jokes = [
            "Tại sao lập trình viên thích dark mode? Vì light mode không có bug... à nhầm, vì họ sợ ánh sáng!",
            "Có 10 loại người: người hiểu nhị phân và người không hiểu nhị phân.",
            "Tại sao Java developer đeo kính? Vì họ không C# (see sharp)!",
            "HTML là gì? Là ngôn ngữ để làm web... đúng không?",
            "Tại sao programmer không bao giờ đói? Vì họ có nhiều cookies!",
            "Debug là gì? Là việc tìm kiếm kim trong bãi rác.",
            "Tại sao code của tôi không chạy? Vì nó thích ngủ!",
            "Selenium là gì? Là công cụ để test bug... nhưng bug vẫn tồn tại!"
        ]
        
        embed = discord.Embed(
            title="😂 Joke",
            description=random.choice(jokes),
            color=self.get_color('primary')
        )
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🧠 LỆNH FACT
    # ==========================================
    @commands.command(name='fact')
    async def fact(self, ctx):
        """🧠 Sự thật thú vị"""
        facts = [
            "Ốc sên có thể ngủ 3 năm liên tục!",
            "Mật ong không bao giờ hỏng!",
            "Bạch tuộc có 3 trái tim!",
            "Con người có 99.9% DNA giống nhau!",
            "Sét đánh nhanh hơn âm thanh!",
            "Chuột túi không thể nhảy lùi!",
            "Cá heo ngủ với một mắt mở!",
            "Kim tự tháp được xây dựng từ 2.3 triệu khối đá!"
        ]
        
        embed = discord.Embed(
            title="🧠 Sự thật thú vị",
            description=random.choice(facts),
            color=self.get_color('info')
        )
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🐱 LỆNH CAT
    # ==========================================
    @commands.command(name='cat')
    async def cat(self, ctx):
        """🐱 Ảnh mèo ngẫu nhiên"""
        session = None
        try:
            session = aiohttp.ClientSession()
            async with session.get("https://api.thecatapi.com/v1/images/search", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        embed = discord.Embed(
                            title="🐱 Mèo đây!",
                            color=self.get_color('primary')
                        )
                        embed.set_image(url=data[0]['url'])
                        await ctx.send(embed=embed)
                        return
        except:
            pass
        finally:
            if session and not session.closed:
                await session.close()
        
        await ctx.send("❌ Không lấy được ảnh mèo!")
    
    # ==========================================
    # 🐶 LỆNH DOG
    # ==========================================
    @commands.command(name='dog')
    async def dog(self, ctx):
        """🐶 Ảnh chó ngẫu nhiên"""
        session = None
        try:
            session = aiohttp.ClientSession()
            async with session.get("https://api.thedogapi.com/v1/images/search", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        embed = discord.Embed(
                            title="🐶 Chó đây!",
                            color=self.get_color('primary')
                        )
                        embed.set_image(url=data[0]['url'])
                        await ctx.send(embed=embed)
                        return
        except:
            pass
        finally:
            if session and not session.closed:
                await session.close()
        
        await ctx.send("❌ Không lấy được ảnh chó!")
    
    # ==========================================
    # 🦊 LỆNH FOX
    # ==========================================
    @commands.command(name='fox')
    async def fox(self, ctx):
        """🦊 Ảnh cáo ngẫu nhiên"""
        session = None
        try:
            session = aiohttp.ClientSession()
            async with session.get("https://randomfox.ca/floof/", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    embed = discord.Embed(
                        title="🦊 Cáo đây!",
                        color=self.get_color('primary')
                    )
                    embed.set_image(url=data['image'])
                    await ctx.send(embed=embed)
                    return
        except:
            pass
        finally:
            if session and not session.closed:
                await session.close()
        
        await ctx.send("❌ Không lấy được ảnh cáo!")
    
    # ==========================================
    # 🎭 LỆNH HUG
    # ==========================================
    @commands.command(name='hug')
    async def hug(self, ctx, member: discord.Member = None):
        """🤗 Ôm ai đó"""
        if not member:
            member = ctx.author
        
        hugs = [
            "https://i.imgur.com/r9aU2xv.gif",
            "https://i.imgur.com/4zWv8uK.gif",
            "https://i.imgur.com/3ZvL7yH.gif"
        ]
        
        embed = discord.Embed(
            title="🤗 Ôm!",
            description=f"**{ctx.author.name}** ôm **{member.name}**!",
            color=self.get_color('primary')
        )
        embed.set_image(url=random.choice(hugs))
        await ctx.send(embed=embed)
    
    # ==========================================
    # 💋 LỆNH KISS
    # ==========================================
    @commands.command(name='kiss')
    async def kiss(self, ctx, member: discord.Member = None):
        """💋 Hôn ai đó"""
        if not member:
            member = ctx.author
        
        kisses = [
            "https://i.imgur.com/3ZvL7yH.gif",
            "https://i.imgur.com/4zWv8uK.gif",
            "https://i.imgur.com/r9aU2xv.gif"
        ]
        
        embed = discord.Embed(
            title="💋 Hôn!",
            description=f"**{ctx.author.name}** hôn **{member.name}**!",
            color=self.get_color('primary')
        )
        embed.set_image(url=random.choice(kisses))
        await ctx.send(embed=embed)
    
    # ==========================================
    # 👋 LỆNH SLAP
    # ==========================================
    @commands.command(name='slap')
    async def slap(self, ctx, member: discord.Member = None):
        """👋 Tát ai đó"""
        if not member:
            member = ctx.author
        
        embed = discord.Embed(
            title="👋 Tát!",
            description=f"**{ctx.author.name}** tát **{member.name}**!",
            color=self.get_color('error')
        )
        await ctx.send(embed=embed)
    
    # ==========================================
    # 💀 LỆNH KILL
    # ==========================================
    @commands.command(name='kill')
    async def kill(self, ctx, member: discord.Member = None):
        """💀 Kill ai đó"""
        if not member:
            member = ctx.author
        
        kills = [
            f"**{ctx.author.name}** đã kill **{member.name}** bằng cây kiếm huyền thoại! ⚔️",
            f"**{ctx.author.name}** đã kill **{member.name}** bằng cách nhìn! 👀",
            f"**{ctx.author.name}** đã kill **{member.name}** vì tội quá đẹp trai! 😎",
            f"**{member.name}** đã chết vì cười! 😂"
        ]
        
        embed = discord.Embed(
            title="💀 Kill!",
            description=random.choice(kills),
            color=self.get_color('error')
        )
        await ctx.send(embed=embed)
    
    # ==========================================
    # 💑 LỆNH SHIP
    # ==========================================
    @commands.command(name='ship')
    async def ship(self, ctx, member1: discord.Member = None, member2: discord.Member = None):
        """💑 Ship 2 người"""
        if not member1:
            member1 = ctx.author
        if not member2:
            member2 = ctx.author
        
        percentage = random.randint(0, 100)
        
        if percentage < 20:
            result = "💔 Không hợp nhau!"
            color = self.get_color('error')
        elif percentage < 50:
            result = "😅 Có thể làm bạn!"
            color = self.get_color('warning')
        elif percentage < 80:
            result = "💕 Khá hợp nhau!"
            color = self.get_color('primary')
        else:
            result = "💑 Định mệnh! Sinh ra để dành cho nhau!"
            color = self.get_color('success')
        
        embed = discord.Embed(
            title="💑 Ship",
            description=f"**{member1.name}** ❤️ **{member2.name}**",
            color=color
        )
        embed.add_field(name="💕 Tỷ lệ hợp nhau", value=f"`{percentage}%`", inline=True)
        embed.add_field(name="📊 Kết quả", value=result, inline=False)
        
        await ctx.send(embed=embed)
    
    # ==========================================
    # 📊 LỆNH RATE
    # ==========================================
    @commands.command(name='rate')
    async def rate(self, ctx, *, thing: str = None):
        """📊 Đánh giá thứ gì đó"""
        if not thing:
            thing = ctx.author.name
        
        rating = random.randint(0, 10)
        
        emojis = ['💩', '😢', '😕', '😐', '🙂', '😊', '😄', '😁', '🤩', '😍', '👑']
        
        embed = discord.Embed(
            title="📊 Đánh giá",
            description=f"**{thing}**: `{rating}/10` {emojis[rating]}",
            color=self.get_color('primary')
        )
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🔤 LỆNH SAY
    # ==========================================
    @commands.command(name='say')
    async def say(self, ctx, *, message: str):
        """🔤 Bot nói theo bạn"""
        await ctx.message.delete()
        await ctx.send(message)
    
    # ==========================================
    # 🔁 LỆNH REVERSE
    # ==========================================
    @commands.command(name='reverse')
    async def reverse(self, ctx, *, text: str):
        """🔁 Đảo ngược chữ"""
        reversed_text = text[::-1]
        
        embed = discord.Embed(
            title="🔁 Đảo ngược",
            description=f"```\n{reversed_text}\n```",
            color=self.get_color('primary')
        )
        await ctx.send(embed=embed)
    
    # ==========================================
    # 🤡 LỆNH MOCK
    # ==========================================
    @commands.command(name='mock')
    async def mock(self, ctx, *, text: str):
        """🤡 Chữ kiểu mỉa mai: tHaY đỔi ChỮ"""
        result = ''.join(
            c.upper() if i % 2 == 0 else c.lower()
            for i, c in enumerate(text)
        )
        
        await ctx.send(f"🤡 {result}")
    
    # ==========================================
    # 👏 LỆNH CLAP
    # ==========================================
    @commands.command(name='clap')
    async def clap(self, ctx, *, text: str):
        """👏 Thêm vỗ tay giữa các chữ"""
        result = " 👏 ".join(text.split())
        
        await ctx.send(f"👏 {result} 👏")
    
    # ==========================================
    # 😀 LỆNH EMOJIFY
    # ==========================================
    @commands.command(name='emojify')
    async def emojify(self, ctx, *, text: str):
        """😀 Chuyển chữ thành emoji"""
        emoji_map = {
            'a': '🇦', 'b': '🇧', 'c': '🇨', 'd': '🇩', 'e': '🇪',
            'f': '🇫', 'g': '🇬', 'h': '🇭', 'i': '🇮', 'j': '🇯',
            'k': '🇰', 'l': '🇱', 'm': '🇲', 'n': '🇳', 'o': '🇴',
            'p': '🇵', 'q': '🇶', 'r': '🇷', 's': '🇸', 't': '🇹',
            'u': '🇺', 'v': '🇻', 'w': '🇼', 'x': '🇽', 'y': '🇾',
            'z': '🇿', '0': '0️⃣', '1': '1️⃣', '2': '2️⃣', '3': '3️⃣',
            '4': '4️⃣', '5': '5️⃣', '6': '6️⃣', '7': '7️⃣', '8': '8️⃣',
            '9': '9️⃣', ' ': '⬜'
        }
        
        result = ' '.join(emoji_map.get(c.lower(), c) for c in text)
        
        await ctx.send(result)

async def setup(bot):
    await bot.add_cog(Fun(bot))