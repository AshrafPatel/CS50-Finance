function chkUserForm() {
    let username = document.querySelector("#username").value
    let password = document.querySelector("#password").value

    let regex_username = /^[a-z0-9_-]{5,25}$/gm;
    let regex_password = /^(?=.*\d)(?=.*[A-Z])(?=.*[a-z])(?=.*[a-zA-Z!#$%&? "])[a-zA-Z0-9!#$%&?]{8,20}$/gm;

    if (regex_username.test(username || username == null || username == "")) {
        alert("Username must be between 5-25 characters.")
        return false
    }

    if (regex_password.test(password) || password == null || password == "") {
        alert("Password must be between 8 and 20 characters\n Must contain one lowercase, one uppercase, one number and a special character in the list (!#$%&?)\nPassword is case sensitive.")
        return false
    }
    return true;
}

function chkLogin() {
    let username2 = document.querySelector("#username").value
    let password2 = document.querySelector("#password").value

    if (username2 == null || username2 == "") {
        alert("Please provide a username")
        return false
    }

    if (password2 == null || password2 == "") {
        alert("Please provide a password")
        return false
    }
    return true
}

function chkBuyForm() {
    let quantity = document.querySelector("#quantity").value
    let symbol = document.querySelector("#symbol").value
    if (symbol == null || symbol == "") {
        alert("Please enter a valid stock symbol")
        return false
    }
    if (quantity == null || quantity == "") {
        alert("Please specify an amount")
        return false
    } else if (quantity < 0) {
        alert("Please a valid quantity")
        return false
    }
    return true
}

function chkSellForm() {
    let quantity = document.querySelector("#quantity").value
    if (quantity == null || quantity == "") {
        alert("Please specify an amount")
        return false
    } else if (quantity < 0) {
        alert("Please a valid quantity")
        return false
    }
    return true
}