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

async function deleteBadge(badgeCode) {
    if (!confirm("Apakah anda yakin ingin menghapus lencana ini?")) {
        return;
    }

    fetch(`/badges/${badgeCode}/delete/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        })
        .then((response) => {
            if (response.ok) fetchBadges();
        })
        .catch((error) => {
            console.error("Terjadi kesalahan dalam menghapus lencana:", error);
            alert("Terjadi kesalahan dalam menghapus lencana.");
        })
}

document.addEventListener("click", (event) => {
    const button = event.target.closest(".delete-badge");

    if (!button) return;

    deleteBadge(button.dataset.code);
});