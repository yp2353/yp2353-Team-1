
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

function room_list_click_handler(roomID){
    console.log("Rood with ID ", roomID)

    chatSocket.send(JSON.stringify({
        'type': 'join_room',
        'roomID': roomID
    }));
}   

// it is also node that will be observed for mutations
var roomList = document.getElementById("room-list").addEventListener("click",function(e) {
    // e.target is our targetted element.
                // try doing console.log(e.target.nodeName), it will result LI
    if(e.target && e.target.nodeName == "LI") {

        var roomID = e.target.dataset.roomId
        room_list_click_handler(roomID)
        
        if(roomContainer.style.visibility == "hidden"){
            roomContainer.style.visibility = "visible";
        }
        
        document.getElementById("room-name").innerHTML = e.target.innerHTML;
    }
});
