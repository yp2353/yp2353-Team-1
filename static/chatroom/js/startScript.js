const roomName = 'global';
const chatSocket = new WebSocket(
'ws://' + window.location.host + '/ws/chatroom/'
);

// chatSocket.onopen = function (event) {
//     console.log('WebSocket connection opened:', event);
// };


chatSocket.onmessage = function(e) {
    console.log("top")
    const data = JSON.parse(e.data);
    document.querySelector('#chat-messages').innerHTML += (
        '<div class="message ' + 
        (data.sender === 'me' ? 'outgoing' : 'incoming') + '">' +
        data.message + '</div>'
        
    );
    console.log(data.message)
};

chatSocket.onclose = function(e) {
    console.log('Chat socket closed unexpectedly');
    // stoping roomlist observer
    observer.disconnect();  
};

