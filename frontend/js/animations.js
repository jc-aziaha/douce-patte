(function () {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReducedMotion || typeof gsap === 'undefined') return;

  if (typeof ScrollTrigger !== 'undefined') gsap.registerPlugin(ScrollTrigger);

  // ----- Révélation de texte, mot par mot -----
  function splitWords(el) {
    const text = el.textContent;
    el.setAttribute('aria-label', text);
    el.textContent = '';
    const words = text.split(' ');
    words.forEach((word, i) => {
      const mask = document.createElement('span');
      mask.className = 'word-mask';
      mask.setAttribute('aria-hidden', 'true');
      const inner = document.createElement('span');
      inner.className = 'word';
      inner.textContent = word + (i < words.length - 1 ? ' ' : '');
      mask.appendChild(inner);
      el.appendChild(mask);
    });
    return el.querySelectorAll('.word');
  }

  const heroHeading = document.querySelector('.hero h1, .page-hero h1');
  if (heroHeading) {
    const words = splitWords(heroHeading);
    gsap.from(words, {
      yPercent: 130,
      rotate: 4,
      duration: 1,
      stagger: .045,
      delay: .1,
      ease: 'power4.out'
    });
  }

  document.querySelectorAll('h2').forEach((heading) => {
    if (heading.closest('.modal-backdrop')) return;
    const words = splitWords(heading);
    gsap.from(words, {
      yPercent: 130,
      rotate: 3,
      duration: .85,
      stagger: .035,
      ease: 'power4.out',
      scrollTrigger: { trigger: heading, start: 'top 88%' }
    });
  });

  // ----- Ouverture de la hero (texte + photo) -----
  const heroContent = document.querySelector('.hero-content');
  const heroIllustration = document.querySelector('.hero-illustration');
  if (heroContent) {
    gsap.from(heroContent.children, {
      opacity: 0,
      y: 22,
      duration: .8,
      stagger: .07,
      delay: .15,
      ease: 'power2.out'
    });
  }
  if (heroIllustration) {
    gsap.from(heroIllustration, { opacity: 0, y: 22, duration: .8, delay: .2, ease: 'power2.out' });
  }

  // ----- Reveal cinématique des photographies -----
  // Le léger zoom (scale 1.14 -> 1) déborde du cadre pendant l'animation ;
  // sans risque pour les photos avec marge autour (hero, à-propos, services),
  // mais la bande .gallery est en plein bord d'écran et ce débordement y
  // provoquait un vrai scroll horizontal sur mobile (confirmé sur iPhone
  // réel, pas un artefact d'outil de test) — cette bande garde donc un
  // fondu simple, sans mise à l'échelle.
  const photoSelectors = ['.pet-card', '.about-photo', '.story-photo', '.detail-photo'];
  document.querySelectorAll(photoSelectors.join(',')).forEach((img) => {
    gsap.fromTo(
      img,
      { scale: 1.14, opacity: 0, filter: 'saturate(.3) brightness(.82)' },
      {
        scale: 1,
        opacity: 1,
        filter: 'saturate(1) brightness(1)',
        duration: 1.2,
        ease: 'power3.out',
        scrollTrigger: { trigger: img, start: 'top 90%' }
      }
    );
  });

  document.querySelectorAll('.gallery img').forEach((img) => {
    gsap.fromTo(
      img,
      { opacity: 0, filter: 'saturate(.3) brightness(.82)' },
      {
        opacity: 1,
        filter: 'saturate(1) brightness(1)',
        duration: 1.2,
        ease: 'power3.out',
        scrollTrigger: { trigger: img, start: 'top 90%' }
      }
    );
  });

  // ----- Apparition des groupes de contenu au scroll -----
  if (typeof ScrollTrigger !== 'undefined') {
    // Groupes en rangée (cartes côte à côte) : un fondu discret, sans
    // mouvement ni zoom, pour qu'aucune carte ne semble désalignée pendant
    // que ses voisines sont encore en train d'apparaître.
    const rowGroupSelectors = ['.cards', '.detail-list'];
    document.querySelectorAll(rowGroupSelectors.join(',')).forEach((group) => {
      const targets = group.children.length ? Array.from(group.children) : [group];
      gsap.from(targets, {
        opacity: 0,
        y: 10,
        duration: .6,
        ease: 'power2.out',
        stagger: .05,
        scrollTrigger: { trigger: group, start: 'top 85%' }
      });
    });

    const revealGroupSelectors = [
      '.section-heading', '.steps',
      '.about-content', '.about-story', '.contact-intro', '.direct-contact'
    ];

    document.querySelectorAll(revealGroupSelectors.join(',')).forEach((group) => {
      const targets = group.children.length ? Array.from(group.children) : [group];
      gsap.from(targets, {
        opacity: 0,
        y: 30,
        scale: .96,
        duration: .75,
        ease: 'back.out(1.15)',
        stagger: .05,
        scrollTrigger: { trigger: group, start: 'top 85%' }
      });
    });
  }

  // ----- Inclinaison 3D de la galerie photo -----
  if (window.matchMedia('(pointer: fine)').matches) {
    document.querySelectorAll('.gallery img').forEach((img) => {
      const rotX = gsap.quickTo(img, 'rotationX', { duration: .4, ease: 'power2' });
      const rotY = gsap.quickTo(img, 'rotationY', { duration: .4, ease: 'power2' });
      const scale = gsap.quickTo(img, 'scale', { duration: .4, ease: 'power2' });
      img.addEventListener('mousemove', (event) => {
        const rect = img.getBoundingClientRect();
        const px = (event.clientX - rect.left) / rect.width - .5;
        const py = (event.clientY - rect.top) / rect.height - .5;
        rotY(px * 16);
        rotX(-py * 16);
      });
      img.addEventListener('mouseenter', () => scale(1.06));
      img.addEventListener('mouseleave', () => {
        rotX(0);
        rotY(0);
        scale(1);
      });
    });
  }

  // ----- Icônes des engagements dessinées au trait (page À propos) -----
  document.querySelectorAll('.illus svg path, .illus svg circle').forEach((shape) => {
    if (typeof shape.getTotalLength !== 'function') return;
    const length = shape.getTotalLength();
    gsap.set(shape, { strokeDasharray: length, strokeDashoffset: length });
    gsap.to(shape, {
      strokeDashoffset: 0,
      duration: 1,
      ease: 'power2.out',
      scrollTrigger: { trigger: shape.closest('.card'), start: 'top 85%' }
    });
  });

  // ----- Boutons magnétiques -----
  if (window.matchMedia('(pointer: fine)').matches) {
    document.querySelectorAll('.button, .service-cta').forEach((el) => {
      const moveX = gsap.quickTo(el, 'x', { duration: .45, ease: 'power3' });
      const moveY = gsap.quickTo(el, 'y', { duration: .45, ease: 'power3' });
      el.addEventListener('mousemove', (event) => {
        const rect = el.getBoundingClientRect();
        moveX((event.clientX - rect.left - rect.width / 2) * .35);
        moveY((event.clientY - rect.top - rect.height / 2) * .35);
      });
      el.addEventListener('mouseleave', () => {
        moveX(0);
        moveY(0);
      });
    });
  }

  // ----- Petits clins d'œil pendant la saisie du formulaire -----
  const contactForm = document.getElementById('contact-form');
  if (contactForm) {
    const makePaw = (className) => {
      const span = document.createElement('span');
      span.className = className;
      span.setAttribute('aria-hidden', 'true');
      return span;
    };

    contactForm.querySelectorAll('.field').forEach((field) => {
      const control = field.querySelector('input, select, textarea');
      if (!control) return;
      const paw = makePaw('field-paw');
      field.appendChild(paw);
      gsap.set(paw, { opacity: 0, scale: .4, rotate: -20 });

      control.addEventListener('focus', () => {
        gsap.to(paw, { opacity: .9, scale: 1, rotate: 0, duration: .5, ease: 'back.out(2.4)' });
      });
      control.addEventListener('blur', () => {
        gsap.to(paw, { opacity: 0, scale: .4, rotate: 20, duration: .35, ease: 'power2.in' });
      });
    });

    const privacyCheckbox = document.getElementById('privacy-notice');
    const privacyWrap = privacyCheckbox ? privacyCheckbox.closest('.privacy-check') : null;
    if (privacyCheckbox && privacyWrap) {
      const stampPaw = makePaw('checkbox-paw');
      privacyWrap.appendChild(stampPaw);
      gsap.set(stampPaw, { opacity: 0, scale: .3, rotate: -25 });

      privacyCheckbox.addEventListener('change', () => {
        if (privacyCheckbox.checked) {
          gsap.fromTo(
            stampPaw,
            { opacity: 1, scale: .3, rotate: -25 },
            { opacity: 1, scale: 1, rotate: 0, duration: .5, ease: 'back.out(3)' }
          );
          gsap.to(stampPaw, { opacity: 0, delay: 1.2, duration: .4 });
        } else {
          gsap.to(stampPaw, { opacity: 0, duration: .2 });
        }
      });
    }
  }

  // Les images redimensionnées après chargement peuvent décaler les triggers.
  window.addEventListener('load', () => {
    if (typeof ScrollTrigger !== 'undefined') ScrollTrigger.refresh();
  });
})();
