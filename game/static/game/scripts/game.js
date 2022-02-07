$('#answer_form').submit(function (e) {
    e.preventDefault();
    disable_input(true)
    hide_move(true)
    clear_all_timers()

    gameSocket.send(JSON.stringify({
        "event": "NEW_USER_NUMBER",
        "message": {
            'number': document.getElementById('id_number').value,
            'timer_ended': false
        },
    }))
})

function clear_all_timers() {
    for (let i = 0; i < timeouts.length; i++) {
        clearInterval(timeouts[i]);
    }
    timeouts = [];
    document.querySelector('div.left_panel .timer').innerHTML = 20
    document.querySelector('div.right_panel .timer').innerHTML = 20
}

function set_data_in_table(user, number, target_number) {
    if (number === 0) {
        number = '-'
    }
    let rows = document.querySelectorAll('tbody tr')
    let header = rows[0]
    let last_row = rows[rows.length - 1]
    if (header.querySelectorAll('th')[2].innerText === user) {
        if (last_row.querySelectorAll('td')[2].innerText === '') {
            last_row.querySelectorAll('td')[2].innerText = number
        }
    }
    else {
        if (last_row.querySelectorAll('td')[3].innerText === '') {
            last_row.querySelectorAll('td')[3].innerText = number
        }
    }
    if (target_number !== null) {
        last_row.querySelectorAll('td')[1].innerText = target_number
    }
}

function set_winner(winner, row=null) {
    let rows = document.querySelectorAll('tbody tr')
    let header = rows[0]
    let last_row;
    if (row !== null) {
        last_row = rows[row]
    }
    else {
        last_row = rows[rows.length - 1]
    }

    if (header.querySelectorAll('th')[2].innerText === winner) {
        last_row.querySelectorAll('td')[2].style.color = '#68EC5C';
        last_row.querySelectorAll('td')[3].style.color = '#F15454';
    }
    else if (header.querySelectorAll('th')[3].innerText === winner) {
        last_row.querySelectorAll('td')[3].style.color = '#68EC5C';
        last_row.querySelectorAll('td')[2].style.color = '#F15454';
    }
    else {
        last_row.querySelectorAll('td')[3].style.color = '#6993FF';
        last_row.querySelectorAll('td')[2].style.color = '#6993FF';
    }
}

function disable_input(mode) {
    document.querySelector('#answer_form input.answer').disabled = mode;
    document.querySelector('#answer_form button.send_answer').disabled = mode;
}


function hide_move(status) {
    if (status === true) {
        document.querySelector('div.left_panel div.move').style.visibility = "hidden";
        document.querySelector('div.right_panel div.move').style.visibility = "visible";
    }
    else {
        document.querySelector('div.left_panel div.move').style.visibility = "visible";
        document.querySelector('div.right_panel div.move').style.visibility = "hidden";
    }
}


function game_end() {
    disable_input(true)
    hide_input()
    clear_all_timers()
    document.querySelector('div.left_panel div.move').style.visibility = "hidden";
    document.querySelector('div.right_panel div.move').style.visibility = "hidden";
    document.querySelector('div.left_game').style.visibility = "hidden";
}

function load_moves(moves, next_move) {
    for (let i = 0; i < moves.length; i++) {
        let move = moves[i];
        create_new_row(move.step);
        set_data_in_table(move['user_1']['name'], move['user_1']['number'], move['target_number'])
        set_data_in_table(move['user_2']['name'], move['user_2']['number'], move['target_number'])
        if (move['move_ended'] === true) {
            set_winner(move['winner'], move.step)
        }
    }
    if (next_move === document.getElementById('user').innerText) {
        disable_input(false)
        hide_move(false)
    }
    else {
        disable_input(true)
        hide_move(true)
    }
}


function hide_input() {
    document.querySelector('#answer_form input.answer').style.visibility = "hidden";
    document.querySelector('#answer_form button.send_answer').style.visibility = "hidden";
}


if ((window.location.href.match('/login/') === null) && (window.location.href.match('/register/') === null)) {
    connect()
}

var gameSocket;

function connect() {
    gameSocket = new WebSocket('ws://' + window.location.host + '/new_game/');

    gameSocket.onopen = function open() {
        console.log('WebSockets connection created.');
        if (window.location.href.match('/new_game/') != null) {
            get_history()
        }
    };

    gameSocket.onclose = function (e) {
        console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
        setTimeout(function () {
            connect();
        }, 1000);
    };
    gameSocket.onmessage = function (e) {
        let data = JSON.parse(e.data);
        data = data["payload"];
        let message = data['message'];
        let event = data["event"];

        switch (event) {
            case "GAME_FIND":
                window.location = 'http://' + window.location.host + '/new_game/';
                break;
            case "USERS_READY":
                clear_all_timers()
                if (window.location.href.match('/new_game/') === null) {
                    window.location = 'http://' + window.location.host + '/new_game/';
                }
                if (message['first_move'] !== document.getElementById('user').innerText) {
                    disable_input(true)
                    hide_move(true)
                    timer('enemy', message['timer'])
                }
                else {
                    disable_input(false)
                    hide_move(false)
                    timer('self', message['timer'])
                }
                break;
            case "HISTORY":
                load_moves(message['moves_history'], message['next_move']);
                break;
            case "RESET_CONNECT":
                gameSocket.close()
                connect()
                break
            case "MOVE":
                clear_all_timers()
                let user = message['user']
                set_data_in_table(user, message['number'], message['target_number'])
                document.getElementById('id_number').value = ''
                if (message['winner'] !== null) {
                    set_winner(message['winner'])
                }
                if (user !== document.getElementById('user').innerText) {
                    disable_input(false)
                    hide_move(false)
                    timer('self', 20)
                }
                else {
                    timer('enemy', 20)
                    hide_move(true)
                }
                if (message['add_new_row'] === true) {
                    create_new_row(message['move_number'])
                }
                break;
            case "GAME_END":
                game_end()
                if (message['game_winner'] === document.getElementById('user').innerText) {
                    document.querySelector('#popup .game_result_message').innerHTML = 'Победа'
                }
                else if (message['game_winner'] !== 'not_winner') {
                    document.querySelector('#popup .game_result_message').innerHTML = 'Поражение'
                }
                else {
                    document.querySelector('#popup .game_result_message').innerHTML = 'Ничья'
                }
                $('#popup').show()
                break;
            case "STOP_WAIT":
                $("#popup").hide()
                break;
            default:
                console.log("No event")
        }
    };

    if (gameSocket.readyState == WebSocket.OPEN) {
        gameSocket.onopen();
    }
}

function find_new_game() {
    $("#popup").show()
    gameSocket.send(JSON.stringify({
        "event": "FIND_GAME",
    }))
}

function stop_wait_game() {
    gameSocket.send(JSON.stringify({
        "event": "STOP_FIND",
    }))
}

function get_history() {
    gameSocket.send(JSON.stringify({
        "event": "GET_HISTORY",
    }))
}

function left_game() {
    gameSocket.send(JSON.stringify({
        "event": "LEFT_GAME",
    }))
}

var timeouts = [];

function timer(user, start_seconds) {
    let current_time = start_seconds;
    let timer_div = document.querySelector('div.right_panel .timer')
    if (user === 'self') {
        timer_div = document.querySelector('div.left_panel .timer')
    }

    let timer_counter = setInterval(
        () => {
            if (current_time === 0) {
                clearInterval(timer_counter)
                timer_div.innerHTML = '20';
                set_data_in_table(document.getElementById('user').innerText, '-', null)
                set_data_in_table(document.getElementById('enemy').innerText, '-', null)
                if (user === 'self') {
                    disable_input(true)
                    gameSocket.send(JSON.stringify({
                        "event": "NEW_USER_NUMBER",
                        "message": {
                            'number': '-',
                            'timer_ended': true
                        },
                    }))
                }
            }
            else {
                timer_div.innerHTML = current_time;
                current_time = current_time - 1;
            }
        },
        1000
    );
    timeouts.push(timer_counter);
}


function create_new_row(row_number) {
    let new_row = document.createElement('tr')
    new_row.id = "move_" + row_number;
    let col_1 = document.createElement('td')
    col_1.innerText = row_number
    let col_2 = document.createElement('td')
    col_2.className = 'target_number'
    col_2.innerText = '?'
    let col_3 = document.createElement('td')
    col_3.className = 'first_player_number'
    let col_4 = document.createElement('td')
    col_4.className = 'second_player_number'
    new_row.appendChild(col_1)
    new_row.appendChild(col_2)
    new_row.appendChild(col_3)
    new_row.appendChild(col_4)
    let table = document.querySelector('table tbody')
    table.appendChild(new_row);
}


$(function () {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    var csrftoken = getCookie('csrftoken');

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
});