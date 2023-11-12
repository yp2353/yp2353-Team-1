
document.querySelector('#chat-message-submit').onclick = function(e) {
    
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    chatSocket.send(JSON.stringify({
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

function room_list_click_handler(){

}

// it is also node that will be observed for mutations
var roomList = document.getElementById("room-list").addEventListener("click",function(e) {
    // e.target is our targetted element.
                // try doing console.log(e.target.nodeName), it will result LI
    if(e.target && e.target.nodeName == "LI") {
        console.log(e.target.innerHTML + " was clicked");
        if(roomContainer.style.visibility == "hidden"){
            roomContainer.style.visibility = "visible";
        }
        
        document.getElementById("room-name").innerHTML = e.target.innerHTML;
    }
});
    
// // Options for the observer (which mutations to observe)
// const config = { attributes: true, childList: true, subtree: true };

// // Callback function to execute when mutations are observed
// const callback = (mutationList, observer) => {
//   for (const mutation of mutationList) {
//     if (mutation.type === "childList") {
//       console.log("A child node has been added or removed.");
//     } else if (mutation.type === "attributes") {
//       console.log(`The ${mutation.attributeName} attribute was modified.`);
//     }
//   }
// };

// // Create an observer instance linked to the callback function
// const observer = new MutationObserver(callback);

// // Start observing the target node for configured mutations
// observer.observe(roomList, config);

