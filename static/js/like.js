function applyLikeState(btn, liked, count) {
    btn.classList.toggle('like-btn--active', liked);
    btn.querySelector('.like-count').textContent = count;
}

function initLikeButton(btn) {
    const postId = btn.dataset.postId;
    const reviewId = btn.dataset.reviewId;
    const param = postId ? 'post_id=' + postId : 'review_id=' + reviewId;

    ajaxDeferred('/social/like/status/?' + param)
        .done(function (data) {
            applyLikeState(btn, data.liked, data.count);
        })
        .fail(function (err) {
            console.error('Не удалось загрузить состояние лайка', err);
        });

    btn.addEventListener('click', function () {
        btn.disabled = true;

        ajaxDeferred('/social/like/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken(),
            },
            body: param,
        })
            .done(function (data) {
                applyLikeState(btn, data.liked, data.count);
            })
            .fail(function (err) {
                if (err.status === 401) {
                    window.location.href = '/accounts/login/';
                } else {
                    console.error('Ошибка при лайке', err);
                }
            })
            .always(function () {
                btn.disabled = false;
            });
    });
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.like-btn[data-post-id], .like-btn[data-review-id]').forEach(initLikeButton);
});
