
function send_phase1_question_answer(answer) {
    socket.send(JSON.stringify({
        "game": true,
        "phase": "phase1",
        "type": "answer",
        "value": answer
    }));
}