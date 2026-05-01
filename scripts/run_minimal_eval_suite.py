from __future__ import annotations

import argparse
import json

from app.evals import MinimalEvalSuite


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the minimal demo eval suite")
    parser.add_argument("--case-id", required=True)
    args = parser.parse_args()
    result = MinimalEvalSuite().run(case_id=args.case_id)
    print(json.dumps(result.summary.model_dump(mode="json"), ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
