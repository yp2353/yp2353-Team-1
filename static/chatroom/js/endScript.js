// my endScripts.js
// Function to send a chat message

var roomID = "";
function sendChatMessage(message) {
    
    $.ajax({
        type: 'POST',
        url: '/chatroom/api/chatroom/',
        data: {
            csrfmiddlewaretoken: getCookie('csrftoken'),
            type: 'chat_message',
            roomID: roomID,
            message: message
        },
        success: function (response) {
            console.log("Function Sucess");
            handleMessage({
                type: "chat_message",
                sender: response.sender,
                message: response.message
            });
        },
        error: function (error) {
            console.log("Erroororro")
            console.error('Error sending chat message:', error);
        }
    });
}

// Attach event listener to chat message input
$('#chat-form').on('keyup', '#chat-message-input', function (e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        $('#chat-message-submit').click();
    }
});

// Attach event listener to chat message submit button
$('#chat-form').on('click', '#chat-message-submit', function (e) {
    e.preventDefault();

    const messageInputDom = $('#chat-message-input');
    const message = messageInputDom.val();
    sendChatMessage(message);

    messageInputDom.val('');
});

// Toggle search bar visibility
$("#add-icon").click(function (e) {
    $("#searchbar").toggle();
});

// Click event listener for room list items
$('#room-list').on('click', 'li', function (e) {
    if (e.target && e.target.nodeName === "LI") {
        roomID = $(e.target).data('room-id');
        room_list_click_handler(roomID);

        if (roomContainer.style.visibility === "hidden") {
            roomContainer.style.visibility = "visible";
        }

        $('#room-name').html($(e.target).html());
    }
});

// Set initial visibility of the room container
var roomContainer = document.getElementById("room-container");
roomContainer.style.visibility = "hidden";

function room_list_click_handler(roomID) {
    console.log("Room with ID ", roomID);
}