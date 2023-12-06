
var roomContainer = document.getElementById("room-container");
roomContainer.style.visibility = "hidden";

// it is also node that will be observed for mutations
var roomListItems = document.querySelectorAll(".room-list-item");

roomListItems.forEach(function (roomListItem) {
    roomListItem.addEventListener("click", function (e) {
        // e.target is our targetted element.
        // try doing console.log(e.target.nodeName), it will result LI
        if (e.target && e.target.nodeName == "LI") {
            var roomID = e.target.dataset.roomId;
            room_list_click_handler(roomID);

            if (roomContainer.style.visibility == "hidden") {
                roomContainer.style.visibility = "visible";
            }

            document.getElementById("room-name").innerHTML = e.target.innerHTML;
        }
    });
});







// var roomList = document.querySelectorAll("#room-list ul li").forEach(function (li) {
//     li.addEventListener("click", function (e) {
//         // e.target is our targetted element.
//         // try doing console.log(e.target.nodeName), it will result LI
//         if (e.target && e.target.nodeName == "LI") {
//             var roomID = e.target.dataset.roomId
//             room_list_click_handler(roomID)

//             if (roomContainer.style.visibility == "hidden") {
//                 roomContainer.style.visibility = "visible";
//             }

//             document.getElementById("room-name").innerHTML = e.target.innerHTML;
//         }
//     });
// });

function room_list_click_handler(roomID) {
    console.log("Room with ID ", roomID);
}