const badgeForm = document.getElementById('badge-form');

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function addBadge(event) {
    event.preventDefault();
    const submitButton = badgeForm.querySelector('button[type="submit"]');
    submitButton.disabled = true;

    fetch("/badges/create/", {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: new FormData(badgeForm),
        })
        .then((response) => {
            if (response.ok) {
                submitButton.disabled = false;
                badgeForm.reset();
                fetchBadges();
            }
        })
        .catch((error) => {
            console.log("Gagal menambahkan lencana: ", error);
        })
}

badgeForm.addEventListener("submit", addBadge);