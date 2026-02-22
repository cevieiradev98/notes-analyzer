from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class NoteFile:
    file_name: str
    file_path: str
    modified_at: datetime
    content: str


@dataclass(slots=True)
class AnalysisResult:
    file_name: str
    category: str
    destination: str
    justification: str
    error: str | None = None


@dataclass(slots=True)
class CategoryRule:
    name: str
    instruction: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "instruction": self.instruction,
        }


@dataclass(slots=True)
class AppConfig:
    api_key: str = ""
    notes_directory: str = ""
    notes_source: str = "local"
    base_prompt: str = (
        "Você é um assistente de organização. Leia a nota e classifique-a em uma categoria "
        "adequada, sugerindo onde ela deve ser guardada."
    )
    categories: list[CategoryRule] = field(
        default_factory=lambda: [
            CategoryRule(name="Trabalho", instruction="Assuntos profissionais, projetos e tarefas de trabalho."),
            CategoryRule(name="Pessoal", instruction="Compromissos pessoais, família, rotina e vida privada."),
            CategoryRule(name="Estudos", instruction="Aprendizado, cursos, resumos e conteúdos de estudo."),
            CategoryRule(name="Diversos", instruction="Itens que não se enquadram claramente nas categorias anteriores."),
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_key": self.api_key,
            "notes_directory": self.notes_directory,
            "notes_source": self.notes_source,
            "base_prompt": self.base_prompt,
            "categories": [category.to_dict() for category in self.categories],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        categories_raw = data.get("categories", cls().categories)
        categories: list[CategoryRule] = []
        if isinstance(categories_raw, list):
            for item in categories_raw:
                if isinstance(item, dict):
                    name = str(item.get("name", "")).strip()
                    instruction = str(item.get("instruction", "")).strip()
                    if name and instruction:
                        categories.append(CategoryRule(name=name, instruction=instruction))
                else:
                    name = str(item).strip()
                    if name:
                        categories.append(
                            CategoryRule(
                                name=name,
                                instruction="Sem regra específica informada.",
                            )
                        )

        return cls(
            api_key=str(data.get("api_key", "")),
            notes_directory=str(data.get("notes_directory", "")),
            notes_source=str(data.get("notes_source", "local")),
            base_prompt=str(data.get("base_prompt", cls().base_prompt)),
            categories=categories or cls().categories,
        )
