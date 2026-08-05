"""Hidden Insights Generator."""
from typing import List, Dict, Any
import scipy.stats as stats
import pandas as pd
from openai import AsyncOpenAI
import os

async def find_hidden_insights(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Output 12: Hidden insights using scipy + LLM."""
    if not videos or len(videos) < 5:
        return [{"insight": "Not enough data for statistical correlation. Need at least 5 videos."}]
        
    df = pd.DataFrame(videos)
    if 'duration_sec' not in df.columns or 'views' not in df.columns:
        return [{"insight": "Missing required metrics (duration_sec, views) for correlation."}]
        
    # Calculate Pearson correlation
    corr, p_value = stats.pearsonr(df['duration_sec'].fillna(0), df['views'].fillna(0))
    
    # Prompt LLM with the stat
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return [{"insight": f"Correlation duration vs views: r={corr:.2f}, p={p_value:.2f}"}]

    client = AsyncOpenAI(api_key=api_key)
    prompt = f"Given that the Pearson correlation between video duration and views is {corr:.2f} (p-value: {p_value:.2f}), write a short, actionable insight for the YouTube creator."
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a YouTube analytics expert."},
                      {"role": "user", "content": prompt}]
        )
        insight_text = response.choices[0].message.content
        return [{
            "type": "correlation_duration_views",
            "stat": f"r={corr:.2f}, p={p_value:.2f}",
            "insight": insight_text
        }]
    except Exception as e:
        return [{"error": str(e), "stat": f"r={corr:.2f}"}]
