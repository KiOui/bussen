let wsStart = 'ws://';
if (window.location.protocol === 'https:') {
    wsStart = 'wss://'
}

let alive_timer = null;

let endpoint = wsStart + window.location.host + '/games/phase2/' + GAME_NAME + '/';
let socket = null;

function put_card(suit, rank) {
    socket.send(JSON.stringify({
        "type": "phase2_card",
        "suit": suit,
        "rank": rank
    }));
}

function call_card(random_id) {
    socket.send(JSON.stringify({
        "type": "phase2_call",
        "id": random_id
    }));
}

function next_card(index) {
    socket.send(JSON.stringify({
        "type": "phase2_next_card",
        "index": index
    }));
}

function handle_event(event) {
    let data = JSON.parse(event.data);
    if (data.type !== null) {
        if (data.type === "refresh") {
            refresh_hand();
            refresh_pyramid();
            refresh_pyramid_header();
        }
        else if (data.type === "message") {
            console.log("message type");
            if (data.color === "red") {
                toastr.error(data.message);
            }
            else if (data.color === "yellow") {
                toastr.warning(data.message);
            }
            else {
                toastr.success(data.message);
            }
        }
        else if (data.type === "redirect") {
            setTimeout(() => { window.location = data.url }, 500)
        }
    }
}

function websocket_setup() {
    socket = new WebSocket(endpoint);

    socket.onmessage = function(e) {
        handle_event(e);
    };

    socket.onerror = function(e) {
        handle_event(e);
    }
}

function reconnect_socket() {
    clearTimeout(alive_timer);
    if (socket === null) {
        websocket_setup();
    }
    else if (socket.readyState === WebSocket.CLOSED) {
        websocket_setup();
    }
    alive_timer = setTimeout(reconnect_socket, 5000);
}

$(document).ready(function() {
    reconnect_socket();
});