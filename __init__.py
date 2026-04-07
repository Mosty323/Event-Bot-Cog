from .gamingevent import GamingEvent

async def setup(bot):
    cog = GamingEvent(bot)
    await bot.add_cog(cog)
