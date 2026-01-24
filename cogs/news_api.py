import os
import json
import asyncio
from datetime import datetime, time, timedelta, timezone

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

STATE_PATH = "./data/news_state.json"


class NewsAPI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tz = timezone(timedelta(hours=-8))
        self.channel_id = int(os.getenv("CHANNEL_ID", "0"))
        self.page_size = int(os.getenv("NEWS_PAGE_SIZE", "5"))

        os.makedirs("./data", exist_ok=True)
        self.state = self._load_state()
        self.task = self.bot.loop.create_task(self._runner())

    def cog_unload(self):
        if self.task and not self.task.done():
            self.task.cancel()

    def _load_state(self):
        if os.path.exists(STATE_PATH):
            try:
                with open(STATE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"last_post_date": None}

    def _save_state(self):
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def _next_8am(self):
        now = datetime.now(self.tz)
        target = datetime.combine(now.date(), time(8, 0), tzinfo=self.tz)
        if now >= target:
            target += timedelta(days=1)
        return target

    async def _fetch_news(self):
        api_key = os.getenv("NEWSDATA_API_KEY", "")
        if not api_key:
            raise RuntimeError("NEWSDATA_API_KEY missing")

        url = "https://newsdata.io/api/1/latest"
        params = {
            "apikey": api_key,
            "country": "us,gb,cn",
            "language": "en",
            "category": "technology",
            "timezone": "america/los_angeles",
            "prioritydomain": "top",
            "image": 0,
            "video": 0,
            "domainurl": "bbc.com",
            "removeduplicate": 0
        }

        timeout = aiohttp.ClientTimeout(total=25)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as r:
                data = await r.json()
                if r.status != 200:
                    raise RuntimeError(f"{r.status}: {data}")
                return data.get("results", [])

    async def _post_news(self, channel):
        if not self.channel_id:
            raise RuntimeError("CHANNEL_ID missing")

        articles = await self._fetch_news()
        if not articles:
            await channel.send("No headlines found.")
            return

        await channel.send(
            f"📰 Daily headlines — {datetime.now(self.tz).strftime('%a %b %d, %Y')} (8:00 AM Seattle time)"
        )

        for a in articles[: self.page_size]:
            e = discord.Embed(
                title=a.get("title", "Headline"),
                url=a.get("link", ""),
                description=a.get("description", "")
            )
            e.set_footer(text=a.get("source_id", "News"))
            if a.get("image_url"):
                e.set_image(url=a["image_url"])
            await channel.send(embed=e)

    async def _runner(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            next_run = self._next_8am()
            sleep_seconds = max(1, int((next_run - datetime.now(self.tz)).total_seconds()))
            await asyncio.sleep(sleep_seconds)

            today = datetime.now(self.tz).date().isoformat()
            if self.state.get("last_post_date") == today:
                continue

            try:
                ch = self.bot.get_channel(self.channel_id)
                if ch is None:
                    ch = await self.bot.fetch_channel(self.channel_id)
                await self._post_news(ch)
                self.state["last_post_date"] = today
                self._save_state()
            except Exception as e:
                print(f"[news_api] {e}")

    @commands.command(name="news_test")
    async def news_test(self, ctx):
        try:
            await ctx.send("testing...")
            await self._post_news(ctx.channel)
            await ctx.send("done")
        except Exception as e:
            await ctx.send(f"{type(e).__name__}: {e}")
            raise


async def setup(bot: commands.Bot):
    await bot.add_cog(NewsAPI(bot))