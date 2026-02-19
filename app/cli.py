from __future__ import annotations

import argparse
import json

from app.core.settings import get_settings
from app.services.audit_logger import AuditLogger
from app.services.pipeline_service import PipelineService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="secure-xl2hwp",
        description="Local secure Excel extraction/cleanup to Hancom payload pipeline",
    )
    parser.add_argument("--input", required=True, help="Input excel file path")
    parser.add_argument("--output-dir", default="examples/output", help="Output artifact directory")
    parser.add_argument("--contract", default="default", help="Contract name under specs/contracts")
    parser.add_argument("--profile", default="default", help="Profile name under specs/profiles")
    parser.add_argument("--template-name", default="default", help="Template profile under specs/templates")
    parser.add_argument("--template-path", default="", help="Optional template file path (.hwpx/.txt)")
    parser.add_argument("--actor-user", default="cli-user", help="Actor id for audit logs")
    parser.add_argument("--actor-role", default="CLI", help="Actor role for audit logs")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings()
    audit_logger = AuditLogger(audit_log_dir=settings.audit_log_dir)
    service = PipelineService(settings=settings, audit_logger=audit_logger)
    outcome = service.process(
        input_path=args.input,
        output_dir=args.output_dir,
        contract_name=args.contract,
        profile_name=args.profile,
        template_name=args.template_name,
        template_path=args.template_path or None,
        actor={"user_id": args.actor_user, "role": args.actor_role},
        request_id="cli-run",
    )
    print(json.dumps(outcome.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
