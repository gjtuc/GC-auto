# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path

from data_pc_origin.o2_env import SKIP_ORIGIN_ENV
from data_pc_origin.p0_types import WorkflowOptions
from data_pc_origin.p3_skip import (
    resolve_skip_stage4,
    should_execute_stage4,
    stage4_skip_reason,
)


class TestP3Skip(unittest.TestCase):
    def test_env_skip(self) -> None:
        self.assertTrue(resolve_skip_stage4(environ={SKIP_ORIGIN_ENV: "1"}))

    def test_explicit_override(self) -> None:
        self.assertFalse(
            resolve_skip_stage4(explicit=False, environ={SKIP_ORIGIN_ENV: "yes"})
        )

    def test_options_skip_stage4(self) -> None:
        self.assertFalse(
            should_execute_stage4(
                options=WorkflowOptions(skip_stage4=True),
                explicit=False,
                environ={},
            )
        )

    def test_write_p3_smoke_artifact(self) -> None:
        out = {
            "env_skip": resolve_skip_stage4(environ={SKIP_ORIGIN_ENV: "1"}),
            "blocked_by_env_only": should_execute_stage4(
                environ={SKIP_ORIGIN_ENV: "1"}
            ),
            "explicit_false_overrides_env": should_execute_stage4(
                explicit=False, environ={SKIP_ORIGIN_ENV: "1"}
            ),
            "reason_when_skip": stage4_skip_reason(explicit=True),
            "reason_when_run": stage4_skip_reason(explicit=False, environ={}),
        }
        path = Path(__file__).resolve().parents[1] / "p3_skip_smoke.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        self.assertTrue(out["env_skip"])
        self.assertFalse(out["blocked_by_env_only"])
        self.assertTrue(out["explicit_false_overrides_env"])
        self.assertIn("Origin", out["reason_when_skip"])
        self.assertEqual(out["reason_when_run"], "")


if __name__ == "__main__":
    unittest.main()
