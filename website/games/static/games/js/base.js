
let update_list = [];

function get_cookie(name) {
    let nameEQ = name + "=";
    let ca = document.cookie.split(';');
    for(let i=0;i < ca.length;i++) {
        let c = ca[i];
        while (c.charAt(0)===' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) === 0) return decodeURI(c.substring(nameEQ.length,c.length));
    }
    return null;
}

function update_and_replace(data_url, container, data) {
    let csrf_token = get_csrf_token();
    jQuery(function($) {
        data.csrfmiddlewaretoken = csrf_token;
        $.ajax({type: 'POST', url: data_url, data, dataType:'json', asynch: true, success:
            function(data) {
                replace_container(container, data.data)
            }}).fail(function() {
                console.error("Failed to update " + container);
            });
        }
    )
}

function update_and_callback(data_url, data, callback/*, args */) {
    let args = Array.prototype.slice.call(arguments, 3);
    let csrf_token = get_csrf_token();
    jQuery(function($) {
        data.csrfmiddlewaretoken = csrf_token;
        $.ajax({type: 'POST', url: data_url, data, dataType:'json', asynch: true, success:
            function(data) {
                args.unshift(data);
                callback.apply(this, args);
            }}).fail(function() {
                console.error("Failed to update");
            });
        }
    )
}

function replace_container(container, data) {
    container.innerHTML = data;
}

function add_update_list(func, args) {
    update_list.push({func: func, args: args});
}

function update_update_list() {
    for (let i = 0; i < update_list.length; i++) {
        try {
            update_list[i].func.apply(this, update_list[i].args);
        } catch (e) {
            console.error("Failed to update " + update_list[i].func + " with arguments " + update_list[i].args)
        }
    }
}

function get_csrf_token() {
    let cookie_csrf = get_cookie("csrf_token");
    if (cookie_csrf === null) {
        if (typeof CSRF_TOKEN !== 'undefined') {
            return CSRF_TOKEN;
        }
        else {
            throw "Unable to retrieve CSRF token";
        }
    }
    else {
        return cookie_csrf;
    }
}

$(document).ready(function() {
    update_update_list();
});