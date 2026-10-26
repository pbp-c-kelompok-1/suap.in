const liveclock = document.getElementById("liveclock");

function displayClock() {
    var current_time = new Date().getTime();
    const time_limit = new Date(current_time);
    time_limit.setHours(24, 0, 0, 0);

    var delta = time_limit - current_time;

    // Time calculations for days, hours, minutes and seconds
    var hours = Math.floor((delta % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    var minutes = Math.floor((delta % (1000 * 60 * 60)) / (1000 * 60));
    var seconds = Math.floor((delta % (1000 * 60)) / 1000);

    // Display the result in the element with id="demo"
    liveclock.innerHTML = hours + " jam, " + minutes + " menit, dan " + seconds + " detik";
    setTimeout(displayClock, 1000);
}

window.addEventListener("load", displayClock);