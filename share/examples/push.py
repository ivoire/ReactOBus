import json
import os
import pwd
import sys
import uuid
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
    username = pwd.getpwuid(os.geteuid()).pw_name

    # Create the socket
    context = zmq.Context()
    sock = context.socket(zmq.PUSH)
    sock.connect(url)

    for i in range(0, num_messages):
        sock.send_multipart([b(topic),
                             b(str(uuid.uuid1())),
                             b(username),
                             b(json.dumps({'id': i}))])


if __name__ == "__main__":
    main()
