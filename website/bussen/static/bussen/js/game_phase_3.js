
function guess(type, index) {
    socket.send(JSON.stringify({
        "game": true,
        "phase": "phase3",
        "type": "guess",
        "guess": type,
        "index": index
    }));
}

function handle_game_event(event) {
    let data = JSON.parse(event.data);
    if (data.type !== null) {
        if (data.type === "celebrate") {
            confetti.start();
            setTimeout(() => { window.location = data.url }, 10000)
        }
    }
}
