
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

var roomContainer = document.getElementById("room-container");
roomContainer.style.visibility = "hidden";

function room_list_click_handler(roomID) {
    console.log("Room with ID ", roomID);

    
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

// it is also node that will be observed for mutations
document.getElementById("room-list").addEventListener("click", function(e) {
    var roomItem = e.target.closest('.room-list-item');
    if (roomItem) {
        var roomID = roomItem.dataset.roomId;
        room_list_click_handler(roomID);

        if (roomContainer.style.visibility === "hidden") {
            roomContainer.style.visibility = "visible";
        }

        document.getElementById("room-name").textContent = roomItem.querySelector('.room-name-display').textContent;
    }
});

