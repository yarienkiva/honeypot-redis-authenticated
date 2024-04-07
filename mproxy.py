import threading
import socket
import select
import sys
import os

import docker

from interceptor import interceptor


class Server:
    def __init__(self, host):
        self.BUFFER_SIZE = 2**20
        self.THREAD_TIMEOUT = 60 * 60 * 24
        self.DOCKER_HOST = host

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(("", 6379))
        self.s.listen(1)

    def loop_forever(self):
        while True:
            s_src, a_src = self.s.accept()
            print(f"{a_src[0]}:{a_src[1]} >con")

            d = threading.Thread(target=self.proxy_thread, args=(s_src, a_src))
            d.setDaemon(True)
            d.start()

        self.s.close()

    def proxy_thread(self, s_src, a_src):
        s_dst = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_dst.connect(self.DOCKER_HOST)

        def done():
            print(f"{a_src[0]}:{a_src[1]} <dis")
            s_src.close()
            s_dst.close()

        while True:
            s_read, _, _ = select.select([s_src, s_dst], [], [], self.THREAD_TIMEOUT)

            if not s_read:
                return done()

            for s in s_read:
                try:
                    data = s.recv(self.BUFFER_SIZE)
                    assert len(data)

                    if s == s_src:
                        s_dst.sendall(interceptor(data, a_src))

                    elif s == s_dst:
                        s_src.sendall(data)
                except Exception as e:
                    return done()


client = docker.from_env()
container = client.containers.run(
    "redis:latest",
    ["redis-server", "--requirepass", os.urandom(16).hex()],
    # name="redis",
    remove=True,
    detach=True,
)

while container.status != "running":
    container.reload()

ip = container.attrs["NetworkSettings"]["IPAddress"]
port = int([*container.attrs["NetworkSettings"]["Ports"]][0].strip("/tcp"))

print("Started server, looping...")

try:
    server = Server((ip, port))
    server.loop_forever()
except KeyboardInterrupt as e:
    container.kill()

print("Stopped server, bye bye...")
