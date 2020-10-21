

function refresh_player_question() {
    update_and_replace(REFRESH_GAME_QUESTION_URL, document.getElementById("question-container"), {});
}