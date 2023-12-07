let currentRoomID = ''
let chatSocket = null;
let senderID = ''; 
let currentUserID = '';


function initializeWebSocket(roomID) {
    if (chatSocket) {
        chatSocket.close();
    }
    
    currentRoomID = roomID;
    chatSocket = new WebSocket( 'ws://' + window.location.host + '/ws/chatroom/');
    
    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
    
        if (data.type === 'chat_message') {
            // Handle chat messages
            const sender = data.sender || 'Anonymous';  // Default to 'Anonymous' if sender is not provided
            const message = data.message;
    
            // Check if the sender is the current user
            const isCurrentUser = data.sender_id === currentUserID;
    
            // Appending the message to the chat interface
            let chat_messages = document.querySelector('#chat-messages');
            if (isCurrentUser) {
                chat_messages.innerHTML += (
                    '<div class="message outgoing">' +
                    message + '<strong>: You</strong> </div>'
                );
            } else {
                chat_messages.innerHTML += (
                    '<div class="message incoming">' +
                    '<strong>' + sender + ':</strong> ' + message + '</div>'
                );
            }
    
            chat_messages.scrollTop = chat_messages.scrollHeight;
        }else if (data.type === 'user_id') {
            // Set currentUserID after receiving user_id from the server
            currentUserID = data.user_id;
            // console.log('Current User ID:', currentUserID);
        }
        
    };
    chatSocket.onopen = function (event) {
        console.log('WebSocket connection opened:', event);
        chatSocket.send(JSON.stringify({
            'type': 'get_user_id'
        }));
        chatSocket.send(JSON.stringify({
            'type': 'join_room',
            'roomID': currentRoomID
        }));
        
    };
    
    chatSocket.onerror = function (error) {
        console.error('WebSocket Error: ', error);
    };
    
    chatSocket.onclose = function(e) {
        console.log('Chat socket closed unexpectedly', e.log);
        // stoping roomlist observer
        // observer.disconnect();  
    };
}

document.querySelector('#chat-message-submit').onclick = function(e) {
    
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    
    chatSocket.send(JSON.stringify({
        'type': 'chat_message',
        'message': message
    }));

    messageInputDom.value = '';
};


document.querySelector('#chat-message-input').focus();
document.querySelector('#chat-message-input').onkeyup = function(e) {
    if (e.key === 'Enter') {  // enter, return
        document.querySelector('#chat-message-submit').click();
    }
};

function room_list_click_handler(roomID) {
    // console.log("Room with ID ", roomID);

    
    initializeWebSocket(roomID);
    // Clear the current messages
    document.querySelector('#chat-messages').innerHTML = '';

    if (chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            'type': 'join_room',
            'roomID': roomID
        }));
    } else {
        console.error('WebSocket is not open yet. Join room message not sent.');
    }
    // Update the room name in the chat interface
    const roomNameElement = document.getElementById("room-name");
    const roomName = document.querySelector(`.room-list-item[data-room-id="${roomID}"]`).textContent;
    roomNameElement.textContent = roomName;

    // Show the room container if it's hidden
    roomContainer.style.visibility = "visible";
}

