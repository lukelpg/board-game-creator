# net/sync.py
"""
Tiny TCP JSON message bus for local-network board sync.
1 host  : GameServer (runs in a thread; shares one queue with UI)
N clients: GameClient (one per app window)
"""
from __future__ import annotations
import json, socket, threading, queue, time

PORT     = 50007           # change if you need
BUFSIZE  = 4096

# ------------------------------------------------------------------ #
class GameServer(threading.Thread):
    def __init__(self, outbound: queue.Queue[str]):
        super().__init__(daemon=True)
        self.out_q = outbound      # UI puts outbound messages here
        self.in_q  = queue.Queue() # UI reads inbound messages here
        self.socks: list[socket.socket] = []
        self.running = True

    def run(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("", PORT)); srv.listen()
        srv.settimeout(0.2)
        threading.Thread(target=self._pump_out, daemon=True).start()
        while self.running:
            try:
                cli, _ = srv.accept()
                cli.settimeout(0.2)
                self.socks.append(cli)
                cli.sendall(b'{"act":"hello"}') 
            except socket.timeout:
                pass
            self._pump_in()
        srv.close()

    # ---------- internal helpers ----------------------------------- #
    def _pump_in(self):
        for s in list(self.socks):
            try:
                data = s.recv(BUFSIZE)
                if not data:
                    self.socks.remove(s); s.close(); continue
                self.in_q.put(data.decode())
            except socket.timeout:
                continue
            except OSError:
                self.socks.remove(s)

    def _pump_out(self):
        while self.running:
            try:
                msg = self.out_q.get(timeout=0.2)
            except queue.Empty:
                continue
            dead = []
            for s in self.socks:
                try: s.sendall(msg.encode())
                except OSError: dead.append(s)
            for s in dead:
                self.socks.remove(s)

    def stop(self): self.running = False


# ------------------------------------------------------------------ #
class GameClient(threading.Thread):
    def __init__(self, host_ip: str, outbound: queue.Queue[str]):
        super().__init__(daemon=True)
        self.host_ip = host_ip.strip() or "localhost"
        self.out_q = outbound
        self.in_q  = queue.Queue()
        self.running = True
        self.error: str | None = None          # ← store last error

    def run(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((self.host_ip, PORT))
            sock.settimeout(0.2)
            sock.sendall(b'{"act":"hello"}') 
        except (socket.gaierror, ConnectionRefusedError, TimeoutError) as e:
            self.error = f"Connection failed: {e}"
            return

        threading.Thread(target=self._pump_out, args=(sock,), daemon=True).start()
        while self.running:
            try:
                data = sock.recv(BUFSIZE)
                if not data:
                    break
                self.in_q.put(data.decode())
            except socket.timeout:
                continue
            except OSError:
                break
        sock.close()

    def _pump_out(self, sock):
        while self.running:
            try:
                msg = self.out_q.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                sock.sendall(msg.encode())
            except OSError:
                break

    def stop(self): self.running = False
