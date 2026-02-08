import json
import os
from datetime import datetime
from typing import Dict, Any, List

class Reporter:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def save_run_results(self, run_id: str, top3: List[Dict], ranking: List[Dict], as_of: datetime):
        """
        Save JSON and Markdown reports.
        """
        date_str = as_of.strftime("%Y%m%d")
        day_dir = os.path.join(self.output_dir, date_str)
        os.makedirs(day_dir, exist_ok=True)
        
        # 1. Save JSON
        top3_path = os.path.join(day_dir, f"run_{run_id}_top3.json")
        ranking_path = os.path.join(day_dir, f"run_{run_id}_ranking.json")
        
        with open(top3_path, "w", encoding="utf-8") as f:
            json.dump(top3, f, indent=2, default=str)
            
        with open(ranking_path, "w", encoding="utf-8") as f:
            json.dump(ranking, f, indent=2, default=str)
            
        # 2. Save Markdown
        md_content = self._generate_markdown(top3, ranking, run_id, as_of)
        md_path = os.path.join(day_dir, f"run_{run_id}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        return md_path

    def _generate_markdown(self, top3: List[Dict], ranking: List[Dict], run_id: str, as_of: datetime) -> str:
        lines = []
        lines.append(f"# VN30 Short-term Trading Report")
        lines.append(f"**Run ID**: {run_id}")
        lines.append(f"**Date**: {as_of.strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        lines.append("> [!WARNING]")
        lines.append("> Disclaimer: This report is for technical analysis purposes only and does not constitute financial advice.")
        lines.append("")
        
        lines.append("## Top 3 Candidates")
        
        for item in top3:
            symbol = item['symbol']
            score = item['score_total']
            signal = item.get('signal', {})
            entry = signal.get('entry_zone', {})
            
            lines.append(f"### {symbol} (Score: {score})")
            lines.append(f"- **Entry Zone**: {entry.get('from')} - {entry.get('to')}")
            lines.append(f"- **Stop Loss**: {signal.get('stop_loss')}")
            lines.append(f"- **Targets**: TP1 {signal.get('take_profit_1')} | TP2 {signal.get('take_profit_2')}")
            
            # Breakdown
            bd = item.get('breakdown', {})
            lines.append(f"#### Score Breakdown")
            lines.append(f"- Trend: {bd.get('trend')} | Base: {bd.get('base')} | Vol: {bd.get('volume')} | Mom: {bd.get('momentum')} | Risk: {bd.get('risk')}")
            
            # Reasons (Mock logic for now, or use what's generated)
            reasons = signal.get('key_reasons', [])
            if not reasons:
                # Generate simple text from breakdown
                if bd.get('trend', 0) > 80: reasons.append("Strong Uptrend")
                if bd.get('base', 0) > 80: reasons.append("Tight Base / Squeeze")
                if bd.get('breakout', 0) > 80: reasons.append("Potential Breakout")
                if bd.get('volume', 0) > 80: reasons.append("High Relative Volume")
            
            if reasons:
                lines.append(f"#### Key Reasons")
                for r in reasons:
                    lines.append(f"- {r}")
            
            lines.append("")
            
        lines.append("## Full Ranking")
        lines.append("| Rank | Symbol | Score | Trend | Base | Vol | Mom | Risk |")
        lines.append("|---|---|---|---|---|---|---|---|")
        
        for idx, item in enumerate(ranking, 1):
            bd = item.get('breakdown', {})
            lines.append(f"| {idx} | {item['symbol']} | {item['score_total']} | {bd.get('trend')} | {bd.get('base')} | {bd.get('volume')} | {bd.get('momentum')} | {bd.get('risk')} |")
            
        return "\n".join(lines)
