// startScript.js

// Function to join a room
function joinRoom(roomID) {
    $.ajax({
        type: 'POST',
        url: '/api/chatroom/',
        data: { roomID: roomID },
        success: function (response) {
            // Handle the response (e.g., update chat messages)
            console.log('Joined room:', roomID);
            const messages = response.messages || [];
            for (const message of messages) {
                handleMessage(message);
            }
        },
        error: function (error) {
            console.error('Error joining room:', roomID, error);
        }
    });
}

// Function to handle incoming chat messages
function handleMessage(data) {
    console.log(data.type);
    console.log(data.message);

    if (data.type === 'chat_message') {
        // Handle chat messages
        const sender = data.sender || 'Anonymous';  // Default to 'Anonymous' if sender is not provided
        const message = data.message;

        // Append the message to the chat interface
        $('#chat-messages').append(
            '<div class="message incoming">' +
            '<strong>' + sender + ':</strong> ' + message + '</div>'
        );
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

