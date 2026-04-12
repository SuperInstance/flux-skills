#!/usr/bin/env python3
"""MUD Navigator — Python adapter for FLUX MUD skill."""
import socket
import time


class MUDNavigator:
    def __init__(self, name, role="greenhorn", host="localhost", port=7777):
        self.name = name
        self.role = role
        self.host = host
        self.port = port
        self.sock = None
        self.current_room = "harbor"

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(3)
        self.sock.connect((self.host, self.port))
        time.sleep(0.5)
        try: self.sock.recv(8192)
        except socket.timeout: pass
        self.sock.sendall(f"{self.name}\n".encode())
        time.sleep(0.5)
        try: self.sock.recv(8192)
        except socket.timeout: pass
        self.sock.sendall(f"{self.role}\n".encode())
        time.sleep(0.5)
        try: return self.sock.recv(8192).decode(errors='replace')
        except socket.timeout: return ""

    def _cmd(self, cmd):
        if not self.sock: return "NOT_CONNECTED"
        self.sock.sendall(f"{cmd}\n".encode())
        time.sleep(0.5)
        try: return self.sock.recv(8192).decode(errors='replace')
        except socket.timeout: return ""

    def enter(self): return self.connect()
    def look(self): return self._cmd("look")
    def go(self, room):
        r = self._cmd(f"go {room}")
        self.current_room = room
        return r
    def say(self, msg): return self._cmd(f"say {msg}")
    def whisper(self, agent, msg): return self._cmd(f"whisper {agent} {msg}")
    def shout(self, msg): return self._cmd(f"shout {msg}")
    def rooms(self): return self._cmd("rooms")
    def status(self, state="working"): return self._cmd(f"status {state}")
    def project(self, text): return self._cmd(f"project {text}")
    def write_msg(self, text): return self._cmd(f"write {text}")
    def quit(self):
        r = self._cmd("quit")
        if self.sock: self.sock.close(); self.sock = None
        return r

    INSTINCT_MAP = {
        0x30: "explore", 0x31: "rest", 0x32: "socialize", 0x33: "forage",
        0x34: "defend", 0x35: "build", 0x36: "signal", 0x37: "migrate",
        0x38: "hoard", 0x39: "teach",
    }

    def execute_instinct(self, opcode, payload=""):
        inst = self.INSTINCT_MAP.get(opcode, "forage")
        if inst == "explore": return self.go(payload) if payload else self._cmd("wander")
        elif inst == "rest": return self.status("idle")
        elif inst == "socialize": return self.say(payload or "...")
        elif inst == "forage": return self.look()
        elif inst == "signal": return self.shout(payload or "beacon")
        elif inst == "migrate": return self._cmd("wander")
        else: return self.look()


if __name__ == "__main__":
    nav = MUDNavigator("skill_tester", "greenhorn")
    print(nav.enter()[:100])
    print(nav.go("tavern")[:100])
    print(nav.say("MUD Navigator skill test!"))
    print(nav.project("MUD Navigator v1.0 — FLUX skill"))
    print(nav.rooms()[:80])
    nav.quit()
    print("✅ MUD Navigator working")
