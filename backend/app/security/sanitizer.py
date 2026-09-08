"""Validation et détection de détournement pour les messages du chatbot.

Deux responsabilités distinctes, cf. 12-specifications-techniques-chatbot-ia.md §8 :

- ``validate_message`` rejette une entrée structurellement invalide (vide, trop
  longue, caractères de contrôle) avant tout appel à un fournisseur — une
  requête malformée ne doit rien coûter.
- ``detect_prompt_injection`` repère une tentative de détournement, par
  heuristique. Elle ne bloque jamais la requête à elle seule : le comportement
  attendu (cf. spécifications fonctionnelles §3) est de traiter la question
  comme hors périmètre, tout en journalisant la tentative pour suivi.
"""

import re

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

# Heuristique volontairement large : elle ne remplace pas les défenses
# structurelles (message jamais concaténé aux instructions système, modèle
# sans outil ni accès réseau), elle s'y ajoute pour la journalisation et le
# court-circuit vers la réponse hors périmètre.
_INJECTION_PATTERNS = re.compile(
    r"ignore(?:z|r)?\s+(?:toutes?\s+)?(?:les\s+|ces\s+|tes\s+)?"
    r"(?:instructions?|consignes?|r[eè]gles?|directives?)"
    r"|ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions"
    r"|disregard\s+(?:the\s+)?(?:above|previous|prior)"
    r"|oublie(?:z)?\s+(?:tes\s+|les\s+|ces\s+)?"
    r"(?:instructions?|consignes?|r[eè]gles?)"
    r"|nouvelles?\s+instructions?"
    r"|tu\s+es\s+maintenant"
    r"|you\s+are\s+now"
    r"|prompt\s+syst[eè]me"
    r"|system\s+prompt"
    r"|r[eé]v[eè]le(?:z)?\s+(?:tes|vos|ton|votre)\s+(?:instructions?|consignes?)"
    r"|quelles?\s+sont\s+tes\s+instructions?"
    r"|sans\s+(?:aucune\s+)?(?:restriction|limite|filtre)"
    r"|r[eé]ponds?\s+sans\s+filtre"
    r"|mode\s+(?:d[eé]veloppeur|sans\s+restriction)"
    r"|developer\s+mode"
    r"|jailbreak"
    r"|\bDAN\b"
    r"|pretend\s+(?:to\s+be|you\s+are)"
    r"|act\s+as\s+(?:if|a|an)",
    re.IGNORECASE,
)


class InvalidMessageError(ValueError):
    """Message rejeté avant tout appel à un fournisseur externe."""


def validate_message(message: str, max_length: int) -> str:
    """Nettoie et valide un message de visiteur.

    Lève ``InvalidMessageError`` si le message est vide, trop long, ou
    contient des caractères de contrôle.
    """
    stripped = message.strip()
    if not stripped:
        raise InvalidMessageError("Le message ne peut pas être vide.")
    if len(stripped) > max_length:
        raise InvalidMessageError(f"Le message dépasse {max_length} caractères.")
    if _CONTROL_CHARS.search(stripped):
        raise InvalidMessageError("Caractères de contrôle non autorisés.")
    return stripped


def detect_prompt_injection(message: str) -> bool:
    """Repère, par heuristique, une tentative de détournement des consignes."""
    return bool(_INJECTION_PATTERNS.search(message))
