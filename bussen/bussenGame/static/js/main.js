const roomName = JSON.parse(document.getElementById('room-name').textContent);
let username = " No_user_name";
let modal = document.getElementById("myModal");
let inputUser;
let questions = ["Black or red?", "Higher, lower or equal?", "In between or outside", "Do you already have this color?"];
let answers = [["Black", "Red", "Color neutral"], ["Higher", "Lower", "Equal"], ["In between", "Outside", "Equal"], ["Yes", "No", "Rainbow"]];
let next = false;
let cards = [];
let answer;
let players = 1;
let question = 0;
let started = false;
let round2started = false;
let round3started = false;
let interval;
let isHost = false;
let round2old = [4, 4];
let round2new = [4, 4];
let numberofplaceBefore = [0, 1, 3, 6, 10];
let placedCards = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], []];
let waitTime = 15000;
let round3Card = 1;
let isPlaying = "";
let isStuck = false;
const timeout = async ms => new Promise(res => setTimeout(res, ms));

const chatSocket = new ReconnectingWebSocket(
    'wss://'
    + window.location.host
    + '/ws/room/'
    + roomName
    + '/'
);

$.ajaxSetup({
    cache: true
});

const observer = new IntersectionObserver(callback, {
  rootMargin: '-1px 0px 0px 0px',
  threshold: [0, 1],
});

function callback(){
    if(!isStuck){
        document.getElementById("cardsTitle").className = "visible";
    }else{
        document.getElementById("cardsTitle").className = "hidden";
    }
    isStuck=!isStuck;
}

chatSocket.onopen = function (e) {
    modal.style.display = "block";
    let input = document.getElementById("fname");
    input.focus();
    input.onkeyup = function (e) {
        if (e.keyCode === 13) {  // enter, return
            inputUser = input.value;
            chatSocket.send(JSON.stringify({
                'message': '?adduser',
                'username': inputUser,
            }));
        }
    }
};

chatSocket.onmessage = async function (e) {
    const data = JSON.parse(e.data);
    //console.log(data);
    if (data.message.startsWith('?round1')) {
        removeButton();
        if (!started) {
            document.getElementById("question-choices").style.display = "none";
            document.getElementById("text-question").innerHTML = "You still have time to grab a drink";
        }
        if (question < 4) {
            document.getElementById("turn-question").innerHTML = "It's " + data.username + "s turn";
            if (data.username === username && data.question < 4) {
                started = true;
                toggleQuestions("block");
                await getQuestion(data);
                chatSocket.send(JSON.stringify({
                    'message': "?round1",
                    'username': username
                }));
                question++;
            }
        }
    } else if (data.message === "?placecard" && data.username !== username) {
        toastr.warning(data.username + " placed a card");
        if (isHost) {
            clearInterval(interval);
            interval = setInterval(sendRound2, waitTime);
        }
        place_card(data.card, data.username);
    } else if (data.message === "?round2") {
        if (!round2started) {
            startRound2();
            if (data.username === username) {
                isHost = true;
                interval = setInterval(sendRound2, waitTime);
            }
        }
        if (round2new[0] < 0) {
            clearInterval(interval);
            round2started = false;
            sendCardsLeft();
            if (isHost) {
                chatSocket.send(JSON.stringify({
                    'message': "?round3",
                    'username': username
                }));
            }
        } else {
            await waitForServerCard();
            round2old = round2new.slice();
            document.getElementById("layer" + round2new[0] + "-" + round2new[1]).style.border = "3px solid #021a40";
            if (round2new[1] === 0) {
                round2new[0]--;
                round2new[1] = round2new[0];
            } else {
                round2new[1]--;
            }
        }

    } else if (data.message === "?round3") {
        round3started = true;
        sendCardsLeft();
    } else if (data.message === "?inthebus") {
        document.getElementById("round2").style.display = "none";
        document.getElementById("yourCards").style.display = "none";
        document.getElementById("inTheBus").style.display = "block";
        document.getElementById("BusTurn").innerText = data.username + " is going in the bus!"
        await timeout(5000);
        document.getElementById("inTheBus").style.display = "none";
        document.getElementById("round3").style.display = "block";
        document.getElementById("isPlaying").innerText = data.username + "s playing";
        document.getElementById("busc0").src = "/static/media/cards/" + data.card + ".jpg";
        selectCard(1, "visible");
        isPlaying = data.username;
        if (data.username === username) {
            startRound3();
        }
    } else if (data.message === "?newhost") {
        if (data.username === username) {
            isHost = true;
        }
    } else if (data.message === "?players"){
        players = data.number;
        document.getElementById("playercount").innerText = "There are currently " + players.toString() + " players in this room";
    }else if (data.message === "?empty") {
        confetti.start();
        document.getElementById("round3message").innerText = "The deck is out of cards, good luck getting home...";
        await timeout(10000);
        window.location.replace("https://bussen.vdhorst.dev");
    } else if (data.message === "?finished") {
        confetti.start();
        await timeout(10000);
        window.location.replace("https://bussen.vdhorst.dev");
    } else if (data.message === "?drink") {
        if (data.username === username) {
            if (data.lie) {
                toastr.error("You Lied, drink up!");
                removeLiedAboutButton(username);
                putCardBack(data.card);
                removePlacedCard(data.card);
            } else {
                toastr.warning(data.looked + ' thought you were lying\n They need to drink');
            }
        } else {
            if (data.lie) {
                toastr.error(data.username + " Lied, they need to drink!\n The card was: " + data.card);
                if (data.looked !== username) {
                    removeLiedAboutButton(data.username);
                    removePlacedCard(data.card);
                }
            } else {
                if (data.looked === username) {
                    toastr.error(data.username + 's card was correct\n You need to drink!');
                } else {
                    toastr.warning(data.username + 's card was correct\n' + data.looked + ' needs to drink!');
                }
            }
        }
    } else if (data.message === "?response") {
        if (data.username !== username) {
            if (data.response === "wrong") {
                toastr.warning(data.username + " needs to drink!");
            } else {
                toastr.success(data.username + " Has guessed correct!");
            }
        } else {
            if (data.response === "wrong") {
                toastr.warning("Wrong! you need to drink!");
            } else {
                toastr.success("Correct!");
            }
        }
    } else if (data.message === "?card") {
        if (data.username === username) {
            cards.push(data.card);
            toggleQuestions("none");
            if (checkAnswer(data.card)) {
                document.getElementById("text-question").innerHTML = "Correct!";
                sendResponse("correct");
            } else {
                document.getElementById("text-question").innerHTML = "Wrong, take a sip!";
                sendResponse("wrong");
            }
            document.getElementById("c" + cards.indexOf(data.card)).src = "/static/media/cards/" + data.card + ".jpg";
            next = true;
        } else if (round2started) {
            next = true;
            document.getElementById("layer" + round2new[0] + "-" + round2new[1]).src = "/static/media/cards/" + data.card + ".jpg";
        } else if (round3started) {
            if (data.username === "#reset") {
                document.getElementById("busc0").src = "/static/media/cards/" + data.card + ".jpg";
            } else {
                document.getElementById("busc" + round3Card).src = "/static/media/cards/" + data.card + ".jpg";
                if (checkMove(data.card, data.move)) {
                    document.getElementById("round3message").innerText = "Correct! next card";
                    selectCard(round3Card, "hidden");
                    round3Card++;
                    if (round3Card > 5) {
                        round3Finished();
                    } else {
                        selectCard(round3Card, "visible");
                    }
                } else {
                    document.getElementById("round3message").innerText = "Wrong! back to the beginning";
                    selectCard(round3Card, "hidden");
                    round3Card = 1;
                    selectCard(round3Card, "visible");
                    if (isPlaying === username) {
                        chatSocket.send(JSON.stringify({
                            'message': "?reset",
                            'username': username,
                        }));
                    }
                }
            }
            next = true;
        }
    } else if (data.message === "Okay") {
        username = inputUser;
        modal.style.display = "none";
    } else {
        document.getElementById("text-input").textContent = "That username is already taken";
    }
};

function round3Finished() {
    chatSocket.send(JSON.stringify({
        'message': "?finished",
        'username': username,
    }));
}

function sendResponse(response) {
    chatSocket.send(JSON.stringify({
        'message': "?response",
        'username': username,
        'response': response,
    }));
}

function place_card(card, username) {
    placedCards[numberofplaceBefore[round2old[0]] + round2old[1]].push(username, card);
    let list = document.getElementById("card" + round2old[0] + "-" + round2old[1]);
    let node = document.createElement("li");
    node.innerHTML += "<button class='w3-button middle' onclick='checkPlacedCard(this.innerHTML)' style='background: black'>" + username + "</button>"
    list.insertBefore(node, list.firstChild);
}

function sendRound2() {
    chatSocket.send(JSON.stringify({
        'message': "?round2",
        'username': username,
    }));
}

function startRound3() {
    for (let i = 1; i < 6; i++) {
        document.getElementById("busu" + i).onclick = async function () {
            chatSocket.send(JSON.stringify({
                'message': "?bus",
                'username': username,
                'move': "up"
            }));
        };
        document.getElementById("busd" + i).onclick = async function () {
            chatSocket.send(JSON.stringify({
                'message': "?bus",
                'username': username,
                'move': "down"
            }));
        };
        document.getElementById("busb" + i).onclick = async function () {
            chatSocket.send(JSON.stringify({
                'message': "?bus",
                'username': username,
                'move': "paal"
            }));
        };
    }
}

function selectCard(id, display) {
    document.getElementById("busu" + id).style.visibility = display;
    document.getElementById("busb" + id).style.visibility = display;
    document.getElementById("busd" + id).style.visibility = display;
}

function sendCardsLeft() {
    let cardsleft = [];
    let cardvalue;
    for (let i = 0; i < 4; i++) {
        cardvalue = document.getElementById("c" + i).src;
        cardvalue = cardvalue.substring(cardvalue.indexOf("cards/") + 6, cardvalue.indexOf(".jpg"));
        if (document.getElementById("c" + i).src !== (window.location.protocol + "//" + window.location.host + "/static/media/cards/back.jpg")) {
            cardsleft.push(document.getElementById("c" + i).src.substring(cardvalue.indexOf("cards/") + 6, cardvalue.indexOf(".jpg")));
        }
    }
    chatSocket.send(JSON.stringify({
        'message': "?left",
        'username': username,
        'left': cardsleft.length
    }));
}

function checkPlacedCard(user) {
    if (placedCards[numberofplaceBefore[round2old[0]] + round2old[1]].length !== 0) {
        let index = 0;
        let cardvalue = document.getElementById("layer" + round2old[0] + "-" + round2old[1]).src;
        let count = 0;
        placedCards[numberofplaceBefore[round2old[0]] + round2old[1]].forEach((v) => (v === user && count++));
        cardvalue = cardvalue.substring(cardvalue.indexOf("cards/") + 6, cardvalue.indexOf(".jpg"));
        if (cardvalue !== "back" && user !== username) {
            if (count === 1) {
                index = placedCards[numberofplaceBefore[round2old[0]] + round2old[1]].indexOf(user);
                if (parseInt(placedCards[numberofplaceBefore[round2old[0]] + round2old[1]][index + 1].substring(1)) === parseInt(cardvalue.substring(1))) {
                    sendDrinkResponse(user, placedCards[numberofplaceBefore[round2old[0]] + round2old[1]][index + 1], false, username);
                } else {
                    sendDrinkResponse(user, placedCards[numberofplaceBefore[round2old[0]] + round2old[1]][index + 1], true, username);
                    removeLiedAboutButton(user);
                    removePlacedCard(placedCards[numberofplaceBefore[round2old[0]] + round2old[1]][index + 1]);
                }
            } else {
                index = -1;
                for (let i = 0; i < count; i++) {
                    index = placedCards[numberofplaceBefore[round2old[0]] + round2old[1]].indexOf(user, index + 1);
                    cardvalue = cardvalue.substring(cardvalue.indexOf("cards/") + 6, cardvalue.indexOf(".jpg"));
                    if (parseInt(placedCards[numberofplaceBefore[round2old[0]] + round2old[1]][index + 1].substring(1)) !== parseInt(cardvalue.substring(1))) {
                        sendDrinkResponse(user, placedCards[numberofplaceBefore[round2old[0]] + round2old[1]][index + 1], true, username);
                        removeLiedAboutButton(user);
                        removePlacedCard(placedCards[numberofplaceBefore[round2old[0]] + round2old[1]][index + 1]);
                        return;
                    }
                }
                sendDrinkResponse(user, placedCards[numberofplaceBefore[round2old[0]] + round2old[1]][index + 1], false, username);
            }
        }
    }
}

function sendDrinkResponse(user, card, lie, looked) {
    chatSocket.send(JSON.stringify({
        'message': "?drink",
        'username': user,
        'card': card,
        'lie': lie,
        'looked': looked
    }));
}

async function getQuestion(data) {
    document.getElementById("turn-question").innerHTML = "It's your turn!";
    document.getElementById("text-question").innerHTML = questions[data.question];
    for (let i = 0; i < 3; i++) {
        document.getElementById("a" + i).innerHTML = answers[data.question][i];
    }
    await waitUserInput(data.question);
}

async function waitUserInput() {
    while (next === false) await timeout(50); // pause script but avoid browser to freeze ;)
    next = false; // reset var
    chatSocket.send(JSON.stringify({
        'message': "?question",
        'username': username
    }));
    while (next === false) await timeout(50); // pause script but avoid browser to freeze ;)
    next = false; // reset var
}

async function waitForServerCard() {
    while (next === false) await timeout(50); // pause script but avoid browser to freeze ;)
    next = false; // reset var
}

function removeButton() {
    document.getElementById("room-start").style.display = "none";
    document.getElementById("questions").style.display = "block";
    document.getElementById("playercount").style.display = "none";
}

function toggleQuestions(property) {
    document.getElementById("answer-submit").style.display = property;
    document.getElementById("question-choices").style.display = property;
}

function removeLiedAboutButton(user) {
    let lis = document.getElementById("card" + round2old[0] + "-" + round2old[1]).getElementsByTagName("li");
    for (let i = 0; i < lis.length; i++) {
        if (lis[i].innerText === user) {
            lis[i].parentNode.removeChild(lis[i]);
            return;
        }
    }
}

function removePlacedCard(card) {
    let arr = placedCards[numberofplaceBefore[round2old[0]] + round2old[1]];
    placedCards[numberofplaceBefore[round2old[0]] + round2old[1]].splice(arr.indexOf(card) - 1, 1);
    placedCards[numberofplaceBefore[round2old[0]] + round2old[1]].splice(arr.indexOf(card), 1);
}

function putCardBack(card) {
    for (let i = 0; i < 4; i++) {
        if (document.getElementById("c" + i).src === (window.location.protocol + "//" + window.location.host + "/static/media/cards/back.jpg")) {
            document.getElementById("c" + i).src = "/static/media/cards/" + card + ".jpg";
            break;
        }
    }
}

function startRound2() {
    round2started = true;
    document.getElementById("round2").style.display = "block";
    document.getElementById("questions").style.display = "none";
    toggleQuestions("none");
    document.getElementById("turn-question").style.display = "none";
    document.getElementById("text-question").style.display = "none";
    document.getElementById("yourCards").classList.add("sticky");
    observer.observe(document.querySelector("#yourCards"));
    for (let k = 0; k < 4; k++) {
        document.getElementById("c" + k).onclick = function () {
            if (document.getElementById("c" + k).src !== (window.location.protocol + "//" + window.location.host + "/static/media/cards/back.jpg")) {
                cardOnClick(k);
            }
        }
    }
}

function cardOnClick(k) {
    chatSocket.send(JSON.stringify({
        'message': "?placecard",
        'username': username,
        'card': cards[k]
    }));
    document.getElementById("c" + k).src = "/static/media/cards/back.jpg";
    place_card(cards[k], username);
}

document.getElementById("answer-submit").onclick = function () {
    let radios = document.getElementsByName('answer');
    for (let i = 0; i < radios.length; i++) {
        if (radios[i].checked) {
            answer = radios[i].value;
            break;
        }
    }
    next = true;
}


document.getElementById("room-start").onclick = function (e) {
    chatSocket.send(JSON.stringify({
        'message': "?start",
        'username': username
    }));
    chatSocket.send(JSON.stringify({
        'message': "?round1",
        'username': username
    }));
}

chatSocket.onclose = function (e) {
    console.error('Chat socket closed unexpectedly');
};

window.onbeforeunload = closingCode;

function closingCode() {
    chatSocket.send(JSON.stringify({
        'message': "/closing_screen",
        'username': username,
        'host': isHost,
    }));
    return null;
}

function getNumber(card) {
    if (card.length === 3) {
        return parseInt(card.substring(1));
    } else {
        return parseInt(card.charAt(1));
    }
}

function checkMove(card, move) {
    let previouscard = document.getElementById("busc" + (round3Card - 1)).src;
    previouscard = previouscard.substring(previouscard.indexOf("cards/") + 6, previouscard.indexOf(".jpg"));
    switch (move) {
        case "up":
            return getNumber(card) > getNumber(previouscard);
        case "down":
            return getNumber(card) < getNumber(previouscard);
        case "paal":
            return getNumber(card) === getNumber(previouscard);
    }
}

function checkAnswer(card) {
    switch (question) {
        case 0:
            switch (card.charAt(0)) {
                case "h":
                    return answer !== "a";
                case  "d":
                    return answer !== "a";
                case "s":
                    return answer !== "b";
                case "c":
                    return answer !== "b";
            }
        case 1:
            cardvalue = getNumber(cards[1]);
            card0 = getNumber(cards[0]);

            if (cardvalue > card0) {
                return answer === "a";
            } else if (cardvalue < card0) {
                return answer === "b";
            } else {
                return answer === "c";
            }
        case 2:
            cardvalue = getNumber(cards[2]);
            card0 = getNumber(cards[0]);
            card1 = getNumber(cards[1]);

            if (cardvalue === card0 || cardvalue === card1) {
                return answer === "c";
            } else if ((cardvalue > card0 && cardvalue < card1) || (cardvalue > card1 && cardvalue < card0)) {
                return answer === "a";
            } else {
                return answer === "b";
            }
        case 3:
            switch (answer) {
                case "a":
                    for (let j = 0; j < cards.length; j++) {
                        if (card.charAt(0) === cards[j].charAt(0)) {
                            return true;
                        }
                    }
                    return false;
                case "b":
                    for (let k = 0; k < cards.length; k++) {
                        if (card.charAt(0) === cards[k].charAt(0)) {
                            return false;
                        }
                    }
                    return true;
                case "c":
                    let tempArr = [];
                    for (let i = 0; i < cards.length; i++) {
                        if (i === 0 || tempArr.findIndex(el => el === cards[i].charAt(0)) === -1) {
                            tempArr.push(cards[i].charAt(0));
                        }
                    }
                    return tempArr.length === 4;

            }
    }
}

