"""FastAPI application — Alzheimer Chat-RL.

Two UIs served from /static/index.html:
    /           →  conversation interface (cuidador + paciente)
    /dashboard  →  caregiver analytics panel

REST API:
    POST /api/sessions              create session
    GET  /api/sessions              list all sessions
    GET  /api/sessions/{id}         session detail
    POST /api/sessions/{id}/turn    execute one turn
    POST /api/sessions/{id}/end     mark session finished
    GET  /api/sessions/{id}/summary engagement summary
"""
from __future__ import annotations

import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC = ROOT / "static"

# ─── Domain imports ───────────────────────────────────────────────
import sys
sys.path.insert(0, str(ROOT))

from src.chatbot.actions import AgentAction
from src.chatbot.activities import ActivityBank
from src.chatbot.tests import CognitiveTestBank
from src.data.local_knowledge import get_local_knowledge
from src.patient_simulator import PatientSimulator
from src.rl.renderer import render_action
from src.signals.engagement_detector import EngagementDetector
from src.signals.interest_tracker import InterestTracker
from src.signals.latency_model import make_signal

# ─── Pydantic models ──────────────────────────────────────────────

class SessionConfig(BaseModel):
    mode: str = "rules_only"       # rules_only | llm_hybrid | llm_only
    language: str = "es"
    city: Optional[str] = None
    birth_year: int = 1945
    seed: Optional[int] = None
    max_turns: int = 20


class TurnRequest(BaseModel):
    action_id: Optional[int] = None   # AgentAction value (0-12)
    free_text: Optional[str] = None   # custom utterance


class TurnResponse(BaseModel):
    turn_id: int
    action_name: str
    agent_utterance: str
    patient_response: str
    latency_s: float
    is_silent: bool
    strategy_fit: float
    test_success: Optional[bool] = None
    test_domain: Optional[str] = None
    test_expected: Optional[str] = None
    triggered_like: Optional[str] = None
    triggered_dislike: Optional[str] = None
    alarms: list[str]
    patient_state: dict
    engagement: dict


class SessionSummary(BaseModel):
    session_id: str
    patient_name: str
    patient_age: int
    patient_stage: str
    n_turns: int
    started_at: str
    ended_at: Optional[str]
    alarms: list[str]
    engagement: dict
    transcript: list[dict]


# ─── In-memory session store ──────────────────────────────────────

class _Session:
    def __init__(self, cfg: SessionConfig):
        self.id = str(uuid.uuid4())[:8]
        self.cfg = cfg
        seed = cfg.seed or random.randint(0, 999_999)
        self.sim = PatientSimulator(seed=seed, mode=cfg.mode, language=cfg.language)
        self.bank = CognitiveTestBank(seed=seed)
        self.activity_bank = ActivityBank(seed=seed)
        self.tracker = InterestTracker()
        self.detector = EngagementDetector()
        self.detector.attach_tracker(self.tracker)
        self.rng = random.Random(seed)
        self.last_test = None
        self.n_turns = 0
        self.transcript: list[dict] = []
        self.started_at = datetime.now().isoformat(timespec="seconds")
        self.ended_at: Optional[str] = None
        self.local_knowledge = None
        if cfg.city:
            try:
                self.local_knowledge = get_local_knowledge(cfg.city, birth_year=cfg.birth_year)
            except Exception:
                pass

    def to_list_item(self) -> dict:
        alarms = self.tracker.check_alarms(self.sim.state)
        return {
            "session_id": self.id,
            "patient_name": self.sim.profile.name,
            "patient_age": self.sim.profile.age,
            "patient_stage": self.sim.state.stage.value,
            "mmse": self.sim.state.mmse,
            "city": self.cfg.city or "",
            "n_turns": self.n_turns,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "n_alarms": len(alarms),
            "engagement": self.tracker.engagement_summary(),
        }


_sessions: dict[str, _Session] = {}


# ─── FastAPI app ──────────────────────────────────────────────────

app = FastAPI(title="Alzheimer Chat-RL", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


@app.get("/", response_class=FileResponse)
def root():
    return FileResponse(str(STATIC / "landing.html"))


@app.get("/app", response_class=FileResponse)
def app_ui():
    return FileResponse(str(STATIC / "index.html"))


@app.get("/dashboard", response_class=FileResponse)
def dashboard():
    return FileResponse(str(STATIC / "dashboard.html"))


@app.get("/science", response_class=FileResponse)
def science():
    return FileResponse(str(STATIC / "science.html"))


@app.get("/supervise", response_class=FileResponse)
def supervise():
    return FileResponse(str(STATIC / "supervise.html"))


# ─── Session endpoints ────────────────────────────────────────────

@app.post("/api/sessions", response_model=dict)
def create_session(cfg: SessionConfig):
    s = _Session(cfg)
    _sessions[s.id] = s
    info = s.to_list_item()
    info["profile"] = s.sim.profile.as_dict(hide_private=True)
    info["state"] = s.sim.state.as_dict()
    if s.local_knowledge:
        info["local_knowledge"] = {
            "city": s.local_knowledge.city,
            "region": s.local_knowledge.region,
            "football_team": s.local_knowledge.football_team,
            "dishes": s.local_knowledge.dishes[:4],
            "festivals": s.local_knowledge.festivals[:3],
            "era_content": s.local_knowledge.era_content(cfg.birth_year)[:3],
        }
    return info


@app.get("/api/sessions", response_model=list)
def list_sessions():
    return [s.to_list_item() for s in reversed(list(_sessions.values()))]


@app.get("/api/sessions/{sid}", response_model=dict)
def get_session(sid: str):
    s = _get(sid)
    info = s.to_list_item()
    info["profile"] = s.sim.profile.as_dict(hide_private=True)
    info["state"] = s.sim.state.as_dict()
    info["transcript"] = s.transcript
    info["alarms"] = s.tracker.check_alarms(s.sim.state)
    return info


@app.post("/api/sessions/{sid}/turn", response_model=TurnResponse)
def execute_turn(sid: str, req: TurnRequest):
    s = _get(sid)
    if s.ended_at:
        raise HTTPException(400, "Session already ended")
    if s.n_turns >= s.cfg.max_turns:
        raise HTTPException(400, f"Max turns ({s.cfg.max_turns}) reached")

    # Determine utterance
    is_procedural = False
    test = None

    if req.free_text:
        utterance = req.free_text
        action_name = "FREE_TEXT"
    elif req.action_id is not None:
        try:
            action = AgentAction(req.action_id)
        except ValueError:
            raise HTTPException(400, f"Invalid action_id {req.action_id}")
        action_name = action.name
        trending = s.tracker.trending(3)
        utterance, test = render_action(
            s.sim, action, s.bank, s.rng,
            last_test=s.last_test,
            activity_bank=s.activity_bank,
            trending_tags=trending,
        )
        is_procedural = bool(test and test.metadata.get("is_procedural", False))
    else:
        raise HTTPException(400, "Provide action_id or free_text")

    # Patient responds
    mood_before = s.sim.state.mood
    turn = s.sim.reply(
        utterance,
        is_procedural=is_procedural,
        topic_category=test.domain if test else None,
    )
    mood_delta = s.sim.state.mood - mood_before

    # Evaluate test
    test_success = None
    test_domain = None
    test_expected = None
    if test:
        result = CognitiveTestBank.evaluate(test, turn.text)
        test_success = result.success
        test_domain = test.domain
        test_expected = test.metadata.get("completion")
        s.sim.record_test_outcome(result.success)
        s.last_test = test
        s.tracker.update(
            test.domain,
            success=test_success,
            latency_s=turn.latency_s,
            mood_delta=mood_delta,
            response_length=len(turn.text.split()),
            is_silent=turn.is_silent,
        )

    s.tracker.update_anxiety(s.sim.state.anxiety)
    alarms = s.tracker.check_alarms(s.sim.state)
    strategy_fit = round(1.0 - min(turn.latency_s / 12.0, 1.0), 3)
    s.detector.record(make_signal(turn.latency_s, s.tracker._silence_streak))
    s.n_turns += 1

    record = dict(
        turn_id=s.n_turns,
        action_name=action_name,
        agent_utterance=utterance,
        patient_response=turn.text,
        latency_s=turn.latency_s,
        is_silent=turn.is_silent,
        strategy_fit=strategy_fit,
        test_success=test_success,
        test_domain=test_domain,
        test_expected=test_expected,
        triggered_like=turn.triggered_like,
        triggered_dislike=turn.triggered_dislike,
        alarms=alarms,
        patient_state=turn.state,
        engagement=s.tracker.engagement_summary(),
    )
    s.transcript.append(record)

    # Auto-end on CLOSE_TURN or fatigue
    if req.action_id == AgentAction.CLOSE_TURN.value or s.sim.state.fatigue >= 0.95:
        s.ended_at = datetime.now().isoformat(timespec="seconds")

    return TurnResponse(**record)


@app.post("/api/sessions/{sid}/end")
def end_session(sid: str):
    s = _get(sid)
    s.ended_at = datetime.now().isoformat(timespec="seconds")
    eng = s.detector.evaluate(alarms=s.tracker.check_alarms(s.sim.state))
    return {
        "session_id": s.id,
        "ended_at": s.ended_at,
        "n_turns": s.n_turns,
        "engagement": {
            "avg_latency_s": eng.avg_latency_s,
            "avg_strategy_fit": eng.avg_strategy_fit,
            "activity_success_rate": eng.activity_success_rate,
            "silence_streak_max": eng.silence_streak_max,
            "trending_topics": eng.trending_topics,
            "alarms": eng.alarms,
            "topic_scores": eng.topic_scores,
        },
    }


@app.get("/api/sessions/{sid}/summary")
def session_summary(sid: str):
    s = _get(sid)
    eng = s.detector.evaluate(alarms=s.tracker.check_alarms(s.sim.state))
    latencies = [t["latency_s"] for t in s.transcript]
    fits = [t["strategy_fit"] for t in s.transcript]
    return {
        "session_id": s.id,
        "patient": s.sim.profile.as_dict(hide_private=False),
        "n_turns": s.n_turns,
        "latencies": latencies,
        "strategy_fits": fits,
        "engagement_summary": eng.summary_text(),
        "topic_scores": eng.topic_scores,
        "trending": eng.trending_topics,
        "alarms": eng.alarms,
        "transcript": s.transcript,
    }


@app.get("/api/actions")
def list_actions():
    return [{"id": a.value, "name": a.name} for a in AgentAction]


# ─── Science / research endpoints ────────────────────────────────

@app.get("/api/science/stats")
def science_stats():
    sessions = list(_sessions.values())
    if not sessions:
        return {
            "empty": True, "n_sessions": 0, "n_turns_total": 0,
            "silence_rate": 0, "stage_distribution": {}, "mmse_values": [],
            "action_stats": {}, "latency_by_stage": {}, "domain_success": {},
            "alarm_counts": {}, "avg_topic_scores": {},
            "mood_trajectories": [], "strategy_fit_trajectories": [],
        }

    stage_counts: dict[str, int] = {}
    mmse_values: list[float] = []
    action_data: dict[str, dict] = {}
    latency_by_stage: dict[str, list] = {}
    domain_tests: dict[str, list] = {}
    alarm_counts: dict[str, int] = {}
    all_topic_scores: dict[str, list] = {}
    n_turns_total = 0
    n_silent_total = 0

    for s in sessions:
        stage_counts[s.sim.state.stage.value] = stage_counts.get(s.sim.state.stage.value, 0) + 1
        mmse_values.append(s.sim.state.mmse)
        n_turns_total += s.n_turns

        for turn in s.transcript:
            n_silent_total += int(turn["is_silent"])
            an = turn["action_name"]
            if an not in action_data:
                action_data[an] = {"n": 0, "latencies": [], "fits": [], "successes": []}
            action_data[an]["n"] += 1
            action_data[an]["latencies"].append(turn["latency_s"])
            action_data[an]["fits"].append(turn["strategy_fit"])
            if turn["test_success"] is not None:
                action_data[an]["successes"].append(int(turn["test_success"]))
            t_stage = turn["patient_state"].get("stage", "UNKNOWN")
            latency_by_stage.setdefault(t_stage, []).append(turn["latency_s"])
            if turn["test_domain"] and turn["test_success"] is not None:
                domain_tests.setdefault(turn["test_domain"], []).append(int(turn["test_success"]))
            for alarm in turn["alarms"]:
                alarm_counts[alarm] = alarm_counts.get(alarm, 0) + 1

        eng = s.tracker.engagement_summary()
        for topic, score in eng.get("topic_scores", {}).items():
            all_topic_scores.setdefault(topic, []).append(score)

    def avg(lst: list) -> float:
        return round(sum(lst) / len(lst), 3) if lst else 0.0

    return {
        "empty": False,
        "n_sessions": len(sessions),
        "n_turns_total": n_turns_total,
        "silence_rate": round(n_silent_total / n_turns_total, 3) if n_turns_total else 0,
        "stage_distribution": stage_counts,
        "mmse_values": mmse_values,
        "action_stats": {
            an: {
                "n": d["n"],
                "avg_latency": avg(d["latencies"]),
                "avg_strategy_fit": avg(d["fits"]),
                "success_rate": avg(d["successes"]) if d["successes"] else None,
            }
            for an, d in action_data.items()
        },
        "latency_by_stage": {
            stage: {
                "avg": avg(v),
                "max": round(max(v), 2),
                "silence_rate": round(sum(1 for x in v if x >= 12.0) / len(v), 3),
            }
            for stage, v in latency_by_stage.items()
        },
        "domain_success": {d: avg(v) for d, v in domain_tests.items()},
        "alarm_counts": alarm_counts,
        "avg_topic_scores": {t: avg(v) for t, v in all_topic_scores.items()},
        "mood_trajectories": [
            [t["patient_state"].get("mood", 0) for t in s.transcript]
            for s in sessions if s.transcript
        ],
        "strategy_fit_trajectories": [
            [t["strategy_fit"] for t in s.transcript]
            for s in sessions if s.transcript
        ],
    }


# ─── Helpers ──────────────────────────────────────────────────────

def _get(sid: str) -> _Session:
    if sid not in _sessions:
        raise HTTPException(404, f"Session {sid} not found")
    return _sessions[sid]
