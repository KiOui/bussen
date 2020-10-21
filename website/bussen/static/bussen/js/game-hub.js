let wsStart = 'ws://';
if (window.location.protocol === 'https:') {
    wsStart = 'wss://'
}

let alive_timer = null;

let endpoint = wsStart + window.location.host + '/hubs/' + GAME_NAME + '/';
let socket = null;

function update_player_amount(players, players_online, can_start) {
    AMOUNT_OF_PLAYERS_BLOCK.innerText = players;
    AMOUNT_OF_ONLINE_PLAYERS_BLOCK.innerText = players_online;
    if (can_start) {
        START_GAME_BUTTON.classList.remove("disabled");
    }
    else {
        START_GAME_BUTTON.classList.add("disabled");
    }
}

function handle_event(event) {
    let data = JSON.parse(event.data);
    if (data.type !== null) {
        if (data.type === "player_amount") {
            update_player_amount(data.players, data.online_players, data.can_start);
        }
        else if (data.type === "game_redirect") {
            window.location = data.url;
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
    START_GAME_BUTTON.addEventListener('click', function(event) {
        socket.send(JSON.stringify({"type": "start_game"}));
        event.preventDefault();
    }, false);
});