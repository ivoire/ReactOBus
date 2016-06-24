import datetime
import json
import os
import pwd
import sys
import uuid
import zmq
import zmq.auth
from zmq.utils.strtypes import b

def main():
    # Get the arguments
    if len(sys.argv) != 4 and len(sys.argv) != 6:
        print("%d arguments" % len(sys.argv))
        print("Usage: push.py url topic num_messages [master_cert slave_cert]")
        sys.exit(1)

    url = sys.argv[1]
    topic = sys.argv[2]
    num_messages = int(sys.argv[3])
    username = pwd.getpwuid(os.geteuid()).pw_name

    # Create the socket
    context = zmq.Context()
    sock = context.socket(zmq.PUSH)
    if len(sys.argv) > 4:
        # Configure encryption
        (server_public, _) = zmq.auth.load_certificate(sys.argv[4])
        sock.curve_serverkey = server_public

        (client_public, client_private) = zmq.auth.load_certificate(sys.argv[5])
        sock.curve_publickey = client_public
        sock.curve_secretkey = client_private

    sock.connect(url)

    for i in range(0, num_messages):
        sock.send_multipart([b(topic),
                             b(str(uuid.uuid1())),
                             b(datetime.datetime.utcnow().isoformat()),
                             b(username),
                             b(json.dumps({'id': i}))])


if __name__ == "__main__":
    main()
