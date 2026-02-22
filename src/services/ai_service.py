from __future__ import annotations

import json
from typing import Callable

from groq import APIStatusError, AsyncGroq

from src.models.schemas import AnalysisResult, CategoryRule, NoteFile


class AIService:
    def __init__(self, api_key: str) -> None:
        self._client = AsyncGroq(api_key=api_key)

    async def close(self) -> None:
        await self._client.close()

    async def analyze_batch(
        self,
        notes: list[NoteFile],
        base_prompt: str,
        categories: list[CategoryRule],
        on_progress: Callable[[int, int], None] | None = None,
    ) -> list[AnalysisResult]:
        results: list[AnalysisResult] = []
        total = len(notes)

        for index, note in enumerate(notes, start=1):
            if on_progress is not None:
                on_progress(index, total)
            result = await self.analyze_note(note=note, base_prompt=base_prompt, categories=categories)
            results.append(result)

        return results

    async def generate_summary(self, combined_text: str) -> str:
        system_instruction = "Você é um assistente de produtividade."
        user_prompt = (
            "Faça um resumo executivo em tópicos do meu dia com base nestas anotações:\n\n"
            f"{combined_text}"
        )

        response = await self._client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )

        content = response.choices[0].message.content if response.choices else ""
        summary = (content or "").strip()
        if not summary:
            raise ValueError("A IA não retornou um resumo válido.")
        return summary

    async def analyze_note(
        self,
        note: NoteFile,
        base_prompt: str,
        categories: list[CategoryRule],
    ) -> AnalysisResult:
        categories_text = "\n".join(
            f"- {category.name}: {category.instruction}" for category in categories
        )
        system_instruction = (
            "Você analisa notas e responde exclusivamente em JSON válido. "
            "Formato obrigatório: {\"category\":\"...\",\"destination\":\"...\",\"justification\":\"...\"}."
        )
        user_prompt = (
            f"{base_prompt}\n\n"
            f"Categorias possíveis:\n{categories_text}\n\n"
            f"Nome do arquivo: {note.file_name}\n"
            f"Conteúdo da nota:\n{note.content}\n"
        )

        try:
            response = await self._client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            content = response.choices[0].message.content if response.choices else ""
            parsed = self._parse_json_response(content or "")
            return AnalysisResult(
                file_name=note.file_name,
                category=str(parsed.get("category", "Sem categoria")),
                destination=str(parsed.get("destination", "Sem destino")),
                justification=str(parsed.get("justification", "Sem justificativa")),
            )
        except APIStatusError as api_error:
            return AnalysisResult(
                file_name=note.file_name,
                category="Erro",
                destination="-",
                justification="Falha na chamada à API.",
                error=self._map_api_error(api_error),
            )
        except (json.JSONDecodeError, ValueError):
            return AnalysisResult(
                file_name=note.file_name,
                category="Erro",
                destination="-",
                justification="Falha ao interpretar resposta da IA.",
                error="A IA retornou um formato inválido.",
            )
        except Exception as error:
            return AnalysisResult(
                file_name=note.file_name,
                category="Erro",
                destination="-",
                justification="Erro inesperado durante a análise.",
                error=str(error),
            )

    @staticmethod
    def _parse_json_response(raw_text: str) -> dict[str, str]:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("Resposta da IA não é um objeto JSON")
        return parsed

    @staticmethod
    def _map_api_error(api_error: APIStatusError) -> str:
        status_code = int(getattr(api_error, "status_code", 0) or 0)
        if status_code in (401, 403):
            return "API Key inválida ou sem permissão."
        if status_code == 429:
            return "Limite de requisições excedido. Tente novamente em alguns minutos."
        if status_code >= 500:
            return "Erro temporário do servidor da API."
        return str(api_error) or "Erro desconhecido na API."
