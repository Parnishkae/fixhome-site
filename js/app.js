/* =====================================================
   РемонтПро — Главный JS-файл
   Подключается на каждой странице.
   Логика разделена на модули — каждый запускается только
   если на странице найдены соответствующие элементы.
   ===================================================== */

(function () {
    'use strict';

    /* ============ 1. БУРГЕР-МЕНЮ (мобильное) ============ */
    function initBurger() {
        const burger = document.getElementById('burger');
        const nav = document.getElementById('nav');

        if (!burger || !nav) return;

        burger.addEventListener('click', function () {
            burger.classList.toggle('is-active');
            nav.classList.toggle('is-open');
            document.body.classList.toggle('menu-open');
        });

        // Закрытие меню при клике на ссылку (мобильный)
        nav.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                burger.classList.remove('is-active');
                nav.classList.remove('is-open');
                document.body.classList.remove('menu-open');
            });
        });
    }

    /* ============ 2. ТЕНЬ ХЕДЕРА ПРИ СКРОЛЛЕ ============ */
    function initHeaderShadow() {
        const header = document.getElementById('header');
        if (!header) return;

        const onScroll = function () {
            if (window.scrollY > 20) {
                header.classList.add('is-scrolled');
            } else {
                header.classList.remove('is-scrolled');
            }
        };

        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    /* ============ 3. АНИМАЦИЯ ПОЯВЛЕНИЯ ПРИ СКРОЛЛЕ ============ */
    function initReveal() {
        const elements = document.querySelectorAll('.reveal');
        if (!elements.length || !('IntersectionObserver' in window)) {
            // Fallback: показываем сразу
            elements.forEach(function (el) { el.classList.add('is-visible'); });
            return;
        }

        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.12,
            rootMargin: '0px 0px -60px 0px'
        });

        elements.forEach(function (el) { observer.observe(el); });
    }

    /* ============ 4. ПЛАВНЫЙ СКРОЛЛ ДЛЯ ЯКОРЕЙ ============ */
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
            anchor.addEventListener('click', function (e) {
                const href = this.getAttribute('href');
                if (href === '#' || href.length < 2) return;

                const target = document.querySelector(href);
                if (!target) return;

                e.preventDefault();
                const headerHeight = 76;
                const offset = target.getBoundingClientRect().top + window.scrollY - headerHeight;
                window.scrollTo({ top: offset, behavior: 'smooth' });
            });
        });
    }

    /* ============ 5. ЗАГРУЗКА УСЛУГ ИЗ JSON ============ */
    async function loadServices() {
        const popular = document.getElementById('popularServices');
        const all = document.getElementById('allServices');

        if (!popular && !all) return;

        // Loader
        const loader = '<div class="services-loading">Загружаем услуги…</div>';
        if (popular) popular.innerHTML = loader;
        if (all) all.innerHTML = loader;

        try {
            const response = await fetch('data/services.json', { cache: 'no-store' });
            if (!response.ok) throw new Error('HTTP ' + response.status);
            const services = await response.json();

            // Главная: 3 популярных (помеченных popular: true) или первые 3
            if (popular) {
                const popularItems = services.filter(function (s) { return s.popular; });
                const list = popularItems.length ? popularItems.slice(0, 3) : services.slice(0, 3);
                popular.innerHTML = list.map(renderServiceCard).join('');
            }

            // Услуги: все
            if (all) {
                all.innerHTML = services.map(renderServiceCard).join('');
            }

            // Привязка кнопок «Заказать»
            attachOrderButtons();

            // Re-init reveal для новых элементов
            initReveal();

        } catch (err) {
            console.error('Не удалось загрузить услуги:', err);
            const msg = '<div class="services-loading">Не удалось загрузить услуги. Откройте сайт через локальный сервер (например, Live Server в VS Code).</div>';
            if (popular) popular.innerHTML = msg;
            if (all) all.innerHTML = msg;
        }
    }

    /* Рендер одной карточки услуги */
    function renderServiceCard(service) {
        // Если картинка указана — используем её, иначе показываем градиентный fallback
        const hasImage = service.image && service.image.length > 0;
        const imageStyle = hasImage ? 'style="background-image: url(\'' + escapeAttr(service.image) + '\');"' : '';
        const imageClass = 'service-card__image' + (hasImage ? '' : ' service-card__image--fallback');

        return [
            '<article class="service-card reveal">',
                '<div class="' + imageClass + '" ' + imageStyle + '></div>',
                '<div class="service-card__body">',
                    '<h3 class="service-card__title">' + escapeHtml(service.title) + '</h3>',
                    '<span class="service-card__price">' + escapeHtml(service.price) + '</span>',
                    '<p class="service-card__desc">' + escapeHtml(service.description) + '</p>',
                    '<button type="button" class="service-card__btn" data-order="' + escapeAttr(service.title) + '">Заказать</button>',
                '</div>',
            '</article>'
        ].join('');
    }

    /* Привязка событий к кнопкам заказа */
    function attachOrderButtons() {
        document.querySelectorAll('[data-order]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const serviceName = btn.getAttribute('data-order');
                openOrderModal(serviceName);
            });
        });
    }

    /* ============ 6. МОДАЛЬНОЕ ОКНО ЗАКАЗА ============ */
    function openOrderModal(serviceName) {
        const modal = document.getElementById('orderModal');
        if (!modal) {
            // Если модалки нет (например, на главной) — просто прокручиваем к форме
            showToast('Услуга «' + serviceName + '» выбрана. Заполните форму ниже.', 'success');
            const contactSection = document.getElementById('contact') || document.querySelector('#contactForm');
            if (contactSection) {
                contactSection.scrollIntoView({ behavior: 'smooth' });
            }
            return;
        }

        const nameField = document.getElementById('modalServiceName');
        const hidden = document.getElementById('modalService');
        if (nameField) nameField.textContent = serviceName;
        if (hidden) hidden.value = serviceName;

        modal.classList.add('is-open');
        document.body.classList.add('menu-open');
    }

    function initModal() {
        const modal = document.getElementById('orderModal');
        if (!modal) return;

        modal.querySelectorAll('[data-close]').forEach(function (el) {
            el.addEventListener('click', closeModal);
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && modal.classList.contains('is-open')) {
                closeModal();
            }
        });

        function closeModal() {
            modal.classList.remove('is-open');
            document.body.classList.remove('menu-open');
        }
    }

    /* ============ 7. ОБРАБОТКА ФОРМ ============ */
    function initForms() {
        document.querySelectorAll('form.form').forEach(function (form) {
            form.addEventListener('submit', handleFormSubmit);
        });
    }

    function handleFormSubmit(e) {
        e.preventDefault();
        const form = e.currentTarget;

        // Очищаем старые ошибки
        form.querySelectorAll('.form__field').forEach(function (f) {
            f.classList.remove('has-error');
        });
        form.querySelectorAll('.form__error').forEach(function (el) {
            el.textContent = '';
        });

        // Валидация
        const data = {};
        let isValid = true;

        const nameInput = form.querySelector('input[name="name"]');
        const phoneInput = form.querySelector('input[name="phone"]');
        const commentInput = form.querySelector('textarea[name="comment"]');
        const serviceInput = form.querySelector('input[name="service"]');

        if (nameInput) {
            const name = nameInput.value.trim();
            if (name.length < 2) {
                showFieldError(nameInput, 'Введите имя (минимум 2 символа)');
                isValid = false;
            } else if (!/^[a-zA-Zа-яА-ЯёЁіїєІЇЄҐґ\s'-]+$/.test(name)) {
                showFieldError(nameInput, 'Имя содержит недопустимые символы');
                isValid = false;
            }
            data.name = name;
        }

        if (phoneInput) {
            const phone = phoneInput.value.trim();
            // Считаем количество цифр
            const digits = phone.replace(/\D/g, '');
            if (digits.length < 10) {
                showFieldError(phoneInput, 'Введите корректный номер телефона');
                isValid = false;
            }
            data.phone = phone;
        }

        if (commentInput) data.comment = commentInput.value.trim();
        if (serviceInput) data.service = serviceInput.value;

        if (!isValid) {
            showToast('Пожалуйста, проверьте заполнение формы', 'error');
            return;
        }

        // Имитация отправки (фронтенд-only)
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Отправляем…';

        // Имитируем запрос. В реальном проекте здесь fetch к backend (например, /api/order.php)
        setTimeout(function () {
            console.log('Отправка заявки:', data);
            showToast('Спасибо! Мы свяжемся с вами в течение 15 минут.', 'success');
            form.reset();
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;

            // Закрываем модалку, если форма была в ней
            const modal = document.getElementById('orderModal');
            if (modal && modal.classList.contains('is-open')) {
                setTimeout(function () {
                    modal.classList.remove('is-open');
                    document.body.classList.remove('menu-open');
                }, 800);
            }
        }, 900);
    }

    function showFieldError(input, message) {
        const field = input.closest('.form__field');
        if (!field) return;
        field.classList.add('has-error');
        const errorEl = field.querySelector('.form__error');
        if (errorEl) errorEl.textContent = message;
    }

    /* ============ 8. TOAST-УВЕДОМЛЕНИЯ ============ */
    let toastTimer = null;
    function showToast(message, type) {
        const toast = document.getElementById('toast');
        if (!toast) {
            alert(message);
            return;
        }

        toast.textContent = message;
        toast.className = 'toast is-visible';
        if (type === 'success') toast.classList.add('toast--success');
        if (type === 'error') toast.classList.add('toast--error');

        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () {
            toast.classList.remove('is-visible');
        }, 4000);
    }

    /* ============ 9. УТИЛИТЫ — ЭКРАНИРОВАНИЕ ============ */
    function escapeHtml(str) {
        if (str == null) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function escapeAttr(str) {
        if (str == null) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /* ============ 10. МАСКА ТЕЛЕФОНА ============ */
    function initPhoneMask() {
        document.querySelectorAll('input[type="tel"]').forEach(function (input) {
            input.addEventListener('input', function (e) {
                let value = e.target.value.replace(/\D/g, '');
                if (value.startsWith('38')) value = value.substring(2);
                if (value.length > 10) value = value.substring(0, 10);

                let formatted = '+38 ';
                if (value.length > 0) formatted += '(' + value.substring(0, 3);
                if (value.length >= 3) formatted += ') ' + value.substring(3, 6);
                if (value.length >= 6) formatted += '-' + value.substring(6, 8);
                if (value.length >= 8) formatted += '-' + value.substring(8, 10);

                e.target.value = formatted.trim();
            });

            input.addEventListener('focus', function (e) {
                if (!e.target.value) e.target.value = '+38 (';
            });

            input.addEventListener('blur', function (e) {
                if (e.target.value === '+38 (' || e.target.value === '+38') {
                    e.target.value = '';
                }
            });
        });
    }

    /* ============ ИНИЦИАЛИЗАЦИЯ ============ */
    document.addEventListener('DOMContentLoaded', function () {
        initBurger();
        initHeaderShadow();
        initSmoothScroll();
        initReveal();
        initForms();
        initPhoneMask();
        initModal();
        loadServices();
    });

})();
