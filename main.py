import logging
import traceback

import coc
import discord
import creds

from coc import utils
from discord.ext import commands

from keep_alive import keep_alive


REPORT_STYLE = "{att.attacker.name} (No. {att.attacker.map_position}, TH{att.attacker.town_hall}) just {verb} {att.defender.name} (No. {att.defender.map_position}, TH{att.defender.town_hall}) for {att.stars} stars and {att.destruction}%. "


bot = commands.Bot(command_prefix="?", intents=discord.Intents.all())
coc_client = coc.login(
    creds.coc_dev_email,
    creds.coc_dev_password,
    client=coc.EventsClient,
    key_names="war_home"
)
logging.basicConfig(level=logging.ERROR)


coc_client.add_war_updates("#2QRY8GP2Y")
coc_client.add_clan_updates("#2QRY8GP2Y")


@bot.event
async def on_ready():
    print("Logged in")

@coc_client.event
@coc.WarEvents.war_attack()
async def on_war_attack(attack, war):
    await bot.get_channel(creds.war_channel).send(REPORT_STYLE.format(att=attack, verb="attacked"))
    #await bot.get_channel(creds.war_channel).send(f"{0} attacked {1} for {2}stars and {3} percent destruction").format(attack.attacker.name, attack.defender.name,attack.stars,attack.destruction)

@coc_client.event
@coc.WarEvents.state()
async def on_war_state_change(current_state, war):
    await bot.get_channel(creds.war_channel).send("{0.clan.name} just entered {1} state!".format(war, current_state))


@coc_client.event
@coc.ClanEvents.member_join(tags=creds.clan_tag)
async def on_clan_member_join(member, clan):
    await bot.get_channel(creds.default_channel).send(
        "{0.name} ({0.tag}) just " "joined our clan {1.name} ({1.tag})!".format(
            member, clan)
    )


@coc_client.event
@coc.ClanEvents.member_name(tags=creds.clan_tag)
async def member_name_change(old_player, new_player):
    await bot.get_channel(creds.default_channel).send(
        "Name Change! {0.name} is now called {1.name} (his tag is {1.tag})".format(
            old_player, new_player)
    )


@coc_client.event
@coc.ClientEvents.event_error()
async def on_event_error(exception):
    if isinstance(exception, coc.PrivateWarLog):
        return  # lets ignore private war log errors
    print("Uh oh! Something went wrong in coc.py events... printing traceback for you.")
    traceback.print_exc()
    traceback.print_stack()


@coc_client.event
@coc.ClanEvents.member_donations(tags=creds.clan_tag)
async def on_donate(old_member, member):
    troops_donated = member.donations - old_member.donations
    await bot.get_channel(creds.default_channel).send("{0} just donated {1} troops!".format(member.name, troops_donated))



@bot.command()
async def player_heroes(ctx, player_tag):
    if not utils.is_valid_tag(player_tag):
        await ctx.send("You didn't give me a proper tag!")
        return

    try:
        player = await coc_client.get_player(player_tag)
    except coc.NotFound:
        await ctx.send("This player doesn't exist!")
        return

    to_send = ""
    for hero in player.heroes:
        to_send += "{}: Lv{}/{}\n".format(str(hero),
                                          hero.level, hero.max_level)

    await ctx.send(to_send)


@bot.command()
async def parse_army(ctx, army_link: str):
    troops, spells = coc_client.parse_army_link(army_link)
    print(troops, spells)
    parsed_link_output = ''
    if troops or spells:  # checking if troops or spells is present in link

        for troop, quantity in troops:
            parsed_link_output += "The user wants {} {}s. They each have {} DPS.\n".format(
                quantity, troop.name, troop.dps)

        for spell, quantity in spells:
            parsed_link_output += "The user wants {} {}s.\n".format(
                quantity, spell.name)
    else:
        parsed_link_output += "Invalid Link!"
    await ctx.send(parsed_link_output)

@bot.command()
async def create_army(ctx):
    link = coc_client.create_army_link(
        barbarian=10,
        archer=20,
        hog_rider=30,
        healing_spell=3,
        poison_spell=2,
        rage_spell=2
    )
    await ctx.send(link)

@bot.command()
async def clan_info(ctx, clan_tag = creds.clan_tag):
    if not utils.is_valid_tag(clan_tag):
        #clan_tag = tag
        return

    try:
        clan = await coc_client.get_clan(clan_tag)
    except coc.NotFound:
        await ctx.send("This clan doesn't exist!")
        return

    if clan.public_war_log is False:
        log = "Private"
    else:
        log = "Public"

    e = discord.Embed(colour=discord.Colour.green())
    e.set_thumbnail(url=clan.badge.url)
    e.add_field(name="Clan Name",
                value=f"{clan.name}({clan.tag})\n[Open in game]({clan.share_link})", inline=False)
    e.add_field(name="Clan Level", value=clan.level, inline=False)
    e.add_field(name="Description", value=clan.description, inline=False)
    e.add_field(name="Leader", value=clan.get_member_by(
        role=coc.Role.leader), inline=False)
    e.add_field(name="Clan Type", value=clan.type, inline=False)
    e.add_field(name="Location", value=clan.location, inline=False)
    e.add_field(name="Total Clan Trophies", value=clan.points, inline=False)
    e.add_field(name="Total Clan Versus Trophies",
                value=clan.versus_points, inline=False)
    e.add_field(name="WarLog Type", value=log, inline=False)
    e.add_field(name="Required Trophies",
                value=clan.required_trophies, inline=False)
    e.add_field(name="War Win Streak", value=clan.war_win_streak, inline=False)
    e.add_field(name="War Frequency", value=clan.war_frequency, inline=False)
    e.add_field(name="Clan War League Rank",
                value=clan.war_league, inline=False)
    e.add_field(name="Clan Labels", value="\n".join(
        label.name for label in clan.labels), inline=False)
    e.add_field(name="Member Count",
                value=f"{clan.member_count}/50", inline=False)
    e.add_field(
        name="Clan Record",
        value=f"Won - {clan.war_wins}\nLost - {clan.war_losses}\n Draw - {clan.war_ties}",
        inline=False
    )
    await ctx.send(embed=e)
    

thing = 0
from discord.ext import tasks
@tasks.loop(seconds = 10) # repeat after every 10 seconds
async def myLoop():
    global thing
    war = await coc_client.get_current_war(creds.clan_tag)
    time = hours, remainder = divmod(int(war.end_time.seconds_until), 3600)
    if thing == 0:
        if time[0] == 0:
            await bot.get_channel(creds.war_channel).send("<@&970426054919475310> 1 hour left until war ends!")
            thing = 1
        elif time[0] > 0:
            thing = 0



@bot.command()
async def clan_member(ctx, clan_tag):
    if not utils.is_valid_tag(clan_tag):
        await ctx.send("You didn't give me a proper tag!")
        return

    try:
        clan = await coc_client.get_clan(clan_tag)
    except coc.NotFound:
        await ctx.send("This clan does not exist!")
        return

    member = ""
    for i, a in enumerate(clan.members, start=1):
        member += f"`{i}.` {a.name}\n"
    embed = discord.Embed(colour=discord.Colour.red(),
                          title=f"Members of {clan.name}", description=member)
    embed.set_thumbnail(url=clan.badge.url)
    embed.set_footer(text=f"Total Members - {clan.member_count}/50")
    await ctx.send(embed=embed)


@bot.command()
async def war(ctx, clan_tag = creds.clan_tag):
    if not utils.is_valid_tag(clan_tag):
        await ctx.send("You didn't give me a proper tag!")
        #clan_tag = tag
        return

    e = discord.Embed(colour=discord.Colour.blue())

    try:
        war = await coc_client.get_current_war(clan_tag)
    except coc.PrivateWarLog:
        return await ctx.send("Clan has a private war log!")

    if war is None:
        return await ctx.send("Clan is in a strange CWL state!")

    e.add_field(name="War State:", value=war.state, inline=False)

    if war.end_time:  # if state is notInWar we will get errors

        hours, remainder = divmod(int(war.end_time.seconds_until), 3600)
        minutes, seconds = divmod(remainder, 60)

        e.add_field(name=war.clan.name, value=war.clan.tag)
        e.add_field(
            name="Opponent:", value=f"{war.opponent.name}\n" f"{war.opponent.tag}", inline=False)
        e.add_field(name="War End Time:",
                    value=f"{hours} hours {minutes} minutes {seconds} seconds", inline=False)

    await ctx.send(embed=e)


keep_alive()
myLoop.start()
bot.run(creds.discord_bot_token)
