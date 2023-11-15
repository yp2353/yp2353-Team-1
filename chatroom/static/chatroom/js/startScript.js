// startScript.js
var sender = undefined
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to join a room
function joinRoom(roomID) {
    $.ajax({
        type: 'POST',
        url: '/chatroom/api/chatroom/',
        data: { 
            csrfmiddlewaretoken: getCookie('csrftoken'),
            type: "join_room",
            roomID: roomID 
        },
        success: function (response) {
            // console.log('Joined room:', roomID);
            // console.log(response)
            if (response.hasOwnProperty("messages")) {
                const messages = response.messages || [];
                for (const message of messages) {
                    handleMessage(message);
                }
            }

            // Update the sender value
            sender = response.sender || 'Anonymous';
            console.log("User is ", sender);
        },
        error: function (error) {
            console.error('Error joining room:', roomID, error);
        }
    });
}

// Function to handle incoming chat messages
function handleMessage(data ) {
    // console.log(data.type);
    // console.log(data.message);
  
    
    if (data.type === 'chat_message') {
        // Handle chat messages
        
        sender = data.sender || 'Anonymous';  
        const message = data.message;
        
        // Append the message to the chat interface
        $('#chat-messages').append(
            '<div class="message incoming">' +
            '<strong>' + sender + ':</strong> ' + message + '</div>'
        );

        // Scroll to the bottom of the chat-messages container
        const chatMessagesContainer = $('#chat-messages');
        chatMessagesContainer.scrollTop(chatMessagesContainer.prop("scrollHeight"));
    }
    
}


// Attach event listener to room list items
$('#room-list').on('click', 'li', function (e) {
    const roomID = $(this).data('room-id');
    joinRoom(roomID);

    // Update the room container visibility
    $('#room-container').css('visibility', 'visible');
    $('#room-name').html($(this).html());
});

