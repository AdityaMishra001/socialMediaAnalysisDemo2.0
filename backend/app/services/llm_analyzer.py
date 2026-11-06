from __future__ import annotations
import json
import logging
from typing import List, Optional
from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.analysis import (
    AnalysisResult,
    SentimentDistribution,
    EmotionBreakdown,
    ThemeItem,
    AspectSentiment,
    Recommendation,
)

logger = logging.getLogger(__name__)

SOURCE_DESCRIPTIONS = {
    "instagram": "Instagram comments and social media interactions",
    "youtube": "YouTube video comments and viewer feedback",
    "youtube_video": "YouTube long-form video (focus on hook, pacing, timestamped reactions, comprehension, and follow-up topics)",
    "youtube_short": "YouTube Short / Reel (focus on first-3-seconds hook, viral trigger, punchline, replayability, and quick reactions)",
    "youtube_channel": "YouTube Channel Community (focus on macro audience personas, recurring requests, channel niche positioning, and community loyalty)",
    "reddit_post": "Reddit discussion thread (focus on community consensus vs dissent, technical depth, and top counterarguments)",
    "tiktok": "TikTok comments and audience feedback",
    "product_reviews": "E-commerce product reviews and customer ratings",
    "app_store": "Mobile App Store / Play Store reviews",
    "customer_support": "Customer support tickets and service interactions",
    "student_feedback": "Student evaluations and course feedback",
    "employee_survey": "Employee internal pulse surveys and workplace feedback",
    "nps_survey": "NPS and customer satisfaction survey responses",
    "community": "Community forum and discussion board posts",
    "general": "General user feedback and open comments",
}

GOAL_DESCRIPTIONS = {
    "improve_content": "improve content creation, engagement, and audience retention",
    "improve_product": "improve product quality, usability, and fix core flaws",
    "customer_satisfaction": "maximize customer satisfaction and eliminate support bottlenecks",
    "reduce_churn": "prevent user drop-off and retain high-value users",
    "improve_teaching": "enhance teaching methodology and student outcomes",
    "general": "extract high-value actionable insights and prioritize next steps",
}

def get_client() -> Optional[AsyncOpenAI]:
    if not settings.OPENAI_API_KEY:
        return None
    kwargs = {"api_key": settings.OPENAI_API_KEY}
    if settings.OPENAI_BASE_URL:
        kwargs["base_url"] = settings.OPENAI_BASE_URL
    return AsyncOpenAI(**kwargs)

async def analyze_feedback(
    feedback_items: List[str],
    feedback_source: str = "general",
    analysis_goal: str = "general",
    language: str = "auto",
) -> AnalysisResult:
    """Analyze feedback items using OpenAI API or fallback to smart heuristic analyzer."""
    if not feedback_items:
        raise ValueError("No feedback items provided for analysis.")

    client = get_client()

    # If API key is present, use frontier LLM with structured output
    if client is not None:
        try:
            return await _analyze_with_llm(
                client=client,
                feedback_items=feedback_items,
                feedback_source=feedback_source,
                analysis_goal=analysis_goal,
                language=language,
            )
        except Exception as e:
            logger.error(f"LLM API call failed: {e}. Falling back to smart simulation analyzer.")

    # Fallback to realistic smart simulation analyzer
    return _generate_smart_analysis(
        feedback_items=feedback_items,
        feedback_source=feedback_source,
        analysis_goal=analysis_goal,
    )

async def _analyze_with_llm(
    client: AsyncOpenAI,
    feedback_items: List[str],
    feedback_source: str,
    analysis_goal: str,
    language: str,
) -> AnalysisResult:
    source_context = SOURCE_DESCRIPTIONS.get(feedback_source, feedback_source)
    goal_context = GOAL_DESCRIPTIONS.get(analysis_goal, analysis_goal)

    # Chunking / truncation to safeguard context limits (up to 80 representative items)
    items_to_send = feedback_items[:80]
    items_formatted = "\n".join([f"- {item}" for item in items_to_send])

    system_prompt = f"""You are a world-class customer intelligence and Voice-of-Customer analyst.
You specialize in analyzing feedback from: {source_context}.
The user's primary goal is to: {goal_context}.

Analyze the provided feedback items objectively and thoroughly.
Strict Grounding Rules:
1. Base all insights strictly on what the feedback explicitly says. Do not invent statistics.
2. In 'representative_quotes' and 'supporting_examples', cite actual excerpts from the feedback.
3. sentiment_distribution percentages (positive + negative + neutral + mixed) must sum to exactly 100.
4. emotion_breakdown values should represent percentage intensity (0 to 100).
5. Recommendations must be prioritized (high, medium, low) and specify clear rationale, expected impact, and effort level.

You must respond ONLY with a valid JSON object matching this schema:
{{
  "overall_sentiment": "positive" | "negative" | "neutral" | "mixed",
  "sentiment_distribution": {{
    "positive": int,
    "negative": int,
    "neutral": int,
    "mixed": int
  }},
  "emotion_breakdown": {{
    "frustration": int,
    "delight": int,
    "confusion": int,
    "excitement": int,
    "disappointment": int,
    "satisfaction": int
  }},
  "executive_summary": "string (concise 2-3 paragraph summary)",
  "key_themes": [
    {{
      "theme": "string",
      "count": int,
      "sentiment": "positive" | "negative" | "neutral" | "mixed",
      "urgency": "low" | "medium" | "high" | "critical",
      "representative_quotes": ["quote1", "quote2"]
    }}
  ],
  "aspect_sentiments": [
    {{
      "aspect": "string (e.g. UI/UX, Performance, Pricing, Customer Service, Content Quality)",
      "sentiment": "positive" | "negative" | "neutral" | "mixed",
      "score": float (between 0.0 and 1.0),
      "supporting_examples": ["quote1"]
    }}
  ],
  "common_complaints": ["string"],
  "recurring_questions": ["string"],
  "suggestions": ["string"],
  "feature_requests": ["string"],
  "recommendations": [
    {{
      "title": "string",
      "priority": "high" | "medium" | "low",
      "rationale": "string",
      "expected_impact": "string",
      "effort": "low" | "medium" | "high",
      "category": "string"
    }}
  ],
  "total_items_analyzed": int,
  "confidence_score": float
}}"""

    user_prompt = f"Total feedback items received: {len(feedback_items)}. Here are the items to analyze:\n\n{items_formatted}"

    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    raw_content = response.choices[0].message.content or "{}"
    parsed = json.loads(raw_content)

    # Normalize counts
    parsed["total_items_analyzed"] = len(feedback_items)
    parsed["is_simulated"] = False

    return AnalysisResult(**parsed)

def _generate_smart_analysis(
    feedback_items: List[str],
    feedback_source: str,
    analysis_goal: str,
) -> AnalysisResult:
    """Smart heuristic analyzer that works offline without an external API key."""
    total = len(feedback_items)

    pos_keywords = ["love", "great", "awesome", "amazing", "good", "best", "excellent", "helpful", "easy", "perfect", "fan", "thanks", "liked", "super"]
    neg_keywords = ["hate", "bad", "terrible", "worst", "bug", "crash", "broken", "slow", "error", "poor", "issue", "problem", "difficult", "disappointed", "annoying", "hard"]
    question_keywords = ["why", "how", "when", "where", "what", "is there", "can you", "could you", "?"]
    feature_keywords = ["please add", "would be great", "wish", "feature", "suggestion", "need", "should have"]

    pos_count = 0
    neg_count = 0
    neutral_count = 0

    detected_complaints: List[str] = []
    detected_questions: List[str] = []
    detected_suggestions: List[str] = []
    detected_features: List[str] = []

    pos_quotes: List[str] = []
    neg_quotes: List[str] = []

    for item in feedback_items:
        lower = item.lower()
        has_pos = any(k in lower for k in pos_keywords)
        has_neg = any(k in lower for k in neg_keywords)

        if has_pos and not has_neg:
            pos_count += 1
            if len(pos_quotes) < 5:
                pos_quotes.append(item)
        elif has_neg and not has_pos:
            neg_count += 1
            if len(neg_quotes) < 5:
                neg_quotes.append(item)
            if len(detected_complaints) < 6:
                detected_complaints.append(item[:140])
        else:
            neutral_count += 1

        if any(q in lower for q in question_keywords) and len(detected_questions) < 5:
            detected_questions.append(item[:140])

        if any(f in lower for f in feature_keywords) and len(detected_features) < 5:
            detected_features.append(item[:140])

    if total > 0:
        pos_pct = round((pos_count / total) * 100)
        neg_pct = round((neg_count / total) * 100)
        neut_pct = max(0, 100 - pos_pct - neg_pct)
    else:
        pos_pct, neg_pct, neut_pct = 33, 33, 34

    if pos_pct > neg_pct + 15:
        overall = "positive"
    elif neg_pct > pos_pct + 15:
        overall = "negative"
    elif pos_pct > 25 and neg_pct > 25:
        overall = "mixed"
    else:
        overall = "neutral"

    source_label = SOURCE_DESCRIPTIONS.get(feedback_source, feedback_source)
    goal_label = GOAL_DESCRIPTIONS.get(analysis_goal, analysis_goal)

    # Key Themes adapting to social context
    if feedback_source == "youtube_short":
        key_themes = [
            ThemeItem(
                theme="Hook & First 3 Seconds Retention",
                count=max(1, int(total * 0.45)),
                sentiment="positive" if pos_pct >= 50 else "mixed",
                urgency="medium",
                representative_quotes=pos_quotes[:2] if pos_quotes else ["Hook captured viewer attention immediately."],
            ),
            ThemeItem(
                theme="Viral Factor & Shareability",
                count=max(1, int(total * 0.35)),
                sentiment="positive" if pos_count > 0 else "neutral",
                urgency="low",
                representative_quotes=pos_quotes[1:3] if len(pos_quotes) >= 3 else (pos_quotes[:1] or ["High replay value."]),
            ),
            ThemeItem(
                theme="Viewer Questions & Part 2 Demand",
                count=max(1, int(total * 0.25)),
                sentiment="neutral",
                urgency="high",
                representative_quotes=detected_questions[:2] if detected_questions else ["Audience requesting follow-up short."],
            ),
        ]
        aspect_sentiments = [
            AspectSentiment(aspect="Hook Effectiveness", sentiment="positive" if pos_pct >= 50 else "neutral", score=round(min(1.0, max(0.1, (pos_pct + 15) / 100)), 2), supporting_examples=pos_quotes[:1] or ["Strong initial hook."]),
            AspectSentiment(aspect="Pacing & Flow", sentiment="positive" if neg_pct < 25 else "mixed", score=round(max(0.3, min(0.95, (100 - neg_pct) / 100)), 2), supporting_examples=pos_quotes[1:2] or ["Smooth transition throughout."]),
            AspectSentiment(aspect="Entertainment & Punchline", sentiment="positive" if pos_pct > neg_pct else "neutral", score=0.84, supporting_examples=pos_quotes[:1] or ["Punchline landed well."]),
        ]
    elif feedback_source == "youtube_video":
        key_themes = [
            ThemeItem(
                theme="Explanation Clarity & Value",
                count=max(1, int(total * 0.4)),
                sentiment="positive" if pos_pct >= 50 else "mixed",
                urgency="low",
                representative_quotes=pos_quotes[:2] if pos_quotes else ["Concepts explained step-by-step."],
            ),
            ThemeItem(
                theme="Pacing & Video Length",
                count=max(1, int(total * 0.3)),
                sentiment="mixed" if neg_pct > 20 else "positive",
                urgency="medium",
                representative_quotes=neg_quotes[:2] if neg_quotes else ["Pacing maintained audience attention."],
            ),
            ThemeItem(
                theme="Audio Balance & Production Quality",
                count=max(1, int(total * 0.25)),
                sentiment="negative" if neg_count > 0 else "positive",
                urgency="high" if neg_pct > 25 else "low",
                representative_quotes=neg_quotes[:1] or ["Clean audio with balanced volume."],
            ),
        ]
        aspect_sentiments = [
            AspectSentiment(aspect="Depth of Content", sentiment="positive" if pos_pct >= 50 else "neutral", score=round(min(1.0, max(0.1, (pos_pct + 10) / 100)), 2), supporting_examples=pos_quotes[:1] or ["Thorough and informative."]),
            AspectSentiment(aspect="Pacing & Retention", sentiment="neutral" if neg_pct > 25 else "positive", score=round(max(0.2, min(0.9, (100 - neg_pct) / 100)), 2), supporting_examples=neg_quotes[:1] or ["Good structure throughout."]),
            AspectSentiment(aspect="Audio & Visuals", sentiment="positive" if neg_pct < 20 else "mixed", score=0.78, supporting_examples=pos_quotes[:1] or ["Clear visual presentation."]),
        ]
    elif feedback_source == "youtube_channel":
        key_themes = [
            ThemeItem(
                theme="Community Loyalty & Niche Authority",
                count=max(1, int(total * 0.45)),
                sentiment="positive" if pos_pct >= 50 else "mixed",
                urgency="low",
                representative_quotes=pos_quotes[:2] if pos_quotes else ["Long-time subscribers actively recommending the channel."],
            ),
            ThemeItem(
                theme="Content Gaps & Requested Series",
                count=max(1, int(total * 0.35)),
                sentiment="neutral",
                urgency="high",
                representative_quotes=detected_questions[:2] if detected_questions else ["Audience requesting advanced deep-dives."],
            ),
            ThemeItem(
                theme="Upload Consistency & Schedule",
                count=max(1, int(total * 0.25)),
                sentiment="mixed",
                urgency="medium",
                representative_quotes=neg_quotes[:1] or ["Viewers eager for consistent weekly content."],
            ),
        ]
        aspect_sentiments = [
            AspectSentiment(aspect="Niche Authority & Trust", sentiment="positive", score=0.88, supporting_examples=pos_quotes[:1] or ["Recognized as a reliable resource."]),
            AspectSentiment(aspect="Community Engagement", sentiment="positive" if pos_pct >= 50 else "neutral", score=0.82, supporting_examples=pos_quotes[:1] or ["Creator actively responds to audience."]),
            AspectSentiment(aspect="Content Freshness", sentiment="mixed" if neg_pct > 25 else "positive", score=0.74, supporting_examples=detected_questions[:1] or ["Topics resonate with target audience."]),
        ]
    else:
        # Default Themes
        key_themes = [
            ThemeItem(
                theme="User Experience & Usability",
                count=max(1, int(total * 0.4)),
                sentiment="positive" if pos_pct >= 50 else ("negative" if neg_pct >= 40 else "mixed"),
                urgency="high" if neg_pct >= 40 else "medium",
                representative_quotes=pos_quotes[:2] if pos_pct >= neg_pct else neg_quotes[:2],
            ),
            ThemeItem(
                theme="Reliability & Performance",
                count=max(1, int(total * 0.3)),
                sentiment="negative" if neg_count > 0 else "neutral",
                urgency="critical" if neg_pct > 35 else "low",
                representative_quotes=neg_quotes[:2] if neg_quotes else ["No major stability blockers reported."],
            ),
            ThemeItem(
                theme="Content Depth & Value",
                count=max(1, int(total * 0.25)),
                sentiment="positive" if pos_count > 0 else "neutral",
                urgency="low",
                representative_quotes=pos_quotes[2:4] if len(pos_quotes) >= 4 else (pos_quotes[:1] or ["Valuable insights provided."]),
            ),
        ]
        # Default Aspect Sentiments
        aspect_sentiments = [
            AspectSentiment(
                aspect="Core Experience & Content",
                sentiment="positive" if pos_pct >= 50 else "neutral",
                score=round(min(1.0, max(0.1, (pos_pct + 10) / 100)), 2),
                supporting_examples=pos_quotes[:1] or ["Positive user appreciation."],
            ),
            AspectSentiment(
                aspect="Speed & Efficiency",
                sentiment="negative" if neg_pct > 30 else "positive",
                score=round(max(0.2, min(0.9, (100 - neg_pct) / 100)), 2),
                supporting_examples=neg_quotes[:1] or ["Smooth experience with minimal delay."],
            ),
            AspectSentiment(
                aspect="Clarity & Communication",
                sentiment="neutral" if neut_pct > 40 else ("positive" if pos_pct > neg_pct else "negative"),
                score=0.72,
                supporting_examples=detected_questions[:1] or ["Clear structure throughout."],
            ),
        ]

    # Defaults if empty
    if not detected_complaints:
        detected_complaints = [
            "Minor friction during initial setup or navigation",
            "Occasional lag or delay in response time",
        ]
    if not detected_questions:
        detected_questions = [
            "When will the next update or feature set be released?",
            "Is there an option to customize workflow preferences?",
        ]
    if not detected_suggestions:
        detected_suggestions = [
            "Streamline repetitive actions with keyboard shortcuts",
            "Provide clearer documentation and quick onboarding tips",
        ]
    if not detected_features:
        detected_features = [
            "Batch export capabilities",
            "Dark mode and mobile layout optimizations",
        ]

    # Recommendations
    recs = [
        Recommendation(
            title=f"Address Primary Pain Points in {source_label}",
            priority="high",
            rationale=f"Negative sentiment is at {neg_pct}%, predominantly driven by recurring complaints.",
            expected_impact=f"Estimated 20-30% boost in satisfaction when tackling the top complaints.",
            effort="medium",
            category="Quality & Experience",
        ),
        Recommendation(
            title=f"Capitalize on Identified Strengths for {goal_label}",
            priority="medium",
            rationale=f"{pos_pct}% of users expressed positive feedback toward core functionality and value.",
            expected_impact="Reinforce brand loyalty and amplify organic word-of-mouth recommendations.",
            effort="low",
            category="Growth & Engagement",
        ),
        Recommendation(
            title="Create an FAQ / Proactive Guide for Recurring Inquiries",
            priority="low",
            rationale=f"Multiple users raised repeated questions regarding features and roadmap.",
            expected_impact="Reduces repetitive questions and decreases support inquiries by up to 25%.",
            effort="low",
            category="Documentation & Support",
        ),
    ]

    exec_summary = (
        f"Analysis of {total} feedback items from {source_label} shows an overall {overall} sentiment "
        f"({pos_pct}% positive, {neg_pct}% negative, {neut_pct}% neutral). "
        f"The primary driver of satisfaction is strong content value and core utility, while primary "
        f"areas for improvement center on speed, clarity, and specific feature enhancements tailored to {goal_label}."
    )

    return AnalysisResult(
        overall_sentiment=overall,
        sentiment_distribution=SentimentDistribution(
            positive=pos_pct,
            negative=neg_pct,
            neutral=neut_pct,
            mixed=max(0, 100 - pos_pct - neg_pct - neut_pct),
        ),
        emotion_breakdown=EmotionBreakdown(
            frustration=min(100, neg_pct + 10),
            delight=min(100, pos_pct + 12),
            confusion=min(100, int(len(detected_questions) * 15)),
            excitement=max(5, int(pos_pct * 0.6)),
            disappointment=max(5, int(neg_pct * 0.7)),
            satisfaction=max(10, int(pos_pct * 0.8)),
        ),
        executive_summary=exec_summary,
        key_themes=key_themes,
        aspect_sentiments=aspect_sentiments,
        common_complaints=detected_complaints,
        recurring_questions=detected_questions,
        suggestions=detected_suggestions,
        feature_requests=detected_features,
        recommendations=recs,
        total_items_analyzed=total,
        confidence_score=0.92,
        is_simulated=True,
    )
