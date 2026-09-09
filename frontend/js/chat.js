(function () {
  const config = window.DOUCE_PATTE_CONFIG || {};
  const MAX_MESSAGE_LENGTH = 500;
  const WAKE_HINT_DELAY_MS = 4000;
  const REQUEST_TIMEOUT_MS = 65000;

  const SUGGESTIONS = [
    'Dans quel secteur intervenez-vous ?',
    'Combien coûte une promenade ?',
    'Quels animaux acceptez-vous ?'
  ];

  const WELCOME_MESSAGE =
    "Bonjour ! Je suis l'assistant automatisé du site Douce Patte. Je réponds uniquement " +
    'en français, aux questions courantes (secteur, tarifs indicatifs, moyens de paiement, ' +
    "organisation d'une garde...). Je ne confirme en revanche jamais de disponibilité réelle " +
    'ni de tarif définitif : pour ça, le formulaire de contact reste la meilleure option.';

  const NETWORK_FALLBACK_MESSAGE =
    "Je ne peux pas vous répondre pour le moment. Merci d'utiliser le formulaire de " +
    'contact : Manon vous répondra directement.';

  const WAKE_HINT_MESSAGE =
    'Le service se réveille après une période sans visite, cela peut prendre environ une ' +
    'minute. Vous pouvez patienter, ou utiliser le formulaire de contact.';

  // sessionStorage (pas localStorage) : la conversation survit à la
  // navigation entre pages du site, mais disparaît à la fermeture de
  // l'onglet — jamais reportée d'une visite à l'autre, conformément à la
  // politique de confidentialité. Rien n'est envoyé au serveur.
  const SESSION_KEY = 'douce-patte-chat-session';

  function loadSession() {
    try {
      const raw = sessionStorage.getItem(SESSION_KEY);
      const parsed = raw ? JSON.parse(raw) : null;
      return { entries: Array.isArray(parsed && parsed.entries) ? parsed.entries : [] };
    } catch (error) {
      return { entries: [] };
    }
  }

  function saveSession(session) {
    try {
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
    } catch (error) {
      /* Stockage indisponible (navigation privée, quota...) : la conversation
         reste utilisable sur la page en cours, simplement pas reportée à la
         suivante. */
    }
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function buildWidget() {
    const widget = el('div', 'chat-widget');
    widget.id = 'chat-widget';

    const toggle = el('button', 'chat-toggle');
    toggle.type = 'button';
    toggle.setAttribute('aria-haspopup', 'dialog');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-controls', 'chat-panel');
    toggle.setAttribute('aria-label', "Ouvrir l'assistant du site");
    toggle.innerHTML =
      '<svg class="icon-chat" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5Z"/></svg>' +
      '<svg class="icon-close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';

    const panel = el('section', 'chat-panel');
    panel.id = 'chat-panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-modal', 'false');
    panel.setAttribute('aria-label', 'Assistant Douce Patte');
    panel.hidden = true;

    const header = el('header', 'chat-panel-header');
    header.appendChild(el('p', 'chat-panel-title', 'Assistant Douce Patte'));
    const close = el('button', 'chat-close', '×');
    close.type = 'button';
    close.setAttribute('aria-label', 'Fermer la conversation');
    header.appendChild(close);

    const messages = el('div', 'chat-messages');
    messages.id = 'chat-messages';
    messages.setAttribute('role', 'log');
    messages.setAttribute('aria-live', 'polite');
    messages.setAttribute('aria-relevant', 'additions');

    const suggestions = el('div', 'chat-suggestions');
    suggestions.id = 'chat-suggestions';
    SUGGESTIONS.forEach((question) => {
      const button = el('button', 'chat-suggestion', question);
      button.type = 'button';
      suggestions.appendChild(button);
    });

    const form = el('form', 'chat-form');
    const label = el('label', 'sr-only', 'Votre message');
    label.setAttribute('for', 'chat-input');
    const textarea = document.createElement('textarea');
    textarea.id = 'chat-input';
    textarea.name = 'message';
    textarea.rows = 1;
    textarea.maxLength = MAX_MESSAGE_LENGTH;
    textarea.required = true;
    textarea.placeholder = 'Posez votre question...';
    textarea.setAttribute('autocomplete', 'off');
    const send = el('button', 'chat-send');
    send.type = 'submit';
    send.setAttribute('aria-label', 'Envoyer le message');
    send.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>';
    form.append(label, textarea, send);

    const disclaimer = el(
      'p',
      'chat-disclaimer',
      "Assistant automatisé : il ne confirme ni disponibilité ni tarif définitif. Voir la "
    );
    const disclaimerLink = document.createElement('a');
    disclaimerLink.href = '/confidentialite.html';
    disclaimerLink.textContent = 'politique de confidentialité';
    disclaimer.appendChild(disclaimerLink);
    disclaimer.appendChild(document.createTextNode('.'));

    panel.append(header, messages, suggestions, form, disclaimer);
    widget.append(toggle, panel);
    document.body.appendChild(widget);

    return { widget, toggle, panel, messages, suggestions, form, textarea, send, close };
  }

  function scrollToBottom(messages) {
    messages.scrollTop = messages.scrollHeight;
  }

  function buildSystemMessage(text) {
    return el('div', 'chat-message chat-message-system', text);
  }

  function addMessage(messages, text, variant) {
    const bubble = el('div', `chat-message chat-message-${variant}`, text);
    messages.appendChild(bubble);
    scrollToBottom(messages);
    return bubble;
  }

  function addSystemMessage(messages, text) {
    return addMessage(messages, text, 'system');
  }

  function addBotAnswer(messages, text, status) {
    const bubble = el('div', 'chat-message chat-message-bot');
    if (status === 'out_of_scope') {
      bubble.classList.add('is-out-of-scope');
    }
    bubble.appendChild(document.createTextNode(text));
    messages.appendChild(bubble);
    scrollToBottom(messages);
  }

  function focusableElements(panel) {
    return Array.from(
      panel.querySelectorAll('button, a[href], textarea, input, [tabindex]:not([tabindex="-1"])')
    ).filter((node) => !node.hidden && node.offsetParent !== null);
  }

  function init() {
    const { widget, toggle, panel, messages, suggestions, form, textarea, send, close } =
      buildWidget();

    const session = loadSession();
    let requestInFlight = false;

    session.entries.forEach((entry) => {
      if (entry.kind === 'bot') addBotAnswer(messages, entry.text, entry.status);
      else addMessage(messages, entry.text, entry.kind);
    });
    if (session.entries.some((entry) => entry.kind === 'visitor')) {
      suggestions.hidden = true;
    }

    function persistEntry(kind, text, status) {
      session.entries.push(status ? { kind, text, status } : { kind, text });
      saveSession(session);
    }

    function trapFocus(event) {
      if (event.key === 'Escape') {
        closePanel();
        return;
      }
      if (event.key !== 'Tab') return;
      const focusable = focusableElements(panel);
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

    function openPanel() {
      panel.hidden = false;
      widget.classList.add('is-open');
      toggle.setAttribute('aria-expanded', 'true');
      panel.addEventListener('keydown', trapFocus);

      if (session.entries.length === 0) {
        addSystemMessage(messages, WELCOME_MESSAGE);
        persistEntry('system', WELCOME_MESSAGE);
      }
      textarea.focus();
    }

    function closePanel() {
      panel.hidden = true;
      widget.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
      panel.removeEventListener('keydown', trapFocus);
      // Le panneau ne s'ouvre que depuis ce bouton : lui rendre le focus est
      // toujours correct, et évite qu'il reste bloqué sur un élément du
      // panneau (désormais masqué) si le focus au moment de l'ouverture
      // n'était pas restaurable (ex. document.body).
      toggle.focus();
    }

    toggle.addEventListener('click', () => {
      if (panel.hidden) openPanel();
      else closePanel();
    });
    close.addEventListener('click', closePanel);

    textarea.addEventListener('input', () => {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 90)}px`;
    });
    textarea.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });

    async function sendMessage(question) {
      if (requestInFlight) return;
      const trimmed = question.trim();
      if (!trimmed) return;

      requestInFlight = true;
      send.disabled = true;
      // Masquer les suggestions peut faire perdre le focus (s'il était sur
      // le bouton cliqué) : on le ramène explicitement sur le champ de
      // saisie pour que le focus reste dans le panneau (piège de focus,
      // touche Échap).
      suggestions.hidden = true;
      addMessage(messages, trimmed, 'visitor');
      persistEntry('visitor', trimmed);
      textarea.value = '';
      textarea.style.height = 'auto';
      textarea.focus();

      const typing = el('div', 'chat-typing');
      typing.append(el('span'), el('span'), el('span'));
      messages.appendChild(typing);
      messages.scrollTop = messages.scrollHeight;

      const wakeHintTimer = window.setTimeout(() => {
        typing.replaceWith(buildSystemMessage(WAKE_HINT_MESSAGE));
        scrollToBottom(messages);
      }, WAKE_HINT_DELAY_MS);

      const controller = new AbortController();
      const abortTimer = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

      try {
        const response = await fetch(`${config.apiBaseUrl || ''}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: trimmed }),
          signal: controller.signal
        });

        window.clearTimeout(wakeHintTimer);
        if (typing.isConnected) typing.remove();

        if (!response.ok) {
          addSystemMessage(messages, NETWORK_FALLBACK_MESSAGE);
          persistEntry('system', NETWORK_FALLBACK_MESSAGE);
        } else {
          const body = await response.json();
          addBotAnswer(messages, body.message, body.status);
          persistEntry('bot', body.message, body.status);
        }
      } catch (error) {
        window.clearTimeout(wakeHintTimer);
        if (typing.isConnected) typing.remove();
        addSystemMessage(messages, NETWORK_FALLBACK_MESSAGE);
        persistEntry('system', NETWORK_FALLBACK_MESSAGE);
      } finally {
        window.clearTimeout(abortTimer);
        requestInFlight = false;
        send.disabled = false;
      }
    }

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      sendMessage(textarea.value);
    });

    suggestions.querySelectorAll('.chat-suggestion').forEach((button) => {
      button.addEventListener('click', () => sendMessage(button.textContent || ''));
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
