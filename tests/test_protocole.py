#!venv/bin/python3

import random
import textwrap
import unittest

import aioircd
from aioircd.states import *
from .common import AsyncTestCase, TestIRC, waitfor


class TestProtocole(AsyncTestCase, TestIRC):
    async def atest_nick_collision(self, nursery):

        await self.start_server(nursery)

        bob = await self.connect_user()
        await bob.usend("NICK bob")
        self.assertFalse(await bob.urecv(), "Nickname should not be used.")

        eve = await self.connect_user()

        with self.assertLogs('aioircd.user', 'WARNING'):
            await eve.usend("NICK bob")
            self.assertIn("Nickname is already in use", await eve.urecv())
        await eve.usend("QUIT")
        await eve.waitforstate(QuitState)

        await bob.usend("QUIT")
        await bob.waitforstate(QuitState)

        bob = await self.connect_user()
        await bob.usend("NICK bob")
        self.assertFalse(await bob.urecv(), "Nickname should not be used.")


class TestTour(AsyncTestCase, TestIRC):
     async def atest_who_and_whois(self, nursery):
        await self.start_server(nursery)

        bob = await self.connect_user()
        await self.register(bob, 'whoisbob')

        eve = await self.connect_user()
        await self.register(eve, 'whoiseve')

        await bob.usend('JOIN #whoischan')
        self.assertEqual(await bob.urecv(), textwrap.dedent('''\
            :whoisbob JOIN #whoischan\r
            :ip6-localhost 353 whoisbob = #whoischan :whoisbob\r
            :ip6-localhost 366 whoisbob #whoischan :End of /NAMES list.\r
            '''))

        await eve.usend('JOIN #whoischan')
        self.assertEqual(await eve.urecv(), textwrap.dedent('''\
            :whoiseve JOIN #whoischan\r
            :ip6-localhost 353 whoiseve = #whoischan :whoisbob whoiseve\r
            :ip6-localhost 366 whoiseve #whoischan :End of /NAMES list.\r
            '''))
        self.assertEqual(await bob.urecv(), ':whoiseve JOIN #whoischan\r\n')

        await bob.usend('WHO #whoischan')
        who_reply = await bob.urecv()
        self.assertIn(':ip6-localhost 352 whoisbob #whoischan ~whoisbob ::1 ip6-localhost whoisbob H :0 John Doe\r\n', who_reply)
        self.assertIn(':ip6-localhost 352 whoisbob #whoischan ~whoiseve ::1 ip6-localhost whoiseve H :0 John Doe\r\n', who_reply)
        self.assertTrue(who_reply.endswith(':ip6-localhost 315 whoisbob #whoischan :End of /WHO list.\r\n'))

        await bob.usend('WHOIS whoiseve')
        self.assertEqual(await bob.urecv(), textwrap.dedent('''\
            :ip6-localhost 311 whoisbob whoiseve ~whoiseve ::1 ip6-localhost :John Doe\r
            :ip6-localhost 312 whoisbob whoiseve ip6-localhost :aioircd\r
            :ip6-localhost 319 whoisbob whoiseve :#whoischan\r
            :ip6-localhost 318 whoisbob whoiseve :End of /WHOIS list.\r
            '''))

     async def atest_tour(self, nursery):
        await self.start_server(nursery)

        bob = await self.connect_user()
        self.assertIsInstance(bob.state, ConnectedState)

        with self.assertLogs('aioircd.user', 'WARNING'):
            await bob.usend("CAP LS 302")
            self.assertRegex(await bob.urecv(), r":ip6-localhost 400 \[::1\]:\d+ - :Command CAP is unknown\.\r\n")


        self.assertIsInstance(bob.state, ConnectedState)

        await bob.usend("NICK bob")
        self.assertFalse(await bob.urecv(), "NICK without USER does not reply")
        await bob.usend("USER bob 0 * :bob")
        self.assertEqual(await bob.urecv(), textwrap.dedent(f"""\
            :ip6-localhost 001 bob :Welcome to the Internet Relay Network bob\r
            :ip6-localhost 002 bob :Your host is ip6-localhost, running version {aioircd.__version__}\r
            :ip6-localhost 003 bob :The server was created someday\r
            :ip6-localhost 004 bob aioircd {aioircd.__version__}  \r
            :ip6-localhost 005 bob AWAYLEN=0 CASEMAPPING=ascii CHANLIMIT=#: CHANMODES= CHANNELLEN=50 CHANTYPES=# ELIST= :are supported by this server\r
            :ip6-localhost 005 bob HOSTLEN=63 KICKLEN=0 MAXLIST= MAXTARGETS=12 MODES=0 NICKLEN=15 STATUSMSG= TOPICLEN=0 USERLEN=15 :are supported by this server\r
            :ip6-localhost 422 bob :MOTD File is missing\r
            """))
        self.assertIsInstance(bob.state, RegisteredState)

        token = random.randint(1000, 9999)
        await bob.usend(f"PING {token}")
        self.assertEqual(await bob.urecv(), f":ip6-localhost PONG ip6-localhost {token}\r\n")

        # Connect Eve, she sends PASS+NICK+USER and consumes the motd
        eve = await self.connect_user()
        await self.register(eve, "eve")

        # Connect Liz, she sends PASS+NICK+USER and consumes the motd
        liz = await self.connect_user()
        await self.register(liz, "liz")

        # Bob sends JOIN
        self.assertFalse(bob.channels)
        self.assertNotIn('#readthedocs', self._servlocal.channels)

        await bob.usend("JOIN #readthedocs")
        self.assertEqual(await bob.urecv(), textwrap.dedent("""\
            :bob JOIN #readthedocs\r
            :ip6-localhost 353 bob = #readthedocs :bob\r
            :ip6-localhost 366 bob #readthedocs :End of /NAMES list.\r
            """))
        self.assertIn('#readthedocs', self._servlocal.channels)
        rtdchan = self._servlocal.channels['#readthedocs']
        self.assertIn(rtdchan, bob.channels)
        self.assertIn(bob, rtdchan.users)

        # Eve JOIN readthedocs
        await eve.usend("JOIN #readthedocs")
        self.assertEqual(await eve.urecv(), textwrap.dedent("""\
            :eve JOIN #readthedocs\r
            :ip6-localhost 353 eve = #readthedocs :bob eve\r
            :ip6-localhost 366 eve #readthedocs :End of /NAMES list.\r
            """))
        self.assertEqual(await bob.urecv(), ":eve JOIN #readthedocs\r\n")
        self.assertIn(rtdchan, eve.channels)
        self.assertIn(eve, rtdchan.users)

        # Liz LIST all channels
        await liz.usend("LIST")
        self.assertEqual(await liz.urecv(), textwrap.dedent("""\
            :ip6-localhost 321 liz Channel :Users Name\r
            :ip6-localhost 322 liz #readthedocs 2 :\r
            :ip6-localhost 323 liz :End of /LIST\r
            """))

        # Liz JOIN readthedocs too
        await liz.usend("JOIN #readthedocs")
        await bob.urecv()
        await eve.urecv()
        self.assertEqual(await liz.urecv(), textwrap.dedent("""\
            :liz JOIN #readthedocs\r
            :ip6-localhost 353 liz = #readthedocs :bob eve liz\r
            :ip6-localhost 366 liz #readthedocs :End of /NAMES list.\r
            """))
        self.assertIn(rtdchan, liz.channels)
        self.assertIn(liz, rtdchan.users)

        # Eve greeting the chat
        await eve.usend("PRIVMSG #readthedocs :Hi all!")
        self.assertEqual(await eve.urecv(), "")
        self.assertEqual(await liz.urecv(), ":eve PRIVMSG #readthedocs :Hi all!\r\n")
        self.assertEqual(await bob.urecv(), ":eve PRIVMSG #readthedocs :Hi all!\r\n")

        # Eve PART from readthedocs
        await eve.usend("PART #readthedocs :I'm taking a break")
        self.assertTrue(await waitfor(lambda: rtdchan not in eve.channels))
        self.assertEqual(await eve.urecv(), "")
        self.assertEqual(await liz.urecv(), ":eve PART #readthedocs :I'm taking a break\r\n")
        self.assertEqual(await bob.urecv(), ":eve PART #readthedocs :I'm taking a break\r\n")
        self.assertNotIn(rtdchan, eve.channels)
        self.assertNotIn(eve, rtdchan.users)

        # Liz send message to Eve
        await liz.usend("PRIVMSG eve :Hi, how are you ?")
        self.assertEqual(await bob.urecv(), "")
        self.assertEqual(await liz.urecv(), "")
        self.assertEqual(await eve.urecv(), ":liz PRIVMSG eve :Hi, how are you ?\r\n")

        # Bob check users in the channel
        await bob.usend("NAMES #readthedocs")
        self.assertEqual(await bob.urecv(), textwrap.dedent("""\
            :ip6-localhost 353 bob = #readthedocs :bob liz\r
            :ip6-localhost 366 bob #readthedocs :End of /NAMES list.\r
            """))

        # Bob QUIT the server, he need to sleep
        await bob.usend("QUIT :Bye")
        self.assertTrue(await bob.waitforstate(QuitState))

        self.assertFalse(await eve.urecv())  # she has no channel in common with bob
        self.assertEqual(await liz.urecv(), ":bob QUIT :Quit: Bye\r\n")
        self.assertNotIn(rtdchan, bob.channels)
        self.assertNotIn(bob, rtdchan.users)

        # Stop the server
        nursery.cancel_scope.cancel()
