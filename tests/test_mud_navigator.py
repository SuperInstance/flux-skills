"""
Tests for the MUD Navigator Python adapter.

Tests the MUDNavigator class with mocked sockets.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "mud-navigator"))
from mud_navigator import MUDNavigator


class TestMUDNavigatorInit:
    def test_default_init(self):
        nav = MUDNavigator("test_agent")
        assert nav.name == "test_agent"
        assert nav.role == "greenhorn"
        assert nav.host == "localhost"
        assert nav.port == 7777
        assert nav.sock is None
        assert nav.current_room == "harbor"

    def test_custom_init(self):
        nav = MUDNavigator("agent2", role="explorer", host="remote", port=9999)
        assert nav.name == "agent2"
        assert nav.role == "explorer"
        assert nav.host == "remote"
        assert nav.port == 9999

    def test_instinct_map_exists(self):
        assert hasattr(MUDNavigator, "INSTINCT_MAP")
        assert len(MUDNavigator.INSTINCT_MAP) == 10

    def test_instinct_map_values(self):
        assert MUDNavigator.INSTINCT_MAP[0x30] == "explore"
        assert MUDNavigator.INSTINCT_MAP[0x31] == "rest"
        assert MUDNavigator.INSTINCT_MAP[0x32] == "socialize"
        assert MUDNavigator.INSTINCT_MAP[0x33] == "forage"
        assert MUDNavigator.INSTINCT_MAP[0x34] == "defend"
        assert MUDNavigator.INSTINCT_MAP[0x35] == "build"
        assert MUDNavigator.INSTINCT_MAP[0x36] == "signal"
        assert MUDNavigator.INSTINCT_MAP[0x37] == "migrate"
        assert MUDNavigator.INSTINCT_MAP[0x38] == "hoard"
        assert MUDNavigator.INSTINCT_MAP[0x39] == "teach"


class TestMUDNavigatorCommands:
    def _setup_mock_sock(self, nav, responses):
        """Set up a mock socket that returns canned responses."""
        nav.sock = MagicMock()
        call_count = [0]

        def mock_recv(size):
            resp = responses[min(call_count[0], len(responses) - 1)]
            call_count[0] += 1
            return resp.encode()

        def mock_recv_timeout(size):
            import socket
            raise socket.timeout()

        nav.sock.recv.side_effect = mock_recv
        nav.sock.sendall = MagicMock()

    def test_not_connected_returns_error(self):
        nav = MUDNavigator("test")
        assert nav.look() == "NOT_CONNECTED"

    def test_look_command(self):
        nav = MUDNavigator("test")
        self._setup_mock_sock(nav, ["You see a harbor."])
        result = nav.look()
        assert "harbor" in result

    def test_go_command(self):
        nav = MUDNavigator("test")
        self._setup_mock_sock(nav, ["You enter the tavern."])
        result = nav.go("tavern")
        assert "tavern" in result
        assert nav.current_room == "tavern"

    def test_say_command(self):
        nav = MUDNavigator("test")
        self._setup_mock_sock(nav, ["You say: hello"])
        result = nav.say("hello")
        assert "hello" in result

    def test_whisper_command(self):
        nav = MUDNavigator("test")
        self._setup_mock_sock(nav, ["You whisper to agent2: secret"])
        result = nav.whisper("agent2", "secret")
        assert "secret" in result

    def test_shout_command(self):
        nav = MUDNavigator("test")
        self._setup_mock_sock(nav, ["You shout: HELP"])
        result = nav.shout("HELP")
        assert "HELP" in result

    def test_rooms_command(self):
        nav = MUDNavigator("test")
        self._setup_mock_sock(nav, ["harbor, tavern, library"])
        result = nav.rooms()
        assert "harbor" in result

    def test_status_command(self):
        nav = MUDNavigator("test")
        self._setup_mock_sock(nav, ["Status: working"])
        result = nav.status("working")
        assert "working" in result

    def test_project_command(self):
        nav = MUDNavigator("test")
        self._setup_mock_sock(nav, ["Project set."])
        result = nav.project("My project")
        assert "project" in result.lower()

    def test_write_msg_command(self):
        nav = MUDNavigator("test")
        self._setup_mock_sock(nav, ["Message written."])
        result = nav.write_msg("Hello world")
        assert "written" in result.lower()

    def test_quit_command(self):
        nav = MUDNavigator("test")
        self._setup_mock_sock(nav, ["Goodbye!"])
        result = nav.quit()
        assert nav.sock is None

    def test_enter_is_connect(self):
        """enter() should be an alias for connect()."""
        nav = MUDNavigator("test")
        nav.connect = MagicMock(return_value="Connected!")
        assert nav.enter() == "Connected!"


class TestMUDNavigatorInstincts:
    def test_execute_instinct_explore_with_payload(self):
        nav = MUDNavigator("test")
        nav.go = MagicMock(return_value="You go to the forest.")
        result = nav.execute_instinct(0x30, "forest")
        assert "forest" in result

    def test_execute_instinct_explore_without_payload(self):
        nav = MUDNavigator("test")
        nav._cmd = MagicMock(return_value="You wander around.")
        result = nav.execute_instinct(0x30)
        assert "wander" in result

    def test_execute_instinct_rest(self):
        nav = MUDNavigator("test")
        nav._cmd = MagicMock(return_value="Status: idle")
        result = nav.execute_instinct(0x31)
        assert "idle" in result

    def test_execute_instinct_socialize_with_payload(self):
        nav = MUDNavigator("test")
        nav.say = MagicMock(return_value="You say: hi there")
        result = nav.execute_instinct(0x32, "hi there")
        assert "hi there" in result

    def test_execute_instinct_socialize_without_payload(self):
        nav = MUDNavigator("test")
        nav.say = MagicMock(return_value="You say: ...")
        result = nav.execute_instinct(0x32)
        assert "..." in result

    def test_execute_instinct_forage(self):
        nav = MUDNavigator("test")
        nav.look = MagicMock(return_value="You see items.")
        result = nav.execute_instinct(0x33)
        assert "items" in result

    def test_execute_instinct_signal_with_payload(self):
        nav = MUDNavigator("test")
        nav.shout = MagicMock(return_value="You shout: SOS")
        result = nav.execute_instinct(0x36, "SOS")
        assert "SOS" in result

    def test_execute_instinct_signal_without_payload(self):
        nav = MUDNavigator("test")
        nav.shout = MagicMock(return_value="You shout: beacon")
        result = nav.execute_instinct(0x36)
        assert "beacon" in result

    def test_execute_instinct_unknown(self):
        """Unknown instinct opcodes should default to look/forage."""
        nav = MUDNavigator("test")
        nav.look = MagicMock(return_value="Looking around.")
        result = nav.execute_instinct(0xFF)
        assert "Looking" in result

    def test_execute_instinct_migrate(self):
        nav = MUDNavigator("test")
        nav._cmd = MagicMock(return_value="Wandering...")
        result = nav.execute_instinct(0x37)
        assert "Wandering" in result

    def test_execute_instinct_hoard(self):
        """Hoard should default to look."""
        nav = MUDNavigator("test")
        nav.look = MagicMock(return_value="Searching...")
        result = nav.execute_instinct(0x38)
        assert "Searching" in result

    def test_execute_instinct_teach(self):
        """Teach should default to look."""
        nav = MUDNavigator("test")
        nav.look = MagicMock(return_value="Examining...")
        result = nav.execute_instinct(0x39)
        assert "Examining" in result

    def test_execute_instinct_defend(self):
        """Defend should default to look."""
        nav = MUDNavigator("test")
        nav.look = MagicMock(return_value="Standing guard.")
        result = nav.execute_instinct(0x34)
        assert "Standing" in result
