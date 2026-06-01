document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.follow-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const username = btn.dataset.username;

            fetch('/social/follow/' + username + '/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCsrfToken(),
                },
            })
                .then(function (response) {
                    if (response.status === 401) {
                        window.location.href = '/accounts/login/';
                        return null;
                    }
                    return response.json();
                })
                .then(function (data) {
                    if (!data) return;
                    btn.classList.toggle('follow-btn--active', data.following);
                    btn.textContent = data.following ? 'Отписаться' : 'Подписаться';
                    const counter = document.querySelector('.followers-count');
                    if (counter) counter.textContent = data.count;
                });
        });
    });
});
