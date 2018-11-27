import comm
import socket
import en_core_web_lg


nlp = en_core_web_lg.load()


def process_connection(sock):
    # receive data from the client
    data = comm.receive_data(sock)
    # do something with the data
    result = nlp(data)
    # send the result back to the client
    comm.send_data(result, sock)
    # close the socket with this particular client
    sock.close()


server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# open socket even if it was used recently (e.g., server restart)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind((comm.server_host, comm.server_port))
# queue up to 5 connections
server_sock.listen(5)
print("Listening on port {}...".format(comm.server_port))
try:
    while True:
        # accept connections from clients
        (client_sock, address) = server_sock.accept()
        # process this connection
        # (this could be launched in a separate thread or process)
        process_connection(client_sock)
except KeyboardInterrupt:
    print("Server process terminated.")
finally:
    server_sock.close()
