"""Tests for the arbiter debate memory system."""

import uuid
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.debate_record import DebateRecord
from app.debate.debate_memory import DebateMemory


# ─── DebateRecord Tests ─────────────────────────────────────────────────────────

class TestDebateRecord:

    def test_from_db_constructs_correctly(self):
        """DebateRecord.from_db produces correct fields from a DebateHistory row."""
        mock_row = MagicMock()
        mock_row.hypothesis_id = uuid.uuid4()
        mock_row.verdict = "FAIL"
        mock_row.rejection_reason = "Method sketch is infeasible on 8GB GPU"
        mock_row.objections = ["Compute exceeds 8GB", "No baseline comparison"]
        mock_row.rebuttals = ["Proposed gradient checkpointing"]
        mock_row.surviving_risks = ["Memory overflow"]
        mock_row.arbiter_notes = "Strong idea but compute concern unresolved"
        mock_row.final_novelty_score = 0.7
        mock_row.final_feasibility_score = 0.3
        mock_row.addressed_prior_objections = []
        mock_row.created_at = datetime.now(UTC)

        record = DebateRecord.from_db(
            mock_row,
            hypothesis_title="Curriculum LoRA for Atari",
            core_claim="LoRA fine-tuning improves sample efficiency",
        )

        assert record.hypothesis_id == str(mock_row.hypothesis_id)
        assert record.hypothesis_title == "Curriculum LoRA for Atari"
        assert record.verdict == "FAIL"
        assert len(record.objections) == 2
        assert record.objections[0] == "Compute exceeds 8GB"
        assert record.rejection_reason == "Method sketch is infeasible on 8GB GPU"

    def test_from_db_handles_none_fields(self):
        """Missing JSONB fields default to empty lists."""
        mock_row = MagicMock()
        mock_row.hypothesis_id = uuid.uuid4()
        mock_row.verdict = "PASS"
        mock_row.rejection_reason = None
        mock_row.objections = None
        mock_row.rebuttals = None
        mock_row.surviving_risks = None
        mock_row.arbiter_notes = None
        mock_row.final_novelty_score = 0.8
        mock_row.final_feasibility_score = 0.9
        mock_row.addressed_prior_objections = None
        mock_row.created_at = datetime.now(UTC)

        record = DebateRecord.from_db(mock_row, "Title", "Claim")

        assert record.objections == []
        assert record.rebuttals == []
        assert record.surviving_risks == []
        assert record.addressed_prior_objections == []

    def test_to_dict_round_trips(self):
        """to_dict produces a serializable dictionary."""
        record = DebateRecord(
            hypothesis_id="abc-123",
            hypothesis_title="Test",
            core_claim="Claim",
            objections=["obj1"],
            rebuttals=["reb1"],
            verdict="FAIL",
            rejection_reason="reason",
            arbiter_notes="notes",
            surviving_risks=["risk1"],
            novelty_score=0.5,
            feasibility_score=0.6,
            addressed_prior_objections=[],
        )
        d = record.to_dict()
        assert d["verdict"] == "FAIL"
        assert d["objections"] == ["obj1"]
        assert isinstance(d, dict)


# ─── DebateMemory.format_history_block Tests ─────────────────────────────────

class TestFormatHistoryBlock:

    def test_empty_records_returns_empty_string(self):
        memory = DebateMemory()
        assert memory.format_history_block([]) == ""

    def test_single_ancestor_formats_correctly(self):
        record = DebateRecord(
            hypothesis_id="parent-1",
            hypothesis_title="Curriculum LoRA for Atari",
            core_claim="LoRA improves sample efficiency",
            objections=["Compute exceeds 8GB", "No baseline comparison"],
            rebuttals=["Proposed gradient checkpointing"],
            verdict="FAIL",
            rejection_reason="Unresolved compute feasibility",
            arbiter_notes="Strong idea but compute concern unresolved",
            surviving_risks=["Memory overflow"],
            novelty_score=0.7,
            feasibility_score=0.3,
            addressed_prior_objections=[],
        )
        memory = DebateMemory()
        block = memory.format_history_block([record])

        assert 'Parent: "Curriculum LoRA for Atari" (FAIL)' in block
        assert "Compute exceeds 8GB; No baseline comparison" in block
        assert "Rejection reason: Unresolved compute feasibility" in block

    def test_multiple_ancestors_numbered_correctly(self):
        records = [
            DebateRecord(
                hypothesis_id=f"hyp-{i}",
                hypothesis_title=f"Hypothesis {i}",
                core_claim=f"Claim {i}",
                objections=[f"Objection {i}"],
                rebuttals=[],
                verdict="FAIL",
                rejection_reason=f"Reason {i}",
                arbiter_notes=None,
                surviving_risks=[],
                novelty_score=0.5,
                feasibility_score=0.5,
                addressed_prior_objections=[],
            )
            for i in range(3)
        ]
        memory = DebateMemory()
        block = memory.format_history_block(records)

        assert "1. Parent:" in block
        assert "2. Ancestor-2:" in block
        assert "3. Ancestor-3:" in block

    def test_addressed_prior_objections_shown(self):
        record = DebateRecord(
            hypothesis_id="child-1",
            hypothesis_title="Improved LoRA v2",
            core_claim="Fixed compute issue",
            objections=[],
            rebuttals=[],
            verdict="PASS",
            rejection_reason=None,
            arbiter_notes=None,
            surviving_risks=[],
            novelty_score=0.8,
            feasibility_score=0.9,
            addressed_prior_objections=["Compute budget now fits 8GB"],
        )
        memory = DebateMemory()
        block = memory.format_history_block([record])

        assert "Addressed from prior: Compute budget now fits 8GB" in block


# ─── ArbiterResponseSchema Tests ────────────────────────────────────────────

class TestArbiterResponseSchema:

    def test_new_fields_default_empty(self):
        from app.debate.agents import ArbiterResponseSchema

        schema = ArbiterResponseSchema()
        assert schema.key_objections == []
        assert schema.addressed_prior_objections == []

    def test_new_fields_populated(self):
        from app.debate.agents import ArbiterResponseSchema

        schema = ArbiterResponseSchema(
            verdict="FAIL",
            key_objections=["Compute infeasible", "No novelty"],
            addressed_prior_objections=["Fixed baseline comparison"],
        )
        assert len(schema.key_objections) == 2
        assert schema.addressed_prior_objections == ["Fixed baseline comparison"]

    def test_model_dump_includes_new_fields(self):
        from app.debate.agents import ArbiterResponseSchema

        schema = ArbiterResponseSchema(
            key_objections=["obj1"],
            addressed_prior_objections=["addr1"],
        )
        d = schema.model_dump()
        assert "key_objections" in d
        assert "addressed_prior_objections" in d
