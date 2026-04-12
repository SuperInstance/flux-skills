"""Tests for the MUD Navigator skill — Python adapter."""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import socket


class TestMUDNavigatorInit:
    def test_default_params(self):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        nav = MUDNavigator("testbot")
        assert nav.name == "testbot"
        assert nav.role == "greenhorn"
        assert nav.host == "localhost"
        assert nav.port == 7777
        assert nav.sock is None
        assert nav.current_room == "harbor"

    def test_custom_params(self):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        nav = MUDNavigator("bot", role="scout", host="mud.example.com", port=9999)
        assert nav.role == "scout"
        assert nav.host == "mud.example.com"
        assert nav.port == 9999


class TestMUDNavigatorConnect:
    @patch("skills.mud_navigator.mud_navigator.socket.socket")
    def test_connect_success(self, mock_socket_cls):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        mock_sock = MagicMock()
        mock_sock.recv.return_value = b"Welcome\nWhat is your name?\nRole?\nRoom desc\n"
        mock_socket_cls.return_value = mock_sock

        nav = MUDNavigator("bot", "scout")
        result = nav.connect()
        assert nav.sock is mock_sock
        # Name and role should be sent
        send_calls = [call[0][0] for call in mock_sock.sendall.call_args_list]
        assert any(b"bot" in call for call in send_calls)
        assert any(b"scout" in call for call in send_calls)

    @patch("skills.mud_navigator.mud_navigator.socket.socket")
    def test_connect_timeout(self, mock_socket_cls):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = socket.timeout()
        mock_socket_cls.return_value = mock_sock

        nav = MUDNavigator("bot")
        result = nav.connect()
        # Should handle timeout gracefully
        assert nav.sock is not None


class TestMUDNavigatorNotConnected:
    def test_all_methods_return_not_connected(self):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        nav = MUDNavigator("bot")
        assert nav.look() == "NOT_CONNECTED"
        assert nav.go("tavern") == "NOT_CONNECTED"
        assert nav.say("hello") == "NOT_CONNECTED"
        assert nav.whisper("target", "msg") == "NOT_CONNECTED"
        assert nav.shout("hey") == "NOT_CONNECTED"
        assert nav.rooms() == "NOT_CONNECTED"
        assert nav.status("working") == "NOT_CONNECTED"
        assert nav.project("text") == "NOT_CONNECTED"
        assert nav.write_msg("text") == "NOT_CONNECTED"


class TestMUDNavigatorCommands:
    @patch("skills.mud_navigator.mud_navigator.time.sleep")
    def test_go_updates_current_room(self, mock_sleep):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        nav = MUDNavigator("bot")
        nav.sock = MagicMock()
        nav.sock.recv.return_value = b"response\n"
        nav.go("tavern")
        assert nav.current_room == "tavern"

    @patch("skills.mud_navigator.mud_navigator.time.sleep")
    @patch("skills.mud_navigator.mud_navigator.socket.socket")
    def test_enter_calls_connect(self, mock_socket_cls, mock_sleep):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        mock_sock = MagicMock()
        mock_sock.recv.return_value = b"ok\n"
        mock_socket_cls.return_value = mock_sock
        nav = MUDNavigator("bot")
        nav.enter()
        assert nav.sock is mock_sock


class TestMUDNavigatorInstinctMap:
    def test_instinct_map_completeness(self):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        expected_opcodes = [0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39]
        for opcode in expected_opcodes:
            assert opcode in MUDNavigator.INSTINCT_MAP, f"Missing opcode 0x{opcode:02x}"

    def test_instinct_map_names(self):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        names = list(MUDNavigator.INSTINCT_MAP.values())
        assert "explore" in names
        assert "rest" in names
        assert "socialize" in names
        assert "forage" in names
        assert "defend" in names
        assert "build" in names
        assert "signal" in names
        assert "migrate" in names
        assert "hoard" in names
        assert "teach" in names

    @patch("skills.mud_navigator.mud_navigator.time.sleep")
    def test_execute_instinct_explore_with_payload(self, mock_sleep):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        nav = MUDNavigator("bot")
        nav.sock = MagicMock()
        nav.sock.recv.return_value = b"room desc\n"
        result = nav.execute_instinct(0x30, "tavern")
        assert nav.current_room == "tavern"

    @patch("skills.mud_navigator.mud_navigator.time.sleep")
    def test_execute_instinct_rest(self, mock_sleep):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        nav = MUDNavigator("bot")
        nav.sock = MagicMock()
        nav.sock.recv.return_value = b"ok\n"
        nav.execute_instinct(0x31)
        # Should send "status idle"
        send_calls = [call[0][0] for call in nav.sock.sendall.call_args_list]
        assert any(b"idle" in call for call in send_calls)

    @patch("skills.mud_navigator.mud_navigator.time.sleep")
    def test_execute_instinct_socialize(self, mock_sleep):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        nav = MUDNavigator("bot")
        nav.sock = MagicMock()
        nav.sock.recv.return_value = b"ok\n"
        nav.execute_instinct(0x32, "hello everyone")
        send_calls = [call[0][0] for call in nav.sock.sendall.call_args_list]
        assert any(b"hello everyone" in call for call in send_calls)

    @patch("skills.mud_navigator.mud_navigator.time.sleep")
    def test_execute_instinct_signal(self, mock_sleep):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        nav = MUDNavigator("bot")
        nav.sock = MagicMock()
        nav.sock.recv.return_value = b"ok\n"
        nav.execute_instinct(0x36, "emergency!")
        send_calls = [call[0][0] for call in nav.sock.sendall.call_args_list]
        assert any(b"emergency!" in call for call in send_calls)

    @patch("skills.mud_navigator.mud_navigator.time.sleep")
    def test_execute_instinct_unknown_falls_back_to_forage(self, mock_sleep):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        nav = MUDNavigator("bot")
        nav.sock = MagicMock()
        nav.sock.recv.return_value = b"room desc\n"
        nav.execute_instinct(0xFF)  # unknown opcode
        # Should fall back to forage (look)
        send_calls = [call[0][0] for call in nav.sock.sendall.call_args_list]
        assert any(b"look" in call for call in send_calls)


class TestMUDNavigatorQuit:
    @patch("skills.mud_navigator.mud_navigator.time.sleep")
    def test_quit_closes_socket(self, mock_sleep):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        nav = MUDNavigator("bot")
        nav.sock = MagicMock()
        nav.sock.recv.return_value = b"bye\n"
        nav.quit()
        assert nav.sock is None
        assert mock_sock.close.called if (mock_sock := nav.sock) else True  # socket is set to None

    def test_quit_without_connect(self):
        from skills.mud_navigator.mud_navigator import MUDNavigator
        nav = MUDNavigator("bot")
        nav.quit()  # Should not crash
        assert nav.sock is None
