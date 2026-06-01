document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            let valid = true;

            form.querySelectorAll('[data-error]').forEach(el => el.remove());

            form.querySelectorAll('input, textarea, select').forEach(function (field) {
                if (!field.name || field.type === 'hidden' || field.type === 'submit') return;

                const value = field.value.trim();
                let error = '';

                if (field.required && value === '') {
                    error = 'Это поле обязательно для заполнения.';
                } else if (value !== '') {
                    const min = field.getAttribute('minlength');
                    const max = field.getAttribute('maxlength');
                    if (min && value.length < parseInt(min)) {
                        error = `Минимальная длина — ${min} символов.`;
                    } else if (max && value.length > parseInt(max)) {
                        error = `Максимальная длина — ${max} символов.`;
                    } else if (field.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                        error = 'Введите корректный email.';
                    } else if (field.type === 'number') {
                        const num = parseFloat(value);
                        const minVal = field.getAttribute('min');
                        const maxVal = field.getAttribute('max');
                        if (minVal && num < parseFloat(minVal)) {
                            error = `Минимальное значение — ${minVal}.`;
                        } else if (maxVal && num > parseFloat(maxVal)) {
                            error = `Максимальное значение — ${maxVal}.`;
                        }
                    }
                }

                if (error) {
                    valid = false;
                    const span = document.createElement('span');
                    span.className = 'form-error';
                    span.setAttribute('data-error', '1');
                    span.textContent = error;
                    field.insertAdjacentElement('afterend', span);
                }
            });

            if (!valid) e.preventDefault();
        });
    });
});
