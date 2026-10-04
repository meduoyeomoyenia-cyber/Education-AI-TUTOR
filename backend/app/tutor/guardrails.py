"""Guardrails: no invented exam rules, cite source type, NG context, minor safety."""
import re
BANNED = re.compile(r"(waec|neco|jamb).{0,20}(date|timetable|202\d)", re.I)
PROFANITY = re.compile(r"\b(idiot|stupid|dumb)\b", re.I)

def check(question: str, answer: str) -> str:
    if BANNED.search(question) or BANNED.search(answer):
        return "Verify exam dates/rules with your school or the official exam body — I don't invent them."
    return ""

def clean(text: str) -> str:
    return PROFANITY.sub("***", text)

def sources() -> str:
    return "Sources: [curriculum/teacher/AI]. Verify important exam rules officially."
