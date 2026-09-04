(function () {
  const form = document.getElementById('contact-form');
  if (!form) return;

  const feedback = document.getElementById('form-feedback');
  const submitButton = document.getElementById('contact-submit');
  const serviceField = document.getElementById('service');
  const config = window.DOUCE_PATTE_CONFIG || {};

  const params = new URLSearchParams(window.location.search);
  const requestedService = params.get('service');
  if (requestedService && serviceField) {
    const knownValues = Array.from(serviceField.options).map((option) => option.value);
    if (knownValues.includes(requestedService)) serviceField.value = requestedService;
  }

  let recaptchaReady = null;
  if (config.recaptchaSiteKey && config.recaptchaSiteKey !== 'REPLACE_WITH_RECAPTCHA_SITE_KEY') {
    const script = document.createElement('script');
    script.src = `https://www.google.com/recaptcha/api.js?render=${config.recaptchaSiteKey}`;
    recaptchaReady = new Promise((resolve) => {
      script.addEventListener('load', () => window.grecaptcha.ready(resolve));
    });
    document.head.appendChild(script);
  }

  function setFeedback(message, ok) {
    feedback.textContent = message;
    feedback.className = message ? `form-feedback ${ok ? 'success' : 'error'}` : 'form-feedback';
  }

  async function getRecaptchaToken() {
    if (!recaptchaReady) return null;
    await recaptchaReady;
    return window.grecaptcha.execute(config.recaptchaSiteKey, { action: 'contact' });
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!form.checkValidity()) {
      form.reportValidity();
      setFeedback('Veuillez remplir correctement tous les champs.', false);
      return;
    }

    submitButton.disabled = true;
    setFeedback('Envoi en cours...', true);

    try {
      const token = await getRecaptchaToken();
      const payload = {
        name: form.name.value.trim(),
        email: form.email.value.trim(),
        phone: form.phone.value.trim(),
        service: form.service.value,
        message: form.message.value.trim(),
        website: form.website.value,
        recaptcha_token: token
      };

      const response = await fetch(`${config.apiBaseUrl || ''}/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setFeedback('', true);
        form.reset();
        openSuccessModal();
      } else if (response.status === 422) {
        setFeedback('Certains champs sont invalides. Merci de les corriger avant de renvoyer votre demande.', false);
      } else {
        setFeedback("Une erreur est survenue. Merci de réessayer ou de m'écrire directement par e-mail.", false);
      }
    } catch (error) {
      setFeedback("Une erreur est survenue. Merci de réessayer ou de m'écrire directement par e-mail.", false);
    } finally {
      submitButton.disabled = false;
    }
  }

  form.addEventListener('submit', handleSubmit);

  // ----- Popup de succès -----
  const modal = document.getElementById('success-modal');
  if (!modal) return;

  const panel = modal.querySelector('.modal-panel');
  const closeButtons = modal.querySelectorAll('[data-modal-close]');
  const checkCircle = modal.querySelector('.modal-check-circle');
  const checkPath = modal.querySelector('.modal-check-path');
  let lastFocused = null;

  function focusableElements() {
    return Array.from(modal.querySelectorAll('button, a[href]')).filter((el) => !el.hidden);
  }

  function handleModalKeydown(event) {
    if (event.key === 'Escape') {
      closeSuccessModal();
      return;
    }
    if (event.key !== 'Tab') return;

    const focusable = focusableElements();
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function spawnConfetti() {
    const colors = ['#bd4732', '#d4877a', '#bfd5c5', '#f1e8dc'];
    const burst = [];
    for (let i = 0; i < 14; i += 1) {
      const dot = document.createElement('span');
      dot.className = 'modal-confetti';
      dot.style.background = colors[i % colors.length];
      panel.appendChild(dot);
      burst.push(dot);
    }

    burst.forEach((dot, i) => {
      const angle = (Math.PI * 2 * i) / burst.length + Math.random() * .5;
      const distance = 90 + Math.random() * 70;
      gsap.fromTo(
        dot,
        { opacity: 1, scale: 0, x: 0, y: 0, rotate: 0 },
        {
          opacity: 0,
          scale: 1,
          x: Math.cos(angle) * distance,
          y: Math.sin(angle) * distance - 20,
          rotate: (Math.random() - .5) * 320,
          duration: 1.1 + Math.random() * .4,
          ease: 'power2.out',
          delay: .15,
          onComplete: () => dot.remove()
        }
      );
    });
  }

  function openSuccessModal() {
    lastFocused = document.activeElement;
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    modal.addEventListener('keydown', handleModalKeydown);
    modal.addEventListener('click', handleBackdropClick);

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const gsapReady = typeof gsap !== 'undefined';

    if (checkCircle && checkPath) {
      [checkCircle, checkPath].forEach((path) => {
        const length = path.getTotalLength();
        path.style.strokeDasharray = String(length);
        path.style.strokeDashoffset = reduced || !gsapReady ? '0' : String(length);
      });
    }

    if (reduced || !gsapReady) {
      panel.style.opacity = '1';
      panel.style.transform = 'none';
    } else {
      gsap.set(modal, { opacity: 0 });
      gsap.set(panel, { opacity: 0, scale: .55, y: 50, rotate: -6 });
      const tl = gsap.timeline();
      tl.to(modal, { opacity: 1, duration: .25, ease: 'power1.out' })
        .to(panel, { opacity: 1, scale: 1, y: 0, rotate: 0, duration: .8, ease: 'back.out(1.9)' }, '-=.1')
        .to(checkCircle, { strokeDashoffset: 0, duration: .5, ease: 'power2.out' }, '-=.35')
        .to(checkPath, { strokeDashoffset: 0, duration: .45, ease: 'power2.out' }, '-=.2')
        .add(spawnConfetti, '-=.3');
    }

    (closeButtons[0] || panel).focus();
  }

  function handleBackdropClick(event) {
    if (event.target === modal) closeSuccessModal();
  }

  function closeSuccessModal() {
    if (modal.hidden) return;
    modal.hidden = true;
    document.body.style.overflow = '';
    modal.removeEventListener('keydown', handleModalKeydown);
    modal.removeEventListener('click', handleBackdropClick);
    if (lastFocused) lastFocused.focus();
  }

  closeButtons.forEach((button) => button.addEventListener('click', closeSuccessModal));
})();
