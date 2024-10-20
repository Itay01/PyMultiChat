# PyMultiChat

PyMultiChat is a simple multi-client chat application built with Python's socket and threading modules. It consists of a server and multiple clients that allow users to communicate in real-time. The application supports features like private messaging, user management by managers, and message broadcasting.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Running the Server](#running-the-server)
  - [Connecting a Client](#connecting-a-client)
  - [Client Commands](#client-commands)
  - [Notes](#notes)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
  - [Server](#server)
  - [Client](#client)

---

## Features

- **Multi-user Support**: Multiple clients can connect to the server simultaneously.
- **Private Messaging**: Send direct messages to specific users.
- **User Roles**:
  - **Managers**: Users with special privileges to promote, kick, or mute other users.
  - **Regular Users**: Standard users who can send and receive messages.
- **Message Broadcasting**: Messages can be sent to all connected clients.
- **User Commands**:
  - `/promote username`: Promote a user to manager.
  - `/kick username`: Remove a user from the chat.
  - `/mute username`: Prevent a user from sending messages.
  - `/msg username message`: Send a private message to a user.
  - `quit`: Exit the chat application.

## Requirements

- Python 3.x

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/PyMultiChat.git
   ```

2. **Navigate to the Project Directory**

   ```bash
   cd PyMultiChat
   ```

## Usage

### Running the Server

1. Open a terminal window.

2. Navigate to the project directory if not already there.

3. Run the server script:

   ```bash
   python server.py
   ```

   The server will start and listen on `127.0.0.1:12345`.

### Connecting a Client

1. Open a new terminal window for each client you wish to connect.

2. Navigate to the project directory.

3. Run the client script:

   ```bash
   python client.py
   ```

4. When prompted, enter a username (usernames cannot start with `@`).

### Client Commands

- **Send a Message**: Type your message and press `Enter` to send it to all users.
- **Private Message**: Use the format `/msg username message` to send a private message.
- **Promote User**: Managers can promote a user using `/promote username`.
- **Kick User**: Managers can kick a user using `/kick username`.
- **Mute User**: Managers can mute a user using `/mute username`.
- **Quit**: Type `quit` to exit the chat.

### Notes

- **Manager Privileges**: By default, the username `Itay` is a manager. Managers can promote other users to manager status.
- **Muted Users**: Muted users can receive messages but cannot send messages to the chat.

## Project Structure

- `server.py`: Server-side script that handles client connections and message routing.
- `client.py`: Client-side script that connects to the server and handles user input/output.

## How It Works

### Server

- **Threaded Connections**: The server uses threading to handle multiple clients concurrently.
- **Message Parsing**: Custom `MessageParser` class to parse incoming data according to a defined protocol.
- **Action Handlers**: Functions mapped to specific action codes to handle different client requests.

### Client

- **Input Handling**: Separate threads to handle user input and server messages concurrently.
- **Message Construction**: Messages are constructed with lengths and action codes to match the server's parsing expectations.
- **Exit Handling**: Graceful exit when the user types `quit` or when the server disconnects.

---

**Enjoy chatting with PyMultiChat!**
