"""Prompt templates and prompt builders for remembrance generation."""

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class PromptPair:
    """System and user prompts for LLM."""

    system: str
    user: str


ENGLISH_SYSTEM_PROMPT = """You write short, warm remembrances for a family altar (Dia de los Muertos ofrenda). Follow these rules exactly:
- Use ONLY the facts the user provides. Do NOT invent names, relatives, places, dates, jobs, illnesses, or events. If a detail is not given, leave it out.
- Write 120 to 180 words in plain text: 2 or 3 short paragraphs.
- Tone: loving, gentle, celebratory of life, never morbid or dramatic.
- Mention the foods, drinks, songs or objects the user listed, at least two of them if provided, as part of how the person is remembered.
- No headings, no bullet points, no markdown, no emojis, no quotation marks around the whole text.
- Do not mention being an AI. Do not add notes before or after the text.
- Write in English."""

SPANISH_SYSTEM_PROMPT = """Escribes recuerdos breves y calidos para un altar familiar (ofrenda de Dia de Muertos). Sigue estas reglas exactamente:
- Usa SOLO los datos que da la persona. NO inventes nombres, familiares, lugares, fechas, oficios, enfermedades ni sucesos. Si falta un dato, omitelo.
- Escribe entre 120 y 180 palabras en texto plano: 2 o 3 parrafos cortos.
- Tono: carinoso, tierno, que celebre la vida; nunca morboso ni dramatico.
- Menciona al menos dos de las comidas, bebidas, canciones u objetos listados.
- Sin titulos, sin vinetas, sin markdown, sin emojis.
- No menciones que eres una IA. No agregues notas antes ni despues.
- Escribe en espanol."""


def _join_list(items: Optional[List[str]]) -> str:
    if not items:
        return ""
    return ", ".join(items)


def build_prompt(ofrenda: Any) -> PromptPair:
    """Build English or Spanish prompt pair from an ofrenda record or dict."""
    is_spanish = getattr(ofrenda, "language", "en") == "es" if not isinstance(ofrenda, dict) else ofrenda.get("language") == "es"
    system_prompt = SPANISH_SYSTEM_PROMPT if is_spanish else ENGLISH_SYSTEM_PROMPT

    def get_val(key: str, default: Any = None) -> Any:
        return getattr(ofrenda, key, default) if not isinstance(ofrenda, dict) else ofrenda.get(key, default)

    name = get_val("name", "")
    relationship = get_val("relationship")
    birth_year = get_val("birth_year")
    death_year = get_val("death_year")
    foods = _join_list(get_val("foods"))
    drinks = _join_list(get_val("drinks"))
    songs = _join_list(get_val("songs"))
    objects = _join_list(get_val("objects"))
    story_text = (get_val("story_text") or "").strip()
    transcript = (get_val("transcript") or "").strip()

    lines: List[str] = []
    if name:
        lines.append(f"Name: {name}")
    if relationship:
        lines.append(f"Relationship to the writer: {relationship}")
    if birth_year or death_year:
        by = birth_year if birth_year else "?"
        dy = death_year if death_year else "?"
        lines.append(f"Years: {by} to {dy}")
    if foods:
        lines.append(f"Favorite foods: {foods}")
    if drinks:
        lines.append(f"Favorite drinks: {drinks}")
    if songs:
        lines.append(f"Songs they loved: {songs}")
    if objects:
        lines.append(f"Objects that remind us of them: {objects}")

    memories_combined = "\n".join([p for p in (story_text, transcript) if p]).strip()
    if memories_combined:
        lines.append("Stories and memories (from the family):")
        lines.append(memories_combined)
        lines.append("\nWrite the remembrance now.")
    else:
        if is_spanish:
            lines.append("\nNo se proporcionaron anécdotas escritas. Escribe un recuerdo más breve (60 a 90 palabras) basado únicamente en las ofrendas listadas arriba.")
        else:
            lines.append("\nNo written family stories were provided. Write a shorter remembrance (60 to 90 words) from the listed offerings only.")

    user_prompt = "\n".join(lines)
    return PromptPair(system=system_prompt, user=user_prompt)


def build_fallback_remembrance(ofrenda: Any) -> str:
    """Build a respectful template fallback remembrance when Ollama is unavailable."""
    def get_val(key: str, default: Any = None) -> Any:
        return getattr(ofrenda, key, default) if not isinstance(ofrenda, dict) else ofrenda.get(key, default)

    name = get_val("name", "Our loved one")
    relationship = get_val("relationship")
    language = get_val("language", "es")
    foods = get_val("foods") or []
    songs = get_val("songs") or []
    story_text = (get_val("story_text") or "").strip()

    def format_list_en(items: List[str]) -> str:
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return ", ".join(items[:-1]) + f", and {items[-1]}"

    def format_list_es(items: List[str]) -> str:
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} y {items[1]}"
        return ", ".join(items[:-1]) + f" y {items[-1]}"

    snippet = f'"{story_text[:200]}"' if story_text else ""

    if language == "es":
        rel_phrase = f", nuestra {relationship}" if relationship else ""
        foods_phrase = f" Su mesa siempre estuvo llena de {format_list_es(foods)}." if foods else ""
        songs_phrase = f" La música de {format_list_es(songs)} todavía resuena en nuestros corazones." if songs else ""
        story_phrase = f" {snippet}" if snippet else ""
        return f"{name} es recordada con infinito cariño{rel_phrase}.{foods_phrase}{songs_phrase}{story_phrase} Este altar mantiene viva su memoria."
    else:
        rel_phrase = f", our {relationship}" if relationship else ""
        foods_phrase = f" Their table was full of {format_list_en(foods)}." if foods else ""
        songs_phrase = f" The music of {format_list_en(songs)} still plays in our hearts." if songs else ""
        story_phrase = f" {snippet}" if snippet else ""
        return f"{name} is remembered with love{rel_phrase}.{foods_phrase}{songs_phrase}{story_phrase} This altar keeps their memory warm."
