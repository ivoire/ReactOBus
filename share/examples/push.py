import sys
import zmq
from zmq.utils.strtypes import b

def main():
    # Get the arguments
    if len(sys.argv) != 4:
        print("Usage: push.py url topic num_messages")
        sys.exit(1)

    url = sys.argv[1]
    topic = sys.argv[2]
    num_messages = int(sys.argv[3])

    # Create the socket
    context = zmq.Context()
    sock = context.socket(zmq.PUSH)
    sock.connect(url)

    for i in range(0, num_messages):
        sock.send_multipart([b(topic), b("id"), b(str(i))])


if __name__ == "__main__":
    main()
