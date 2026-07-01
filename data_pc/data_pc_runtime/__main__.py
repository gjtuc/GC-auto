"""data_pc_runtime CLI: python -m data_pc_runtime [--ensure-once]"""
from data_pc_runtime.layer4_supervisor import cli_main

if __name__ == "__main__":
    raise SystemExit(cli_main())
