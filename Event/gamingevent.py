import random
import asyncio
import discord
from redbot.core import commands
from discord import app_commands
from discord.ui import View, Button, Select, Modal, TextInput
from discord import ButtonStyle, TextStyle


COLORS = {
    "purple": 0x7C5CBF,
    "blue":   0x4A90D9,
    "green":  0x43B581,
    "gold":   0xF0B429,
    "red":    0xED4245,
    "pink":   0xE91E8C,
    "cyan":   0x00BCD4,
}

DEFAULT_GAMES = [
    "Lethal Company", "Phasmophobia", "Among Us", "Fortnite",
    "Minecraft", "Deep Rock Galactic", "Left 4 Dead 2", "Valheim",
]

DEFAULT_CHALLENGES = [
    {"text": "Stirb in dieser Runde kein einziges Mal", "difficulty": "⭐⭐⭐", "label": "Schwer"},
    {"text": "Benutze nur das günstigste Item das du findest", "difficulty": "⭐⭐", "label": "Mittel"},
    {"text": "Rede die ganze Runde nur in Großbuchstaben im Voice", "difficulty": "⭐", "label": "Leicht"},
    {"text": "Du darfst nicht weglaufen — nur vorwärts gegen Gegner", "difficulty": "⭐⭐⭐", "label": "Schwer"},
    {"text": "Kauf am Ende jeder Runde das teuerste Item im Shop", "difficulty": "⭐⭐", "label": "Mittel"},
    {"text": "Mach jeden Raum leer bevor du weitergehst", "difficulty": "⭐⭐", "label": "Mittel"},
    {"text": "Du musst immer der letzte sein der das Schiff betritt", "difficulty": "⭐⭐⭐", "label": "Schwer"},
    {"text": "Kein Kommunizieren außer mit Emojis", "difficulty": "⭐", "label": "Leicht"},
    {"text": "Du darfst kein Equipment kaufen — nur Funde benutzen", "difficulty": "⭐⭐⭐", "label": "Schwer"},
    {"text": "Zähle nach jeder Aktion laut von 5 runter", "difficulty": "⭐", "label": "Leicht"},
]


def diff_color(label: str) -> int:
    if label == "Leicht":
        return COLORS["green"]
    if label == "Mittel":
        return COLORS["gold"]
    return COLORS["red"]


def diff_emoji(label: str) -> str:
    if label == "Leicht":
        return "🟢"
    if label == "Mittel":
        return "🟡"
    return "🔴"


def build_challenge_embed(c: dict) -> discord.Embed:
    embed = discord.Embed(color=diff_color(c["label"]))
    embed.set_author(name="🎯  Gaming Event Bot  •  Challenge")
    embed.title = c["text"]
    embed.add_field(
        name="Schwierigkeit",
        value=f"{diff_emoji(c['label'])}  {c['difficulty']}  **{c['label']}**",
        inline=True,
    )
    embed.set_footer(text="Viel Erfolg!  •  Gaming Event Bot")
    return embed


def build_random_game_embed(game: str, games: list) -> discord.Embed:
    embed = discord.Embed(color=COLORS["cyan"])
    embed.set_author(name="🎮  Gaming Event Bot  •  Zufälliges Spiel")
    embed.title = game
    embed.description = "> Heute Nacht wird gezockt! Alle einloggen."
    embed.add_field(name="📚 Spiele in der Liste", value=str(len(games)), inline=True)
    embed.set_footer(text="Kein Bock? /randomgame nochmal!  •  Gaming Event Bot")
    return embed


def build_event_embed(title: str, user: discord.User, games: list, challenges: list) -> discord.Embed:
    embed = discord.Embed(color=COLORS["pink"])
    embed.set_author(name="🚀  Gaming Event Bot  •  Event Start")
    embed.title = title or "Das Event startet jetzt!"
    embed.description = (
        "**Alle einloggen!** Das Gaming Event beginnt jetzt.\n\n"
        "╔══════════════════════════════╗\n"
        "║  `/challenge` — Deine Challenge\n"
        "║  `/randomgame` — Spiel auswählen\n"
        "║  `/umfrage` — Wer ist dabei?\n"
        "╚══════════════════════════════╝"
    )
    embed.add_field(name="🕹️ Spiele", value=f"{len(games)} verfügbar", inline=True)
    embed.add_field(name="🎯 Challenges", value=f"{len(challenges)} verfügbar", inline=True)
    embed.set_footer(text=f"Gestartet von {user.name}  •  Gaming Event Bot")
    return embed


def build_poll_embed(frage: str, user: discord.User) -> discord.Embed:
    embed = discord.Embed(color=COLORS["purple"])
    embed.set_author(name="📅  Gaming Event Bot  •  Umfrage")
    embed.title = frage
    embed.description = (
        "✅  **Dabei** — reagiere mit ✅\n"
        "❌  **Nicht dabei** — reagiere mit ❌\n"
        "❓  **Vielleicht** — reagiere mit ❓"
    )
    embed.set_footer(text=f"Umfrage von {user.name}  •  Gaming Event Bot")
    return embed


# ── Modals ────────────────────────────────────────────────────────────────────

class GameAddModal(Modal, title="🕹️  Spiel hinzufügen"):
    game_name = TextInput(
        label="Name des Spiels",
        placeholder="z.B. Rust, Sea of Thieves, ...",
        required=True,
        max_length=100,
        style=TextStyle.short,
    )

    def __init__(self, cog_ref):
        super().__init__()
        self.cog = cog_ref

    async def on_submit(self, interaction: discord.Interaction):
        name = self.game_name.value.strip()
        if any(g.lower() == name.lower() for g in self.cog.games):
            embed = discord.Embed(color=COLORS["red"], title="❌  Bereits vorhanden")
            embed.description = f"**{name}** ist schon in der Liste!"
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.cog.games.append(name)
        embed = discord.Embed(color=COLORS["green"])
        embed.set_author(name="✅  Spiel hinzugefügt")
        embed.title = name
        embed.description = "Wurde erfolgreich zur Spiele-Liste hinzugefügt."
        embed.set_footer(text=f"{len(self.cog.games)} Spiele insgesamt")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ChallengeAddModal(Modal, title="🎯  Challenge hinzufügen"):
    challenge_text = TextInput(
        label="Challenge-Beschreibung",
        placeholder="Beschreibe die Challenge...",
        required=True,
        max_length=300,
        style=TextStyle.paragraph,
    )
    challenge_diff = TextInput(
        label="Schwierigkeit: Leicht / Mittel / Schwer",
        placeholder="Mittel",
        required=False,
        max_length=10,
        style=TextStyle.short,
    )

    def __init__(self, cog_ref):
        super().__init__()
        self.cog = cog_ref

    async def on_submit(self, interaction: discord.Interaction):
        text = self.challenge_text.value.strip()
        raw_diff = (self.challenge_diff.value or "Mittel").strip()
        diff_map = {
            "leicht": {"difficulty": "⭐", "label": "Leicht"},
            "mittel": {"difficulty": "⭐⭐", "label": "Mittel"},
            "schwer": {"difficulty": "⭐⭐⭐", "label": "Schwer"},
        }
        diff = diff_map.get(raw_diff.lower(), diff_map["mittel"])
        self.cog.challenges.append({"text": text, **diff})
        embed = discord.Embed(color=COLORS["green"])
        embed.set_author(name="✅  Challenge hinzugefügt")
        embed.title = text
        embed.add_field(
            name="Schwierigkeit",
            value=f"{diff_emoji(diff['label'])}  {diff['difficulty']}  **{diff['label']}**",
        )
        embed.set_footer(text=f"{len(self.cog.challenges)} Challenges insgesamt")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Views ─────────────────────────────────────────────────────────────────────

class GameListView(View):
    def __init__(self, cog_ref, page: int = 0):
        super().__init__(timeout=120)
        self.cog = cog_ref
        self.page = page
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        page_size = 10
        total_pages = max(1, -(-len(self.cog.games) // page_size))

        add_btn = Button(label="Spiel hinzufügen", emoji="➕", style=ButtonStyle.success)
        add_btn.callback = self.add_callback
        self.add_item(add_btn)

        rem_btn = Button(
            label="Spiel entfernen", emoji="🗑️", style=ButtonStyle.danger,
            disabled=len(self.cog.games) == 0,
        )
        rem_btn.callback = self.remove_callback
        self.add_item(rem_btn)

        if total_pages > 1:
            prev_btn = Button(label="Zurück", emoji="◀️", style=ButtonStyle.secondary,
                              disabled=self.page == 0)
            prev_btn.callback = self.prev_callback
            self.add_item(prev_btn)

            next_btn = Button(label="Weiter", emoji="▶️", style=ButtonStyle.secondary,
                              disabled=self.page >= total_pages - 1)
            next_btn.callback = self.next_callback
            self.add_item(next_btn)

    async def add_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(GameAddModal(self.cog))

    async def remove_callback(self, interaction: discord.Interaction):
        view, embed = build_game_remove_view(self.cog, self.page)
        if view is None:
            return await interaction.response.send_message("❌ Keine Spiele zum Entfernen.", ephemeral=True)
        await interaction.response.edit_message(embed=embed, view=view)

    async def prev_callback(self, interaction: discord.Interaction):
        self.page = max(0, self.page - 1)
        embed, view = build_game_list_message(self.cog, self.page)
        await interaction.response.edit_message(embed=embed, view=view)

    async def next_callback(self, interaction: discord.Interaction):
        page_size = 10
        total_pages = max(1, -(-len(self.cog.games) // page_size))
        self.page = min(total_pages - 1, self.page + 1)
        embed, view = build_game_list_message(self.cog, self.page)
        await interaction.response.edit_message(embed=embed, view=view)


class GameRemoveView(View):
    def __init__(self, cog_ref, page: int = 0):
        super().__init__(timeout=120)
        self.cog = cog_ref
        self.page = page

        page_size = 10
        start = page * page_size
        slice_ = self.cog.games[start:start + page_size]

        options = [
            discord.SelectOption(
                label=g, value=str(start + i),
                description=f"Eintrag #{start + i + 1} aus der Liste entfernen",
                emoji="🗑️",
            )
            for i, g in enumerate(slice_)
        ]

        select = Select(placeholder="Welches Spiel soll entfernt werden?", options=options)
        select.callback = self.select_callback
        self.add_item(select)

        cancel_btn = Button(label="Abbrechen", emoji="✖️", style=ButtonStyle.secondary)
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)

    async def select_callback(self, interaction: discord.Interaction):
        index = int(interaction.data["values"][0])
        removed = self.cog.games.pop(index)
        embed = discord.Embed(color=COLORS["green"])
        embed.set_author(name="✅  Spiel entfernt")
        embed.title = f'"{removed}" wurde aus der Liste entfernt.'
        embed.set_footer(text=f"{len(self.cog.games)} Spiele verbleiben")
        await interaction.response.edit_message(embed=embed, view=None)
        await asyncio.sleep(1.5)
        list_embed, list_view = build_game_list_message(self.cog, 0)
        await interaction.edit_original_response(embed=list_embed, view=list_view)

    async def cancel_callback(self, interaction: discord.Interaction):
        embed, view = build_game_list_message(self.cog, 0)
        await interaction.response.edit_message(embed=embed, view=view)


class ChallengeListView(View):
    def __init__(self, cog_ref, page: int = 0):
        super().__init__(timeout=120)
        self.cog = cog_ref
        self.page = page
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        page_size = 7
        total_pages = max(1, -(-len(self.cog.challenges) // page_size))

        add_btn = Button(label="Challenge hinzufügen", emoji="➕", style=ButtonStyle.success)
        add_btn.callback = self.add_callback
        self.add_item(add_btn)

        rem_btn = Button(
            label="Challenge entfernen", emoji="🗑️", style=ButtonStyle.danger,
            disabled=len(self.cog.challenges) == 0,
        )
        rem_btn.callback = self.remove_callback
        self.add_item(rem_btn)

        if total_pages > 1:
            prev_btn = Button(label="Zurück", emoji="◀️", style=ButtonStyle.secondary,
                              disabled=self.page == 0)
            prev_btn.callback = self.prev_callback
            self.add_item(prev_btn)

            next_btn = Button(label="Weiter", emoji="▶️", style=ButtonStyle.secondary,
                              disabled=self.page >= total_pages - 1)
            next_btn.callback = self.next_callback
            self.add_item(next_btn)

    async def add_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ChallengeAddModal(self.cog))

    async def remove_callback(self, interaction: discord.Interaction):
        view, embed = build_challenge_remove_view(self.cog, self.page)
        if view is None:
            return await interaction.response.send_message("❌ Keine Challenges zum Entfernen.", ephemeral=True)
        await interaction.response.edit_message(embed=embed, view=view)

    async def prev_callback(self, interaction: discord.Interaction):
        self.page = max(0, self.page - 1)
        embed, view = build_challenge_list_message(self.cog, self.page)
        await interaction.response.edit_message(embed=embed, view=view)

    async def next_callback(self, interaction: discord.Interaction):
        page_size = 7
        total_pages = max(1, -(-len(self.cog.challenges) // page_size))
        self.page = min(total_pages - 1, self.page + 1)
        embed, view = build_challenge_list_message(self.cog, self.page)
        await interaction.response.edit_message(embed=embed, view=view)


class ChallengeRemoveView(View):
    def __init__(self, cog_ref, page: int = 0):
        super().__init__(timeout=120)
        self.cog = cog_ref
        self.page = page

        page_size = 7
        start = page * page_size
        slice_ = self.cog.challenges[start:start + page_size]

        options = [
            discord.SelectOption(
                label=c["text"][:80] + ("..." if len(c["text"]) > 80 else ""),
                value=str(start + i),
                description=f"{c['difficulty']} {c['label']} — Eintrag #{start + i + 1}",
                emoji="🗑️",
            )
            for i, c in enumerate(slice_)
        ]

        select = Select(placeholder="Welche Challenge soll entfernt werden?", options=options)
        select.callback = self.select_callback
        self.add_item(select)

        cancel_btn = Button(label="Abbrechen", emoji="✖️", style=ButtonStyle.secondary)
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)

    async def select_callback(self, interaction: discord.Interaction):
        index = int(interaction.data["values"][0])
        removed = self.cog.challenges.pop(index)
        embed = discord.Embed(color=COLORS["green"])
        embed.set_author(name="✅  Challenge entfernt")
        embed.title = f"Challenge #{index + 1} wurde entfernt."
        embed.description = f"~~{removed['text']}~~"
        embed.set_footer(text=f"{len(self.cog.challenges)} Challenges verbleiben")
        await interaction.response.edit_message(embed=embed, view=None)
        await asyncio.sleep(1.5)
        list_embed, list_view = build_challenge_list_message(self.cog, 0)
        await interaction.edit_original_response(embed=list_embed, view=list_view)

    async def cancel_callback(self, interaction: discord.Interaction):
        embed, view = build_challenge_list_message(self.cog, 0)
        await interaction.response.edit_message(embed=embed, view=view)


# ── Builder helpers ───────────────────────────────────────────────────────────

def build_game_list_message(cog, page: int = 0):
    page_size = 10
    total_pages = max(1, -(-len(cog.games) // page_size))
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    slice_ = cog.games[start:start + page_size]
    game_icons = ["🎮", "🕹️", "👾", "🎯", "🏆", "⚔️", "🛸", "🔫", "🧩", "🌟"]

    embed = discord.Embed(color=COLORS["blue"])
    embed.set_author(name="🕹️  Gaming Event Bot  •  Spiele-Liste")
    embed.title = f"{len(cog.games)} Spiele verfügbar"
    if slice_:
        embed.description = "\n".join(
            f"{game_icons[(start + i) % len(game_icons)]}  `{str(start + i + 1).zfill(2)}`  **{g}**"
            for i, g in enumerate(slice_)
        )
    else:
        embed.description = "*Noch keine Spiele. Füge welche über den Button hinzu!*"
    embed.set_footer(text=f"Seite {page + 1} / {total_pages}  •  {len(cog.games)} Spiele gesamt")
    return embed, GameListView(cog, page)


def build_challenge_list_message(cog, page: int = 0):
    page_size = 7
    total_pages = max(1, -(-len(cog.challenges) // page_size))
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    slice_ = cog.challenges[start:start + page_size]

    embed = discord.Embed(color=COLORS["purple"])
    embed.set_author(name="🎯  Gaming Event Bot  •  Challenge-Liste")
    embed.title = f"{len(cog.challenges)} Challenges verfügbar"
    if slice_:
        embed.description = "\n\n".join(
            f"{diff_emoji(c['label'])}  `{str(start + i + 1).zfill(2)}`  **{c['text']}**\n"
            f"\u200b\u2003{c['difficulty']} {c['label']}"
            for i, c in enumerate(slice_)
        )
    else:
        embed.description = "*Noch keine Challenges. Füge welche über den Button hinzu!*"
    embed.set_footer(text=f"Seite {page + 1} / {total_pages}  •  {len(cog.challenges)} Challenges gesamt")
    return embed, ChallengeListView(cog, page)


def build_game_remove_view(cog, page: int = 0):
    page_size = 10
    start = page * page_size
    if not cog.games[start:start + page_size]:
        return None, None
    embed = discord.Embed(color=COLORS["red"])
    embed.set_author(name="🗑️  Spiel entfernen")
    embed.title = "Wähle das Spiel aus das du entfernen möchtest."
    return GameRemoveView(cog, page), embed


def build_challenge_remove_view(cog, page: int = 0):
    page_size = 7
    start = page * page_size
    if not cog.challenges[start:start + page_size]:
        return None, None
    embed = discord.Embed(color=COLORS["red"])
    embed.set_author(name="🗑️  Challenge entfernen")
    embed.title = "Wähle die Challenge aus die du entfernen möchtest."
    return ChallengeRemoveView(cog, page), embed


# ── Cog ───────────────────────────────────────────────────────────────────────

class GamingEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games: list = list(DEFAULT_GAMES)
        self.challenges: list = [dict(c) for c in DEFAULT_CHALLENGES]

    @commands.hybrid_command(name="challenge", description="🎯 Zufällige Challenge für die Runde")
    @app_commands.describe(kanal="Zielkanal (optional)")
    @commands.guild_only()
    async def challenge(self, ctx: commands.Context, kanal: discord.TextChannel = None):
        if not self.challenges:
            return await ctx.send("❌ Keine Challenges in der Liste!", ephemeral=True)
        c = random.choice(self.challenges)
        embed = build_challenge_embed(c)
        target = kanal or ctx.channel
        if kanal and kanal.id != ctx.channel.id:
            await target.send(embed=embed)
            return await ctx.send(f"✅ Challenge in {target.mention} gepostet!", ephemeral=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="challenge_list", description="📋 Alle Challenges anzeigen & verwalten")
    @commands.guild_only()
    async def challenge_list(self, ctx: commands.Context):
        embed, view = build_challenge_list_message(self, 0)
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @commands.hybrid_command(name="randomgame", description="🎮 Zufälliges Spiel auswählen")
    @app_commands.describe(kanal="Zielkanal (optional)")
    @commands.guild_only()
    async def randomgame(self, ctx: commands.Context, kanal: discord.TextChannel = None):
        if not self.games:
            return await ctx.send(
                "❌ Keine Spiele in der Liste! Nutze `/game_list` um welche hinzuzufügen.", ephemeral=True
            )
        game = random.choice(self.games)
        embed = build_random_game_embed(game, self.games)
        target = kanal or ctx.channel
        if kanal and kanal.id != ctx.channel.id:
            await target.send(embed=embed)
            return await ctx.send(f"✅ Spiel in {target.mention} gepostet!", ephemeral=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="game_list", description="🕹️ Spiele-Liste anzeigen & verwalten")
    @commands.guild_only()
    async def game_list(self, ctx: commands.Context):
        embed, view = build_game_list_message(self, 0)
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @commands.hybrid_command(name="umfrage", description="📅 Verfügbarkeits-Umfrage erstellen")
    @app_commands.describe(
        frage="z.B. Wer ist Freitag 20 Uhr dabei?",
        kanal="Zielkanal (optional)",
    )
    @commands.guild_only()
    async def umfrage(self, ctx: commands.Context, frage: str, kanal: discord.TextChannel = None):
        target = kanal or ctx.channel
        embed = build_poll_embed(frage, ctx.author)
        msg = await target.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        await msg.add_reaction("❓")
        if kanal and kanal.id != ctx.channel.id:
            return await ctx.send(f"✅ Umfrage in {target.mention} erstellt!", ephemeral=True)
        await ctx.send("✅ Umfrage erstellt!", ephemeral=True)

    @commands.hybrid_command(name="event_start", description="🚀 Event starten und alle pingen")
    @app_commands.describe(
        titel="Event-Name (optional)",
        kanal="Zielkanal (optional)",
    )
    @commands.guild_only()
    async def event_start(self, ctx: commands.Context, titel: str = None, kanal: discord.TextChannel = None):
        target = kanal or ctx.channel
        embed = build_event_embed(titel, ctx.author, self.games, self.challenges)
        await target.send(content="@everyone", embed=embed)
        if kanal and kanal.id != ctx.channel.id:
            return await ctx.send(f"✅ Event in {target.mention} gestartet!", ephemeral=True)
        await ctx.send("✅ Event gestartet!", ephemeral=True)