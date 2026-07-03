# -*- coding: utf-8
import json
import unittest
from pathlib import Path

from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_full, fx_job_op_full
from data_pc_origin.o9_facade import update_from_dataframe
from data_pc_origin.p0_types import Stage2Artifacts, WorkflowOptions
from data_pc_origin.p1_payload import assemble_stage2_metadata
from data_pc_origin.p5_workflow import Stage2RunResult
from data_pc_origin.p7_mail_hook import MailAttachmentError, MailJob, run_mail_workflow
from data_pc_origin.tests._helpers import WORKFLOW_TEST_ENV


def _fx_stage2(_path: str) -> Stage2RunResult:
    from data_pc_origin.p1_payload import Stage2Metadata

    art = Stage2Artifacts(fx_job_df_full(), r"G:\calc.xlsx")
    meta = assemble_stage2_metadata(
        sample_name=SAMPLE_JOB,
        identity_key=("20250601", "seed"),
        saved_excel=r"G:\calc.xlsx",
    )
    return Stage2RunResult(artifacts=art, metadata=meta)


class TestP7MailHook(unittest.TestCase):
    def test_reject_pdf(self) -> None:
        from data_pc_origin.p7_mail_hook import parse_mail_attachment

        job = MailJob(attachment_path=r"G:\a.pdf")
        with self.assertRaises(MailAttachmentError):
            parse_mail_attachment(job)

    def test_write_p7_smoke_artifact(self) -> None:
        job = MailJob(
            attachment_path=r"G:\mail\KCH_20250601.xlsx",
            subject="gc_automation",
        )

        def origin(payload):
            op, _ = fx_job_op_full()
            return update_from_dataframe(
                payload.opju_path,
                payload.df,
                payload.sample_name,
                save_in_place=payload.save_in_place,
                identity_key=payload.identity_key,
                op=op,
                skip_gate=True,
                printer=lambda _m: None,
                log_fn=lambda _m: None,
            )

        res = run_mail_workflow(
            job,
            WorkflowOptions(opju_path=OPJU_FX),
            stage2_runner=_fx_stage2,
            origin_runner=origin,
            explicit_skip=False,
            environ=WORKFLOW_TEST_ENV,
        )
        out = {
            "mail_xlsx": job.attachment_path,
            "workflow_ok": res.ok,
            "sheets_updated": (
                res.stage4.origin.sheets_updated
                if res.stage4 and res.stage4.origin
                else 0
            ),
        }
        path = Path(__file__).resolve().parents[1] / "p7_mail_smoke.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        self.assertTrue(out["workflow_ok"])
        self.assertEqual(out["sheets_updated"], 8)


if __name__ == "__main__":
    unittest.main()
