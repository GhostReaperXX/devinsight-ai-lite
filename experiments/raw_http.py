"""HTTP is text sent over a connection. Speak it by hand to see exactly what travels.

Run from the project root: python experiments/raw_http.py example.com
"""

import socket
import ssl
import sys


def fetch(host: str, use_tls: bool) -> str:
    """Open a connection, send one request as text, and return the raw response."""
    request = f"GET / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
    port = 443 if use_tls else 80

    with socket.create_connection((host, port), timeout=10) as connection:
        if use_tls:
            context = ssl.create_default_context()
            with context.wrap_socket(connection, server_hostname=host) as secure:
                print(f"TLS version: {secure.version()}")
                subject = dict(item[0] for item in secure.getpeercert()["subject"])
                print(f"Certificate issued to: {subject}")
                secure.sendall(request.encode("ascii"))
                return read_all(secure)
        connection.sendall(request.encode("ascii"))
        return read_all(connection)


def read_all(connection) -> str:
    chunks = []
    while chunk := connection.recv(4096):
        chunks.append(chunk)
    return b"".join(chunks).decode("utf-8", errors="replace")


def show(title: str, response: str) -> None:
    head = response.split("\r\n\r\n", maxsplit=1)[0]
    print(f"--- {title} ---")
    print(head)
    print()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    show("over plain HTTP (port 80)", fetch(target, use_tls=False))
    show("over HTTPS (port 443)", fetch(target, use_tls=True))
