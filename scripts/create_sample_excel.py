from pathlib import Path

import pandas as pd


def main() -> None:
    rows = [
        {
            "Project ID": "PJT-2026-001",
            "Project Name": "로컬 보안 자동화 구축",
            "Owner": "홍길동",
            "Budget": 180000000,
            "Progress": 35,
            "State": "진행중",
            "Report Date": "2026-02-19",
            "비고": "우선순위 상",
        },
        {
            "Project ID": "PJT-2026-002",
            "Project Name": "엑셀 정제 파이프라인",
            "Owner": "김영희",
            "Budget": 95000000,
            "Progress": 88,
            "State": "진행중",
            "Report Date": "2026-02-19",
            "비고": "리스크 낮음",
        },
    ]

    df = pd.DataFrame(rows)
    out_path = Path("examples/input/sample_projects.xlsx")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(out_path, index=False)
    print(f"sample excel written: {out_path}")


if __name__ == "__main__":
    main()
