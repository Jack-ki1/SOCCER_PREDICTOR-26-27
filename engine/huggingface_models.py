"""
Hugging Face model integration — honest scope.

Checked during planning (build plan §6): there is no authoritative,
production-grade pretrained EPL outcome-prediction model on Hugging Face
worth depending on. Academic literature on ML in sports prediction
consistently shows gradient-boosted trees (engine/ml_models.py) matching
or beating deep-learning approaches on this specific tabular problem — so
this module's job is deliberately narrower than "download a predictor":

    1. Sentiment/NLP on pre-match team news, as ONE additional feature for
       the ML ensemble (mirrors what Beal et al.'s ~63%-accuracy published
       ensemble did with text signals) — not a probability generator on
       its own.
    2. A place to load your own fine-tuned model later, once you have
       enough proprietary historical + engineered-feature data to make
       that worthwhile.

Nothing here should be plugged in a way that lets an LLM's output become
the probability numbers themselves — that's a regression from "transparent
maths" back to "vibes," which cuts against the whole design of this
project. Explanations, yes (v4 in the roadmap). Predictions, no.

Requires `transformers` + a torch/tf backend if you actually want to run
inference — imported lazily so the rest of the project works without it.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NewsSentiment:
    text: str
    label: str      # 'positive' | 'negative' | 'neutral'
    score: float     # confidence, 0-1


_PIPELINE_CACHE = {}


def _get_sentiment_pipeline():
    """Lazily loads a general-purpose HF sentiment model. Swap the model id for
    anything you prefer — this is a reasonable, small, widely-used default."""
    if "sentiment" not in _PIPELINE_CACHE:
        try:
            from transformers import pipeline
            _PIPELINE_CACHE["sentiment"] = pipeline(
                "sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english",
            )
        except ImportError as exc:
            raise ImportError(
                "engine.huggingface_models needs `pip install transformers torch` to run inference. "
                "The rest of the project works fine without it — this module is optional enrichment."
            ) from exc
    return _PIPELINE_CACHE["sentiment"]


def analyze_team_news(text: str) -> NewsSentiment:
    """
    Runs one piece of team-news/press-conference text through a
    general-purpose sentiment model. The output is meant to become a
    single scalar feature (positive-news-score) in
    engine/feature_engineering.py, not a standalone prediction.
    """
    pipe = _get_sentiment_pipeline()
    result = pipe(text[:512])[0]  # truncate — this is a lightweight signal, not full-document analysis
    return NewsSentiment(text=text, label=result["label"].lower(), score=float(result["score"]))


def team_news_feature(texts: list[str]) -> float:
    """
    Aggregates several news snippets into one feature value in roughly
    [-1, 1] (negative = bad news dominant, positive = good news dominant).
    Returns 0.0 (neutral) if transformers isn't installed or no text is
    given — this must degrade gracefully, since it's explicitly optional.
    """
    if not texts:
        return 0.0
    try:
        scores = []
        for t in texts:
            s = analyze_team_news(t)
            scores.append(s.score if s.label == "positive" else -s.score)
        return sum(scores) / len(scores)
    except ImportError:
        return 0.0
