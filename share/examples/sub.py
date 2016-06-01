import sys
import zmq


def main():
    # Get the arguments
    if len(sys.argv) != 2:
        print("Usage: sub.py url")
        sys.exit(1)

    url = sys.argv[1]

    context = zmq.Context()
    sock = context.socket(zmq.SUB)
    sock.setsockopt(zmq.SUBSCRIBE, b"")
    sock.connect(url)

    while True:
        msg = sock.recv_multipart()
        print(msg)

if __name__ == "__main__":
    main()
