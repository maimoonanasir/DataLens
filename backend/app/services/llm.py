"""LLM integration using Groq API — SQL-extraction approach (no tool calling)."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from backend.app.models.dataset import ColumnProfile
from backend.app.services.query_engine import execute_raw_sql, get_column_unique_values

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env", override=True)

MODEL = "llama-3.3-70b-versatile"
MAX_ROUNDS = 4


def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")
    return Groq(api_key=api_key)


def _table(dataset_id: str) -> str:
    from backend.app.database import data_table_name
    return data_table_name(dataset_id)


def _extract_sql(text: str) -> str | None:
    for pattern in [r"<sql>(.*?)</sql>", r"```sql(.*?)```", r"```(.*?)```"]:
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def chat_with_data(
    dataset_id: str,
    messages: list[dict[str, Any]],
    filters: dict[str, Any],
    profiles: list[ColumnProfile],
) -> tuple[str, list[str]]:
    client = _get_client()
    table = _table(dataset_id)
    columns = [p.name for p in profiles]
    col_list = ", ".join(f'"{c}"' for c in columns)

    system_prompt = (
        f"You are DataLens AI, an expert data analyst. "
        f"You have access to a SQLite table called `{table}` with columns: {col_list}.\n"
        "To query data, output a SQL SELECT statement wrapped in <sql></sql> tags. "
        "Use double quotes for column names with spaces. "
        "After seeing query results, give a concise business-focused answer (2-4 sentences) with specific numbers. "
        f"Active filters: {json.dumps(filters) if filters else 'none'}."
    )

    api_messages = [{"role": "system", "content": system_prompt}]
    for m in messages:
        api_messages.append({"role": m["role"], "content": m["content"]})

    tools_used: list[str] = []

    for _round in range(MAX_ROUNDS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=api_messages,
            max_tokens=1024,
        )
        reply = response.choices[0].message.content or ""

        sql = _extract_sql(reply)
        if not sql:
            clean = re.sub(r"<sql>.*?</sql>", "", reply, flags=re.DOTALL).strip()
            return clean or "I could not generate a response.", tools_used

        tools_used.append("query_data")
        try:
            rows = execute_raw_sql(dataset_id, sql)
            result_text = json.dumps(rows[:200], default=str)
        except Exception as exc:
            result_text = f"SQL error: {exc}"

        api_messages.append({"role": "assistant", "content": reply})
        api_messages.append({
            "role": "user",
            "content": f"Query results: {result_text}\n\nNow answer the original question using these results.",
        })

    return "I reached my analysis limit. Please try a more specific question.", tools_used


def generate_summary(
    dataset_id: str,
    profiles: list[ColumnProfile],
    chart_data_summary: str,
) -> str:
    client = _get_client()
    profile_text = _build_profile_context(profiles)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior business analyst writing an executive summary. "
                    "Write in clear, professional business English in flowing paragraphs. "
                    "No bullet points. Reference specific numbers and patterns. "
                    "Highlight 3-5 actionable insights in 4-6 paragraphs."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Dataset Profile:\n{profile_text}\n\n"
                    f"Key Chart Findings:\n{chart_data_summary}\n\n"
                    "Write an executive summary highlighting key patterns and actionable insights."
                ),
            },
        ],
        max_tokens=1500,
    )
    return response.choices[0].message.content or "Unable to generate summary."


def _build_profile_context(profiles: list[ColumnProfile]) -> str:
    lines: list[str] = []
    for p in profiles:
        stat_str = ""
        if p.dtype == "numeric":
            stat_str = f"min={p.stats.get('min')}, max={p.stats.get('max')}, mean={p.stats.get('mean')}"
        elif p.dtype == "datetime":
            stat_str = f"from {p.stats.get('min')} to {p.stats.get('max')}"
        elif p.dtype == "categorical":
            top = p.stats.get("top_values", [])[:3]
            stat_str = "top values: " + ", ".join(f"{t['value']} ({t['count']})" for t in top)
        lines.append(f"- {p.name} ({p.dtype}): {p.unique_count} unique, {p.null_pct}% missing. {stat_str}")
    return "\n".join(lines)
