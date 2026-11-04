"""Adaption Labs pipeline (docs.adaptionlabs.ai). Needs: pip install adaption; export ADAPTION_API_KEY=...
Every command prices the job first and only spends credits with --run.
  python scripts/make_dataset.py 2000 > seed.jsonl
  python scripts/adaption_pipeline.py adapt seed.jsonl --run   # polish our ground-truth rows
  python scripts/adaption_pipeline.py invent --rows 1500 --run # or generate from a description
  python scripts/adaption_pipeline.py estimate               # prices 200/1000/2000 rows, shows your balance
  python scripts/adaption_pipeline.py train DATASET_ID         # AutoScientist training run"""
import argparse, sys, time
sys.path.insert(0, ".")
import app  # loads .env
from adaption import Adaption

PROMPT = ("Short, jargon-free electricity-bill tips for Indian households in Gujarat. Each row gives a monthly bill, "
          "billing period, household size, weather (cooling degree-days) and units used, and the answer explains "
          "slab overrun, cooling load or being on track, with exact rupee and unit figures, in a warm tone.")

def wait_import(c, ds):
    while True:
        st = c.datasets.get_status(ds)
        if st.status == "failed": raise SystemExit(f"Import failed: {st.error_data}")
        if st.row_count is not None: return st.row_count
        time.sleep(5)

def main():
    a = argparse.ArgumentParser(); a.add_argument("cmd", choices=["estimate", "adapt", "invent", "train"])
    a.add_argument("arg", nargs="?"); a.add_argument("--rows", type=int, default=1500); a.add_argument("--run", action="store_true"); a.add_argument("--max-credits", type=float)
    a = a.parse_args(); c = Adaption()
    guard = lambda est: est > a.max_credits and sys.exit(f"Estimate {est} is over --max-credits {a.max_credits}; not running.") if a.max_credits else None
    if a.cmd == "estimate":        # price a few sizes before spending anything
        for n in (200, 1000, 2000):
            e = c.datasets.invent(dataset_prompt=PROMPT, rows=n, estimate=True)
            print(f"invent {n} rows: {e.estimated_credits} credits (you have {e.available_credits})")
    elif a.cmd == "adapt":
        ds = c.datasets.upload_file(a.arg).dataset_id; print("rows:", wait_import(c, ds))
        kw = dict(column_mapping={"prompt": "prompt", "completion": "completion"}, job_specification={"max_rows": a.rows})
        est = c.datasets.adapt(ds, estimate=True, **kw).estimated_credits_consumed; print("estimated credits:", est); guard(est)
        if not a.run: return print("dry run; add --run")
        c.datasets.adapt(ds, **kw); st = c.datasets.wait_for_completion(ds, timeout=3600); print(st.status)
        c.datasets.download(ds, file_format="jsonl").write_to_file("adapted.jsonl"); print("saved adapted.jsonl, id", ds)
    elif a.cmd == "invent":
        kw = dict(dataset_prompt=PROMPT, rows=a.rows, name="WattBack tips",
                  language_expansion={"type": "translate", "sample_rate": 0.5, "languages": ["hi", "gu"]})
        est = c.datasets.invent(estimate=True, **kw).estimated_credits; print("estimated credits:", est); guard(est)
        if not a.run: return print("dry run; add --run")
        ds = c.datasets.invent(**kw).id
        while (r := c.datasets.get(ds)).status not in ("succeeded", "failed"): time.sleep(5)
        if r.status == "failed": raise SystemExit(f"failed: {r.error_data}")
        c.datasets.download(ds, file_format="jsonl").write_to_file("invented.jsonl"); print("saved invented.jsonl, id", ds)
    else:
        run = c.autoscientist.create(dataset_id=a.arg); print("run:", run.id, run.status, "(track it in the Adaption app)")

main()
