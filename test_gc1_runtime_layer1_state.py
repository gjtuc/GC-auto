# -*- coding: utf-8 -*-
"""T23 — gc1_runtime.layer1_state roundtrip·STW 테스트."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from gc1_runtime.layer1_state import (
    AtomRecord,
    AtomStatus,
    JobPaths,
    JobState,
    StateStore,
)

ROOT = Path(__file__).resolve().parent
EXAMPLE_JSON = ROOT / "deploy" / "gc_autochro_job.example.json"


class TestAtomRecord(unittest.TestCase):
    def test_seven_fields_roundtrip_dict(self):
        rec = AtomRecord(
            status=AtomStatus.RUNNING,
            attempt=2,
            channel_used="H",
            fail_code=None,
            probe_snapshot={"tree_line": "x"},
            started_at="2026-06-30T10:00:00+09:00",
            ended_at=None,
        )
        back = AtomRecord.from_dict(rec.to_dict())
        self.assertEqual(back.status, AtomStatus.RUNNING)
        self.assertEqual(back.attempt, 2)
        self.assertEqual(back.channel_used, "H")
        self.assertEqual(back.probe_snapshot, {"tree_line": "x"})

    def test_invalid_status_defaults_pending(self):
        rec = AtomRecord.from_dict({"status": "unknown"})
        self.assertEqual(rec.status, AtomStatus.PENDING)


class TestJobStateRoundtrip(unittest.TestCase):
    def test_example_json_load_save_reload(self):
        self.assertTrue(EXAMPLE_JSON.is_file(), f"missing {EXAMPLE_JSON}")
        raw = json.loads(EXAMPLE_JSON.read_text(encoding="utf-8"))
        state = JobState.from_dict(raw)
        self.assertEqual(state.job_id, raw["job_id"])
        self.assertEqual(state.atoms["Ω.A.L4.P0.01"].status, AtomStatus.OK)
        self.assertEqual(state.atoms["Ω.A.L4.P4.03"].status, AtomStatus.RUNNING)
        self.assertIsNone(state.atoms["Ω.A.L4.P9.14"].channel_used)

        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(JobPaths(tmp))
            store.save(state)
            path = store.paths.job_json
            self.assertTrue(os.path.isfile(path))
            reloaded = store.load()
            self.assertEqual(reloaded.to_dict(), state.to_dict())

    def test_new_job_pending_atoms(self):
        ids = ("Ω.A.L4.P0.01", "Ω.A.L4.P1.01")
        job = JobState.new_job(atom_ids=ids, data_name="test")
        self.assertTrue(job.job_id)
        self.assertTrue(job.started_at)
        for aid in ids:
            self.assertEqual(job.atoms[aid].status, AtomStatus.PENDING)

    def test_corrupt_json_returns_empty_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, ".gc_autochro_job.json")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("{not json")
            store = StateStore(JobPaths(tmp))
            state = store.load()
            self.assertEqual(state.job_id, "")
            self.assertEqual(state.atoms, {})


class TestStateStoreStw(unittest.TestCase):
    def test_stw_atom_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(JobPaths(tmp))
            job = JobState.new_job(atom_ids=("Ω.A.L4.P2.03",))
            store.save(job)
            store.stw_atom(
                job,
                "Ω.A.L4.P2.03",
                status=AtomStatus.FAIL,
                attempt=3,
                channel_used="H",
                fail_code="E_P2_FOCUS",
                probe_snapshot={"x": 1},
                started_at="t0",
                ended_at="t1",
            )
            loaded = store.load()
            rec = loaded.atoms["Ω.A.L4.P2.03"]
            self.assertEqual(rec.status, AtomStatus.FAIL)
            self.assertEqual(rec.fail_code, "E_P2_FOCUS")
            self.assertEqual(loaded.atom_current, "Ω.A.L4.P2.03")


if __name__ == "__main__":
    unittest.main()
