const roomName = JSON.parse(document.getElementById('room-name').textContent);
var username = " No_user_name";
var modal = document.getElementById("myModal");
var inputUser;
var questions = ["Black or red?","Higher, lower or equal?","In between or outside","Do you already have this color?"];
var answers = [["Black", "Red", "Color neutral"], ["Higher","Lower","Equal"], ["In between","Outside", "Equal"], ["Yes", "No", "Rainbow"]];
var next = false;
var cards = [];
var answer;
var question=0;
var started=false;
var round2started=false;
let round2old = [4,4];
let round2new = [4,4];
let numberofplaceBefore = [0,1,3,6,10];
var placedCards = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]];

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


chatSocket.onopen = function (e) {
    modal.style.display = "block";
    var input = document.getElementById("fname");
    input.focus();
    input.onkeyup = function (e) {
        if (e.keyCode === 13) {  // enter, return
            inputUser=input.value;
            chatSocket.send(JSON.stringify({
                'message': '?adduser',
                'username': inputUser,
            }));
        }

    }
};

chatSocket.onmessage = async function (e) {
    const data = JSON.parse(e.data);
    console.log(data);
    if (data.message.startsWith('?round1')) {
        removeButton();
        if(!started){
            document.getElementById("question-choices").style.display = "none";
            document.getElementById("text-question").innerHTML = "You still have time to grab a drink";
        }
        if(question<4) {
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
    }
    else if(data.message === "?placecard" && data.username !== username){
        place_card(data.card,data.username);
    }
    else if(data.message === "?round2"){
        document.getElementById("turn-question").innerHTML = "Place your cards!";
        if(!round2started) {
            startRound2();
        }
        if(round2new[0]<0){
            round2started=false;
            chatSocket.send(JSON.stringify({
                    'message': "?round3",
                    'username': username
            }));
        }else {
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
    }
    else if(data.message === "?drink"){
        if(data.username === username){
            if(data.lie){
                document.getElementById("turn-question").innerHTML = "You lied!";
                document.getElementById("text-question").innerHTML = "Drink up";
                putCardBack(data.card);
            }else{
                document.getElementById("text-question").innerHTML = "Someone thought you were lying, they need to drink";
            }
        }
        else{
            if(data.lie){
                document.getElementById("turn-question").innerHTML = data.username + " Lied";
                document.getElementById("text-question").innerHTML = "They need to drink";
            }else{
                document.getElementById("text-question").innerHTML = data.username + "s card was correct";
            }
        }
    }
    else if(data.message === "?card"){
        if(data.username === username){
            cards.push(data.card);
            toggleQuestions("none");
            if(checkAnswer(data.card)){
                document.getElementById("text-question").innerHTML = "Correct!";
            }else{
                document.getElementById("text-question").innerHTML = "Wrong, take a sip!";
            }
            document.getElementById("c"+cards.indexOf(data.card)).src = "/static/media/cards/" + data.card+".jpg";
            next=true;
        }
        else if(round2started){
            next=true;
            document.getElementById("layer"+round2new[0]+"-"+round2new[1]).src = "/static/media/cards/" + data.card+".jpg";
        }
    }
    else if(data.message === "Okay"){
        username = inputUser;
        modal.style.display = "none";
    }
    else{
        document.getElementById("text-input").textContent = "That username is already taken";
    }
};

function place_card(card, username){
    placedCards[numberofplaceBefore[round2old[0]]+round2old[1]].push(username,card);
    var list=document.getElementById("card"+round2old[0]+"-"+round2old[1]);
    var node = document.createElement("li");
    node.innerHTML+="<button class='w3-button middle' onclick='checkPlacedCard(this.innerHTML)' style='background: black'>"+username+"</button>"
    list.insertBefore(node,list.firstChild);
}

function checkPlacedCard(user){
    let index = placedCards[numberofplaceBefore[round2old[0]]+round2old[1]].indexOf(user)+1;
    let cardvalue = document.getElementById("layer"+round2old[0]+"-"+round2old[1]).src;
    if(cardvalue.substring(cardvalue.indexOf("cards/")+6,cardvalue.indexOf(".jpg")) !== "back" && user !== username){
        cardvalue = cardvalue.substring(cardvalue.indexOf("cards/") + 6, cardvalue.indexOf(".jpg"));
        document.getElementById("turn-question").innerHTML = user + "s card was " + placedCards[numberofplaceBefore[round2old[0]] + round2old[1]][index];
        if (parseInt(placedCards[numberofplaceBefore[round2old[0]] + round2old[1]][index].substring(1)) === parseInt(cardvalue.substring(1))) {
            document.getElementById("text-question").innerHTML = "You need to drink!";
            chatSocket.send(JSON.stringify({
                'message': "?drink",
                'username': username,
                'card':placedCards[numberofplaceBefore[round2old[0]] + round2old[1]][index],
                'lie':false
            }));
        } else {
            document.getElementById("text-question").innerHTML = "They were lying!";
            chatSocket.send(JSON.stringify({
                'message': "?drink",
                'username': user,
                'card':placedCards[numberofplaceBefore[round2old[0]] + round2old[1]][index],
                'lie':true
            }));
        }
    }
}

async function getQuestion(data){
    document.getElementById("turn-question").innerHTML = "It's your turn!";
    document.getElementById("text-question").innerHTML = questions[data.question];
    for (var i = 0; i < 3; i++) {
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

async function waitForServerCard(){
    while (next === false) await timeout(50); // pause script but avoid browser to freeze ;)
    next = false; // reset var
}

function removeButton(){
    document.getElementById("room-start").style.display = "none";
    document.getElementById("questions").style.display = "block";
}

function toggleQuestions(property){
    document.getElementById("answer-submit").style.display = property;
    document.getElementById("question-choices").style.display = property;
}

function putCardBack(card) {
    for(let i=0; i<4; i++){
        if(document.getElementById("c"+i).src === (window.location.protocol+"//"+window.location.host+"/static/media/cards/back.jpg")){
            document.getElementById("c"+i).src = "/static/media/cards/"+card+".jpg";
            break;
        }
    }
}

function startRound2() {
    round2started=true;
    document.getElementById("round2").style.display = "block";
    toggleQuestions("none");

    for(let k=0; k<4; k++){
    document.getElementById("c"+k).onclick= function(){
            if(document.getElementById("c"+k).src !== (window.location.protocol+"//"+window.location.host+"/static/media/cards/back.jpg")) {
                cardOnClick(k);
            }
        }
    }
}

function cardOnClick(k){
            chatSocket.send(JSON.stringify({
            'message': "?placecard",
            'username': username,
            'card': cards[k]
        }));
        document.getElementById("c"+k).src = "/static/media/cards/back.jpg";
        place_card(cards[k],username);
}

document.getElementById("answer-submit").onclick = function(){
    var radios = document.getElementsByName('answer');
    for( let i=0; i<radios.length; i++){
        if(radios[i].checked){
            answer=radios[i].value;
            break;
        }
    }
    next=true;
}


document.getElementById("room-start").onclick = function (e) {
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
        'username': username
    }));
    return null;
}
function getNumber(card) {
    if(card.length === 3){
        return parseInt(card.substring(1));
    }else{
        return parseInt(card.charAt(1));
    }
}
function checkAnswer(card){
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

            if(cardvalue>card0){
                return answer ==="a";
            }
            else if(cardvalue<card0){
                return answer ==="b";
            }
            else {
                return answer === "c";
            }
        case 2:
            cardvalue=getNumber(cards[2]);
            card0=getNumber(cards[0]);
            card1=getNumber(cards[1]);

            if (cardvalue===card0 || cardvalue===card1){
                return answer ==="c";
            }
            else if((cardvalue>card0 && cardvalue<card1) || (cardvalue>card1 && cardvalue<card0)) {
                return answer === "a";
            }else{
                return answer === "b";
            }
        case 3:
            switch (answer) {
                case "a":
                    for(j in cards){
                        if(card.charAt(0) === j.charAt(0)){
                            return true;
                        }
                    }
                    return false;
                case "b":
                    for(k in cards){
                        if(card.charAt(0) === k.charAt(0)){
                            return false;
                        }
                    }
                    return true;
                case "c":
                    var tempArr=[];
                    for(var i=0; i<cards.length; i++){
                        if(i===0 || tempArr.findIndex(el => el === cards[i].charAt(0))===-1){
                            tempArr.push(cards[i].charAt(0));
                        }
                    }
                    if(tempArr.length===4){
                        return true;
                    }else{
                        return false;
                    }

            }
    }
}

