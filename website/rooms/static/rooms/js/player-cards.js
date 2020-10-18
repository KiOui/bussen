

function refresh_player_cards() {
    update_and_replace(REFRESH_CARDS_DATA_URL, document.getElementById("card-container"), {});
}