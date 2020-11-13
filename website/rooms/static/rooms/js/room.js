let wsStart = 'ws://';
if (window.location.protocol === 'https:') {
    wsStart = 'wss://'
}

let alive_timer = null;

let endpoint = wsStart + window.location.host + '/rooms/' + ROOM_SLUG + '/';
let socket = null;

function ping_alive() {
    socket.send(JSON.stringify({"type": "ping"}));
}

function handle_event(event) {
    /* Execute game event handler */
    if (typeof handle_game_event !== 'undefined') {
        handle_game_event(event);
    }

    /* Execute room event handler */
    let data = JSON.parse(event.data);
    if (data.type !== null) {
        if (data.type === 'refresh') {
            update_update_list();
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
        else if (data.type === 'redirect') {
            if (data.delay !== null)
            {
                setTimeout(() => { window.location = data.url }, data.delay)
            }
            else {
                window.location = data.url;
            }
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
    else {
        ping_alive();
    }
    alive_timer = setTimeout(reconnect_socket, 5000);
}

function kick_player(player_id) {
    update_and_callback(KICK_PLAYER_URL, {"player": player_id}, kick_player_callback);
}

function kick_player_callback(data) {
    if (data.succeeded !== null) {
        if (!data.succeeded) {
            alert("The player cound not be kicked.");
        }
        update_update_list();
    }
}

$(document).ready(function() {
    reconnect_socket();
});