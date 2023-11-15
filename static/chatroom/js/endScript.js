
// Function to send a chat message
function sendChatMessage(message) {
    $.ajax({
        type: 'POST',
        url: '/api/chatroom/',
        data: {
            type: 'chat_message',
            roomID: roomName,
            message: message
        },
        success: function (response) {
            // Handle the success (if needed)
        },
        error: function (error) {
            console.error('Error sending chat message:', error);
        }
    });
}

// Attach event listener to chat message input
$('#chat-message-submit').on('click', function (e) {
    const messageInputDom = $('#chat-message-input');
    const message = messageInputDom.val();

    sendChatMessage(message);

    messageInputDom.val('');
});



$('#chat-message-input').focus();
$('#chat-message-input').on('keyup', function(e) {
    if (e.key === 'Enter') {
        $('#chat-message-submit').click();
    }
});


var roomContainer = document.getElementById("room-container");
roomContainer.style.visibility = "hidden";

function room_list_click_handler(roomID){
    console.log("Rood with ID ", roomID)
}   

$('#room-list').on('click', 'li', function(e) {
    if (e.target && e.target.nodeName === "LI") {
        var roomID = $(e.target).data('room-id');
        room_list_click_handler(roomID);

        if (roomContainer.style.visibility === "hidden") {
            roomContainer.style.visibility = "visible";
        }

        $('#room-name').html($(e.target).html());
    }
});
