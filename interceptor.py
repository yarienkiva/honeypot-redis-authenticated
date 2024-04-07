from serializer import deserialize, is_serialized, token
import csv


def interceptor(d: bytes, a_src: list) -> bytes:
    try:
        data = deserialize(d) if is_serialized(d) else token(d)

        if (
            d.isascii()
            and (data[0].upper() == b"AUTH" and 2 <= len(data) <= 3)
            or (
                (
                    data[0].upper() == b"HELLO"
                    and data[2].upper() == b"AUTH"
                    and len(data) == 5
                )
            )
        ):
            if len(data) == 3:
                row = [a_src[0], data[1].decode(), data[2].decode()]
            elif len(data) == 5:
                row = [a_src[0], data[3].decode(), data[4].decode()]
            else:
                row = [a_src[0], "", data[1].decode()]

            print(row)

            with open("auth.log", "a") as f:
                wr = csv.writer(f, quoting=csv.QUOTE_ALL)
                wr.writerow(row)

        print(d[:50])
        with open(f"payload_{a_src[0]}:{a_src[1]}.log", "ab") as f:
            f.write(d)

    except Exception as e:
        with open("err.log", "ab") as f:
            f.write(b"------------------------------------------------------\n")
            f.write(b"IP: " + a_src[0].encode() + b"\n")
            f.write(b"ERR: " + str(e).encode() + b"\n")
            f.write(d + b"\n")
    return d
