import logging
import socket
import threading

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def handle_client(connection, client_address, connection_type: str):
    """Handle a client connection."""
    try:
        logging.info(f"New {connection_type} connection from {client_address}")
        while True:
            data = connection.recv(1024)
            if data:
                logging.info(f"Received from {client_address}: {data.decode()}")
                # Echo back the received data
                connection.sendall(data)
                if connection_type == "short-lived":
                    break
            else:
                break
    finally:
        connection.close()
        logging.info(f"{connection_type} connection with {client_address} closed.")


def start_server(port: int, connection_type: str):
    """Starts a server to listen for connections on a specific port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("", port))
        server_socket.listen()
        logging.info(f"{connection_type.capitalize()} server listening on port {port}")

        while True:
            connection, client_address = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client, args=(connection, client_address, connection_type)
            )
            client_thread.daemon = True
            client_thread.start()


if __name__ == "__main__":
    # Port numbers for long-lived and short-lived connections
    long_lived_port: int = 12345
    short_lived_port: int = 54321

    # Start long-lived connection server in a separate thread
    long_lived_thread = threading.Thread(
        target=start_server, args=(long_lived_port, "long-lived"), daemon=True
    )
    long_lived_thread.start()

    # Start short-lived connection server in the main thread
    start_server(short_lived_port, "short-lived")
