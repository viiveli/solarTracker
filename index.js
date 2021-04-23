let xhr = new XMLHttpRequest();
xhr.timeout = 2500;

getStatus();

let status_query = setInterval(getStatus, 5000);

function rotateTracker(direction) {
    switch(direction) {
        case 1:
            xhr.open("POST", "/?rotatehccw", true);
            break;
        case 2:
            xhr.open("POST", "/?rotatehcw", true);
            break;
        case 3:
            xhr.open("POST", "/?rotatevccw", true);
            break;
        case 4:
            xhr.open("POST", "/?rotatevcw", true);
            break;
    }

    xhr.send();
}

function getStatus() {
    xhr.open("GET", "/?status", true)
    xhr.send();

    xhr.onload = function() {
        let deviceStatus = JSON.parse(this.response)

        let level = deviceStatus['powerlevel'];
        let trackerStatus = deviceStatus['running'];
        let hibernationStatus = deviceStatus['hibernate'];

        document.getElementById("powerLevel").innerText = level + '%';

        if (trackerStatus == true && hibernationStatus == true) {
            document.getElementById("statusInfo").innerText = 'tracker on, in hibernation';
            document.getElementById("toggleTracker").checked = true;
        } else if (trackerStatus == true && hibernationStatus == false) {
            document.getElementById("statusInfo").innerText = 'tracking';
            document.getElementById("toggleTracker").checked = true;
        } else {
            document.getElementById("statusInfo").innerText = 'tracker off';
            document.getElementById("toggleTracker").checked = false;
        }
    }
}

function restartTracker() {
    xhr.open("POST", "/?restart", true);

    document.getElementById("toggleTracker").disabled = true;
    
    let inputs = document.getElementsByClassName('axisControls');
    for(let i = 0; i < inputs.length; i++) {
        inputs[i].disabled = true;
    }

    xhr.send();
    setTimeout(function(){ location.reload() }, 10000);
}

function toggleTracker(element) {
    if (element.checked) {
        xhr.open("POST", "/?trackeron", true);
        
        let inputs = document.getElementsByClassName('axisControls');
        for(let i = 0; i < inputs.length; i++) {
            inputs[i].disabled = true;
        }
    }
    else {
        xhr.open("POST", "/?trackeroff", true);

        let inputs = document.getElementsByClassName('axisControls');
        for(let i = 0; i < inputs.length; i++) {
            inputs[i].disabled = false;
        }
    }
    
    xhr.send();
    setTimeout(getStatus, 2500);
}
