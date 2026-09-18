from ellinetircd.PluginAPI import GenericContext, PluginType
from ellinetircd.accounts import get_connection, add_user, verify_password, UserNotFoundError
from ellinetircd.user import BotUser, load_opers
from typing import Optional
import trio
import logging
import shlex
from pathlib import Path

logger = logging.getLogger(__name__)

PLUGIN_TYPE = PluginType.GENERIC
PLUGIN_NAME = "NickServ"
PLUGIN_ID = "NickServ"

DATABASE_PATH = Path("NickServ.db")

async def setup(context: GenericContext):
    conn = get_connection()
    c = conn.cursor()
    async with trio.open_nursery() as nursery:
        async with BotUser(nursery) as bot:
            await bot.register("NickServ")
            async for user, channel, message in bot.messages():
                if channel:
                    continue
                
                args = shlex.split(message)
                match args[0].upper():
                    case "HELP":
                        await bot.send_message(user, "Available commands:")
                        await bot.send_message(user, "/msg NickServ REGISTER <password> [email]")
                        await bot.send_message(user, "/msg NickServ IDENTIFY <password>")
                    
                    case "REGISTER":
                        if user.nick is None:
                            continue
                        if len(args) != 2:
                            await bot.send_message(user, "Usage: /msg NickServ REGISTER <password> [email]")
                            await bot.send_message(user, "Email is optional and does not do anything currently other then be stored.")
                            continue
                        
                        password = args[1]
                        email: Optional[str] = None
                        if len(args) > 2:
                            email = args[2]

                        add_user(c, user.nick, password, email)
                        await bot.send_message(user, "Registration successful.")
                        user.modes.add("r")
                    case "IDENTIFY"|"LOGIN":
                        if user.nick is None:
                            continue
                        if len(args) != 2:
                            await bot.send_message(user, "Usage: /msg NickServ IDENTIFY <password>")
                            continue
                        password = args[1]
                        try:
                            if not verify_password(c, user.nick, password) is None:
                                await bot.send_message(user, "Incorrect password.")
                                continue
                        except UserNotFoundError:
                            await bot.send_message(user, "You do not have an account. Use /msg NickServ REGISTER to create one.")
                            continue
                        user.modes.add("r")
                        await bot.send_message(user, "Login successful.")
                        if user.nick in load_opers()["opers"]:
                            user.modes.add("o")
                            await bot.send_message(user, "+o has been granted to you.")

                    case _:
                        await bot.send_message(user, f"Unknown command: {args[0]}")