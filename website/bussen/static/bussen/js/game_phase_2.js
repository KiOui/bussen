
function put_card(suit, rank) {
    socket.send(JSON.stringify({
        "game": true,
        "phase": "phase2",
        "type": "card",
        "suit": suit,
        "rank": rank
    }));
}

function call_card(random_id) {
    socket.send(JSON.stringify({
        "game": true,
        "phase": "phase2",
        "type": "call",
        "id": random_id
    }));
}

function next_card(index) {
    socket.send(JSON.stringify({
        "game": true,
        "phase": "phase2",
        "type": "next_card",
        "index": index
    }));
}