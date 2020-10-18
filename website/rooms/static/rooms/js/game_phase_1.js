let wsStart = 'ws://';
if (window.location.protocol === 'https:') {
    wsStart = 'wss://'
}

let alive_timer = null;

let endpoint = wsStart + window.location.host + '/rooms/phase1/' + GAME_NAME + '/';
let socket = null;

function send_phase1_question_answer(answer) {
    socket.send(JSON.stringify({
        "type": "phase1_answer",
        "value": answer
    }));
}

function handle_event(event) {
    let data = JSON.parse(event.data);
    if (data.type !== null) {
        if (data.type === "refresh") {
            refresh_player_cards();
            refresh_player_question();
        }
        else if (data.type === "message") {
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
            setTimeout(() => { window.location = data.url }, 4000)
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