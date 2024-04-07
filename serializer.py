from io import BytesIO
import tokenize


def read(f: BytesIO, n: int) -> bytes:
    """
    Read `n` bytes from IO object f.

    params:
    -------
            - BytesIO f: input to read from
            - int     n: number of bytes to read

    return:
    -------
            Return bytes read
    """

    if type(n) == str or type(n) == bytes:
        n = int(n)

    buff = b""
    for _ in range(n):
        buff += f.read(1)
    return buff


def readuntil(f: BytesIO, s: bytes) -> bytes:
    """
    Read bytes from IO object f until sentinel is found.

    params:
    -------
            - BytesIO f: input to read from
            - bytes   s: sentinel bytes to read until

    return:
    -------
            Return bytes up to (and including) the sentinel
    """

    if type(s) == str:
        s = s.encode()

    buff = b""
    sent = b""

    while len(sent) < len(s) and (c := read(f, 1)):
        buff += c
        sent += c

    if len(sent) != len(s) or sent == s:
        return buff

    while (c := read(f, 1)) and (sent := sent[1:] + c) and sent != s:
        buff += c
    buff += c
    return buff


def lax_deserialize(b: bytes) -> list:
    """
    Not meant to be used, use `deserialize` instead.
    Convert a malformed serialized redis command to its plaintext version.

    params:
    -------
            - bytes b: malformed serialized command to decoded

    return:
    -------
            Return the decoded command as a list of keywords

    example:
    --------
            b'azeazeazeaez*2\r\npadpadpad$7\r\nCOMMANDteehee\r\n$4\r\nDOCS\r\n' -> [b'COMMAND', b'DOCS']

    """

    f = BytesIO(b)

    l = []

    readuntil(f, "*")
    argcount = int(readuntil(f, "\r\n"))

    for _ in range(argcount):
        readuntil(f, "$")
        arglen = int(readuntil(f, "\r\n"))

        argval = read(f, arglen)
        readuntil(f, "\r\n")
        print(argval)
        l.append(argval)

    return l


def deserialize(b: bytes) -> list:
    """
    Convert a serialized redis command to its plaintext version.

    params:
    -------
            - bytes b: serialized command to decoded

    return:
    -------
            Return the decoded command as a list of keywords

    example:
    --------
            b'*2\r\n$7\r\nCOMMAND\r\n$4\r\nDOCS\r\n' -> [b'COMMAND', b'DOCS']

    """

    f = BytesIO(b)

    l = []

    assert read(f, 1) == b"*"

    argcount = int(readuntil(f, "\r\n"))

    for _ in range(argcount):
        assert read(f, 1) == b"$"
        arglen = int(readuntil(f, "\r\n"))

        argval = read(f, arglen + 2).strip(b"\r\n")

        l.append(argval)

    return l


def serialize(b: list) -> bytes:
    """
    Serialized a redis command.

    params:
    -------
            - list b: a list of keywords to serialize

    return:
    -------
            Return the serialized command

    example:
    --------
            [b'COMMAND', b'DOCS'] -> b'*2\r\n$7\r\nCOMMAND\r\n$4\r\nDOCS\r\n'

    """

    l = b"*" + str(len(b)).encode() + b"\r\n"

    for argval in b:
        l += b"$" + str(len(argval)).encode() + b"\r\n"
        l += argval + b"\r\n"

    return l


def is_serialized(b: bytes) -> bool:
    """
    Check if input is serialized or not.

    params:
    -------
            - bytes b: input to check

    return:
    -------
            Return if the input is a serialized redis string or not

    example:
    --------
            b'*2\r\n$7\r\nCOMMAND\r\n$4\r\nDOCS\r\n' -> true
            b'keys *\n'                              -> false

    """
    try:
        deserialize(b)
        return True
    except Exception:
        return False


"""
Byte string tokenizer, why was this so hard to find ??
"""
token = lambda d: [
    b.encode() for _, b, _, _, e in tokenize.tokenize(BytesIO(d.strip()).readline) if e
]

if __name__ == "__main__":
    payload = b"*3\r\n$3\r\nset\r\n$6\r\ncoucou\r\n$4\r\nbite\r\n"
    print(payload == serialize(deserialize(payload)))
