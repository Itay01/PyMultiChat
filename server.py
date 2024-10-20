import socket
import threading
from datetime import datetime

# Server configuration
HOST = '127.0.0.1'  # IP address to listen on
PORT = 12345  # Port to listen on

# Global variables to keep track of clients and their information
clients = []  # List of client sockets
usernames = {}  # Dictionary mapping client sockets to usernames
client_addresses = {}  # Dictionary mapping client sockets to their addresses
managers = ["Itay"]  # List of manager usernames
muted_users = []  # List of muted usernames


class MessageParser:
    """Parses messages received from clients."""

    def __init__(self, data):
        self.data = data  # The raw data string to parse
        self.idx = 0  # Current index in the data string

    def read_int(self):
        """Reads an integer from the data string starting at the current index."""
        num_str = ''
        while self.idx < len(self.data) and self.data[self.idx].isdigit():
            num_str += self.data[self.idx]
            self.idx += 1

        if not num_str:
            raise ValueError(f"Expected integer value at position {self.idx}")
        return int(num_str)

    def read_string(self, length):
        """Reads a string of the given length from the data string starting at the current index."""
        if self.idx + length > len(self.data):
            raise ValueError(f"Expected string of length {length} at position {self.idx}")

        result = self.data[self.idx:self.idx + length]
        self.idx += length
        return result


def get_timestamp():
    """Returns the current time formatted as 'HH:MM'."""
    return datetime.now().strftime('%H:%M')


def safe_send(client_socket, message):
    """Sends a message to the client socket safely, handling exceptions."""
    try:
        message_len = str(len(message))
        message = message_len + message  # Prepend the length of the message
        client_socket.send(message.encode())
    except Exception:
        cleanup_client(client_socket)


def get_client_socket_by_username(username):
    """Retrieves the client socket associated with the given username."""
    for client, uname in usernames.items():
        if uname == username:
            return client
    return None


def is_manager(username):
    """Checks if the username belongs to a manager."""
    return username in managers


def broadcast(message, sender_socket=None):
    """Sends a message to all connected clients except the sender."""
    for client in clients:
        if client != sender_socket and client in usernames:
            safe_send(client, message)


def cleanup_client(client_socket):
    """Removes a client from all tracking structures and notifies others."""
    if client_socket in clients:
        clients.remove(client_socket)

    username = usernames.pop(client_socket, None)
    if username:
        if username in muted_users:
            muted_users.remove(username)

        timestamp = get_timestamp()
        message = f"{timestamp} {username} has left the chat!"
        broadcast(message)
    client_address = client_addresses.pop(client_socket, "Unknown")
    print(f"Client disconnected: {client_address}")
    client_socket.close()


def send_private_message(sender_socket, sender_username, recipient_username, message):
    """Sends a private message from one user to another."""
    recipient_socket = get_client_socket_by_username(recipient_username)
    if recipient_socket is None:
        safe_send(sender_socket, f"User {recipient_username} not found.")
        return True

    timestamp = get_timestamp()
    formatted_message = f"{timestamp} !{sender_username}: {message}"
    safe_send(sender_socket, formatted_message)
    safe_send(recipient_socket, formatted_message)
    return True


def handle_send_message(client_socket, parser, username):
    """Handles sending a message from a client to the chat or another user."""
    msg_len = parser.read_int()
    message = parser.read_string(msg_len)

    if message.strip() == "quit":
        return False  # Client wants to quit the chat

    if username in muted_users:
        safe_send(client_socket, "You cannot speak here.")
        return True

    if message.strip() == "managers-view":
        # Client requested the list of managers
        managers_list = ', '.join([f"@{mgr}" for mgr in managers])
        safe_send(client_socket, f"Managers: {managers_list}")
        return True

    if message.startswith('!'):
        # Private message format: '!recipient_username message'
        exclamation_idx = message.find(' ')
        if exclamation_idx == -1:
            safe_send(client_socket, "Invalid private message format.")
            return True

        recipient_username = message[1:exclamation_idx]
        private_message = message[exclamation_idx + 1:]
        return send_private_message(client_socket, username, recipient_username, private_message)

    # Broadcast the message to all other clients
    timestamp = get_timestamp()
    prefix = f"@{username}" if is_manager(username) else username
    formatted_message = f"{timestamp} {prefix}: {message}"
    broadcast(formatted_message, sender_socket=client_socket)
    return True


def handle_promote_user(client_socket, parser, username):
    """Handles promoting another user to manager status."""
    if not is_manager(username):
        safe_send(client_socket, "Only managers can promote users.")
        return True

    target_uname_len = parser.read_int()
    target_username = parser.read_string(target_uname_len)

    if target_username not in managers:
        managers.append(target_username)
        safe_send(client_socket, f"{target_username} has been promoted to manager.")
    else:
        safe_send(client_socket, f"{target_username} is already a manager.")
    return True


def handle_kick_user(client_socket, parser, username):
    """Handles kicking a user out of the chat."""
    if not is_manager(username):
        safe_send(client_socket, "Only managers can kick users.")
        return True

    target_uname_len = parser.read_int()
    target_username = parser.read_string(target_uname_len)
    target_socket = get_client_socket_by_username(target_username)

    if target_socket:
        safe_send(target_socket, "You have been kicked from the chat.")
        cleanup_client(target_socket)
        timestamp = get_timestamp()
        message = f"{timestamp} {target_username} has been kicked from the chat!"
        broadcast(message)
    else:
        safe_send(client_socket, f"User {target_username} not found.")
    return True


def handle_mute_user(client_socket, parser, username):
    """Handles muting a user in the chat."""
    if not is_manager(username):
        safe_send(client_socket, "Only managers can mute users.")
        return True

    target_uname_len = parser.read_int()
    target_username = parser.read_string(target_uname_len)

    if target_username not in muted_users:
        muted_users.append(target_username)
        safe_send(client_socket, f"{target_username} has been muted.")
        target_socket = get_client_socket_by_username(target_username)
        if target_socket:
            safe_send(target_socket, "You have been muted by a manager.")
    else:
        safe_send(client_socket, f"{target_username} is already muted.")
    return True


def handle_private_message(client_socket, parser, username):
    """Handles sending a private message to another user."""
    if username in muted_users:
        safe_send(client_socket, "You cannot speak here.")
        return True

    recipient_uname_len = parser.read_int()
    recipient_username = parser.read_string(recipient_uname_len)
    msg_len = parser.read_int()
    message = parser.read_string(msg_len)
    return send_private_message(client_socket, username, recipient_username, message)


# Mapping of action codes to their corresponding handler functions
action_handlers = {
    1: handle_send_message,
    2: handle_promote_user,
    3: handle_kick_user,
    4: handle_mute_user,
    5: handle_private_message,
}


def handle_client(client_socket):
    """Main function to handle communication with a connected client."""
    try:
        # Initial data reception (expected to contain the username)
        data = client_socket.recv(4096).decode()
        if not data:
            cleanup_client(client_socket)
            return

        parser = MessageParser(data)

        # Read the length and value of the username
        uname_len = parser.read_int()
        username = parser.read_string(uname_len)

        # Validate the username
        if username.startswith('@'):
            safe_send(client_socket, "Username cannot start with '@'.")
            cleanup_client(client_socket)
            return

        # Store the username associated with the client socket
        usernames[client_socket] = username

        # Notify other clients about the new user
        timestamp = get_timestamp()
        join_message = f"{timestamp} {username} has joined the chat!"
        broadcast(join_message)

        # Main loop to handle incoming messages from the client
        while True:
            try:
                data = client_socket.recv(4096).decode()
                if not data:
                    break

                parser = MessageParser(data)
                uname_len = parser.read_int()
                sent_username = parser.read_string(uname_len)

                # Check if the username matches
                if sent_username != usernames[client_socket]:
                    safe_send(client_socket, "Username mismatch.")
                    continue

                # Read the action code
                if parser.idx >= len(data):
                    safe_send(client_socket, "Missing action code.")
                    continue
                action_code = int(data[parser.idx])
                parser.idx += 1

                # Get the handler function based on the action code
                handler = action_handlers.get(action_code)
                if handler:
                    continue_session = handler(client_socket, parser, username)
                    if not continue_session:
                        break  # Exit the loop if the handler signals to stop
                else:
                    safe_send(client_socket, "Invalid action code.")
            except Exception:
                break  # Exit the loop on exception

        cleanup_client(client_socket)
    except Exception:
        cleanup_client(client_socket)


def accept_connections():
    """Accepts new client connections and starts a new thread for each client."""
    while True:
        client_socket, client_address = server.accept()
        clients.append(client_socket)
        client_addresses[client_socket] = client_address
        print(f"Client connected: {client_address}")

        # Start a new thread to handle the client
        thread = threading.Thread(target=handle_client, args=(client_socket,), daemon=True)
        thread.start()


# Setting up the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print(f"Server started on {HOST}:{PORT}")

# Start accepting connections
accept_connections()
