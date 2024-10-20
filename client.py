import socket
import threading
import sys
import queue

# Server configuration
HOST = '127.0.0.1'  # Server IP address (localhost)
PORT = 12345  # Port to connect to


def receive_messages(sock, exit_event):
    """
    Function to receive messages from the server.
    Runs in a separate thread and listens for incoming messages.
    """
    while not exit_event.is_set():
        try:
            # Receive data from the server
            data = sock.recv(4096).decode()
            if data:
                # Initialize index to parse the message length
                message_len_idx = 0

                # Parse the message length from the received data
                while (data[message_len_idx].isdigit() and
                       int("".join(data[:message_len_idx + 1])) <
                       len(data[message_len_idx + 1:])):
                    message_len_idx += 1

                # Extract the message length and the actual message
                message_len = int("".join(data[:message_len_idx + 1]))
                message_start = message_len_idx + 1
                message_end = message_start + message_len
                message = data[message_start:message_end]

                # Verify that the message length matches the expected length
                if len(message) != message_len:
                    print("Something went wrong while reading the message.")
                    continue

                # Display the received message
                print(message)

                # Check if the client has been kicked from the chat
                if message == "You have been kicked from the chat.":
                    exit_event.set()
                    sock.close()
            else:
                # Server has closed the connection
                print("Connection closed by the server.")
                exit_event.set()
                sock.close()
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            # Handle connection errors
            exit_event.set()
            sock.close()


def input_thread_func(input_queue, exit_event):
    """
    Function to handle user input.
    Runs in a separate thread to avoid blocking the main thread.
    """
    while not exit_event.is_set():
        try:
            # Get user input and put it in the queue
            user_input = input()
            input_queue.put(user_input)
        except (EOFError, Exception):
            # Handle end-of-file or other exceptions
            exit_event.set()


def send_message(sock, username, action_code, target="", message=""):
    """
    Function to send a message to the server.
    Constructs the message according to the protocol and sends it.
    """
    try:
        # Calculate lengths of username, target, and message
        uname_len = str(len(username))
        target_len = str(len(target))
        msg_len = str(len(message))

        # Construct the data packet
        data = uname_len + username + action_code + target_len + target + msg_len + message

        # Send the encoded data to the server
        sock.send(data.encode())
    except Exception as e:
        print(f"Error sending message: {e}")


def main():
    """Main function to start the client and handle user interactions."""
    try:
        # Create a socket and connect to the server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
    except Exception as e:
        print(f"Unable to connect to server: {e}")
        return

    # Prompt the user to enter a username
    username = input("Enter your username: ")
    if username.startswith('@'):
        print("Username cannot start with '@'.")
        return

    # Send the username to the server to register
    send_message(client_socket, username, '0')

    # Create an event to signal when the client should exit
    exit_event = threading.Event()
    # Create a queue to handle input from the user
    input_queue = queue.Queue()

    # Start a thread to receive messages from the server
    threading.Thread(target=receive_messages, args=(client_socket, exit_event), daemon=True).start()

    # Start a thread to read user input without blocking
    threading.Thread(target=input_thread_func, args=(input_queue, exit_event), daemon=True).start()

    # Main loop to process user input and send messages
    while not exit_event.is_set():
        try:
            # Wait for the next input from the user
            message = input_queue.get(timeout=1)

            if message.strip() == "quit":
                # User wants to quit the chat
                send_message(client_socket, username, '1', message=message)
                exit_event.set()
            elif message.startswith("/promote "):
                # Promote another user to manager
                target_username = message[len("/promote "):].strip()
                send_message(client_socket, username, '2', message=target_username)
            elif message.startswith("/kick "):
                # Kick a user from the chat
                target_username = message[len("/kick "):].strip()
                send_message(client_socket, username, '3', message=target_username)
            elif message.startswith("/mute "):
                # Mute a user in the chat
                target_username = message[len("/mute "):].strip()
                send_message(client_socket, username, '4', message=target_username)
            elif message.startswith("/msg "):
                # Send a private message to another user
                parts = message.split(' ', 2)
                if len(parts) == 3:
                    recipient_username = parts[1]
                    private_message = parts[2]
                    send_message(client_socket, username, '5', recipient_username, private_message)
                else:
                    print("Invalid private message format. Use: /msg username message")
            else:
                # Send a general message to the chat
                send_message(client_socket, username, '1', message=message)
        except queue.Empty:
            # Continue the loop if no input is received
            continue

    # Close the client socket and exit the program
    client_socket.close()
    sys.exit()


if __name__ == "__main__":
    main()
