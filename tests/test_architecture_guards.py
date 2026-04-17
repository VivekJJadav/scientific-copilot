import importlib
from types import SimpleNamespace

import pytest
from pydantic import ValidationError


def test_research_atom_factory_populates_extracted_fields():
    from app.core.atoms import ResearchAtom

    paper = SimpleNamespace(
        arxiv_id="1234.5678",
        title="Factory Test",
        abstract="Abstract",
        authors=[{"name": "Author"}],
        published_year=2026,
        pdf_url="https://example.com/paper.pdf",
        methods=["LoRA"],
        limitations=["Small sample"],
        claims=["Improves accuracy"],
        embedding=None,
        arxiv_status="processed",
    )

    atom = ResearchAtom.from_paper(paper)

    assert atom.methods == ["LoRA"]
    assert atom.limitations == ["Small sample"]
    assert atom.claims == ["Improves accuracy"]


def test_research_atom_reconstruction_only_exists_for_non_paper_sources():
    import pathlib

    app_root = pathlib.Path("/Users/vicky/Desktop/scientific-copilot/app")
    matches = []
    for path in app_root.rglob("*.py"):
        text = path.read_text()
        if "ResearchAtom(" in text:
            matches.append(path.name)

    assert matches == ["arxiv_client.py"]


def test_embedder_uses_single_module_level_model_instance():
    embedder_module = importlib.import_module("app.extraction.embedder")

    first = embedder_module.get_embedder()
    second = embedder_module.get_embedder()

    assert first is second
    assert first._get_model() is embedder_module.EMBEDDING_MODEL
    assert second._get_model() is embedder_module.EMBEDDING_MODEL


def test_task_store_exposes_progress():
    from app.api.routes.tasks import create_task, update_task_status, _task_store

    task_id = create_task()
    update_task_status(task_id, "running", progress=40, message="Halfway")

    assert _task_store[task_id]["progress"] == 40
    assert _task_store[task_id]["message"] == "Halfway"


def test_gap_extraction_response_uses_pydantic_validation():
    from app.reasoning.gap_extractor import GapExtractionResponseSchema

    with pytest.raises(ValidationError):
        GapExtractionResponseSchema.model_validate_json('{"gaps": [')


def test_dataset_extraction_response_uses_pydantic_validation():
    from app.clustering.dataset_extractor import DatasetExtractionResponseSchema

    with pytest.raises(ValidationError):
        DatasetExtractionResponseSchema.model_validate_json('{"datasets": [')
