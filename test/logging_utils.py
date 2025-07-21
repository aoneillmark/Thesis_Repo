# utils/logging_utils.py
from pathlib import Path
import datetime, logging, uuid, csv

class LogManager:
    def __init__(self, root="logs", run_id=None):
        ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        self.run_dir = Path(root) / (run_id or f"run_{ts}_{uuid.uuid4().hex[:6]}")
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # stream *everything* to run.log as well
        fh = logging.FileHandler(self.run_dir / "run.log", encoding="utf-8")
        fh.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
        logging.getLogger().addHandler(fh)

    # e.g. path("evo_gen_0003", "pre") → Path(...)
    def path(self, *segments) -> Path:
        p = self.run_dir.joinpath(*segments)
        p.mkdir(parents=True, exist_ok=True)
        return p

    # light helper for appending one CSV row
    def write_row(self, rel_path, row):
        parts  = rel_path.split("/")
        fpath  = self.path(*parts[:-1]) / parts[-1]   # <─ FIX
        first  = not fpath.exists()
        with open(fpath, "a", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            if first:
                writer.writerow(row.keys())
            writer.writerow(row.values())