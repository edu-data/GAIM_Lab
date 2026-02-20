"""
GAIM Lab v7.0 — SQLite Data Persistence Layer

분석 결과를 SQLite DB에 저장하고 이력·성장 데이터를 조회하는 Repository.
DB 파일: data/gaim_lab.db (자동 생성)
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# DB 파일 기본 경로
_DB_DIR = Path(__file__).resolve().parent.parent / "data"
_DB_PATH = _DB_DIR / "gaim_lab.db"

# ============================================================
# Schema
# ============================================================
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS analyses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id     TEXT UNIQUE,
    video_path      TEXT NOT NULL,
    video_name      TEXT NOT NULL,
    analyzed_at     TEXT NOT NULL,
    elapsed_seconds REAL DEFAULT 0,
    total_score     REAL DEFAULT 0,
    grade           TEXT DEFAULT '',
    confidence      REAL DEFAULT 0,
    version         TEXT DEFAULT '7.0',
    preset          TEXT DEFAULT 'default',
    result_json     TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS dimension_scores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    name        TEXT NOT NULL,
    score       REAL NOT NULL,
    max_score   REAL NOT NULL,
    percentage  REAL NOT NULL,
    grade       TEXT DEFAULT '',
    confidence  REAL DEFAULT 1.0,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_analyses_video_name ON analyses(video_name);
CREATE INDEX IF NOT EXISTS idx_analyses_analyzed_at ON analyses(analyzed_at);
CREATE INDEX IF NOT EXISTS idx_dim_analysis_id ON dimension_scores(analysis_id);
"""


class AnalysisRepository:
    """분석 결과 CRUD Repository (SQLite)"""

    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else _DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    # ----------------------------------------------------------
    # DB Lifecycle
    # ----------------------------------------------------------

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_db(self):
        """Create tables if not exist"""
        with self._conn() as conn:
            conn.executescript(_SCHEMA_SQL)

    # ----------------------------------------------------------
    # Write
    # ----------------------------------------------------------

    def save_result(
        self,
        video_path: str,
        pipeline_id: str,
        result: Dict,
        pedagogy: Dict = None,
        elapsed_seconds: float = 0.0,
    ) -> int:
        """Save a pipeline result to DB. Returns analysis row id."""
        ped = pedagogy or {}
        total_score = ped.get("total_score", 0)
        grade = ped.get("grade", "")
        confidence = ped.get("confidence", {}).get("overall", 0)
        version = ped.get("version", "7.0")
        preset = ped.get("preset_used", "default")
        video_name = Path(video_path).stem

        with self._conn() as conn:
            cur = conn.execute(
                """INSERT OR REPLACE INTO analyses
                   (pipeline_id, video_path, video_name, analyzed_at,
                    elapsed_seconds, total_score, grade, confidence,
                    version, preset, result_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    pipeline_id,
                    str(video_path),
                    video_name,
                    datetime.now().isoformat(),
                    elapsed_seconds,
                    total_score,
                    grade,
                    confidence,
                    version,
                    preset,
                    json.dumps(result, ensure_ascii=False, default=str),
                ),
            )
            analysis_id = cur.lastrowid

            # Save dimension scores
            dimensions = ped.get("dimensions", [])
            for d in dimensions:
                conn.execute(
                    """INSERT INTO dimension_scores
                       (analysis_id, name, score, max_score, percentage, grade, confidence)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        analysis_id,
                        d.get("name", ""),
                        d.get("score", 0),
                        d.get("max_score", 0),
                        d.get("percentage", 0),
                        d.get("grade", ""),
                        d.get("confidence", 1.0),
                    ),
                )
            conn.commit()
        return analysis_id

    # ----------------------------------------------------------
    # Read
    # ----------------------------------------------------------

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get recent analysis history (newest first)."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT id, pipeline_id, video_name, analyzed_at,
                          total_score, grade, confidence, version, elapsed_seconds
                   FROM analyses ORDER BY analyzed_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_by_id(self, analysis_id: int) -> Optional[Dict]:
        """Get full analysis result by id."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
            ).fetchone()
            if not row:
                return None
            result = dict(row)
            dims = conn.execute(
                "SELECT * FROM dimension_scores WHERE analysis_id = ?",
                (analysis_id,),
            ).fetchall()
            result["dimensions"] = [dict(d) for d in dims]
        return result

    def get_growth_data(self, video_name_prefix: str) -> List[Dict]:
        """
        Get time-series data for growth analysis.
        Matches video names starting with the given prefix (e.g. teacher name).
        """
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT a.id, a.video_name, a.analyzed_at, a.total_score,
                          a.grade, a.confidence
                   FROM analyses a
                   WHERE a.video_name LIKE ?
                   ORDER BY a.analyzed_at ASC""",
                (f"{video_name_prefix}%",),
            ).fetchall()

        results = []
        with self._conn() as conn:
            for r in rows:
                entry = dict(r)
                dims = conn.execute(
                    "SELECT name, score, max_score, percentage FROM dimension_scores WHERE analysis_id = ?",
                    (r["id"],),
                ).fetchall()
                entry["dimensions"] = [dict(d) for d in dims]
                results.append(entry)
        return results

    def count(self) -> int:
        """Total number of analyses."""
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]

    def delete_by_id(self, analysis_id: int) -> bool:
        """Delete an analysis and its dimension scores."""
        with self._conn() as conn:
            conn.execute("DELETE FROM dimension_scores WHERE analysis_id = ?", (analysis_id,))
            cur = conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
            conn.commit()
        return cur.rowcount > 0
