let wsStart = 'ws://';
if (window.location.protocol === 'https:') {
    wsStart = 'wss://'
}

let alive_timer = null;

let endpoint = wsStart + window.location.host + '/games/phase3/' + GAME_NAME + '/';
let socket = null;

function guess(type, index) {
    socket.send(JSON.stringify({
        "type": "phase3_guess",
        "guess": type,
        "index": index
    }));
}

function handle_event(event) {
    let data = JSON.parse(event.data);
    if (data.type !== null) {
        if (data.type === "refresh") {
            refresh_bus();
        }
        else if (data.type === "celebrate") {
            confetti.start();
            setTimeout(() => { window.location = data.url }, 10000)
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