"""
プロファイリングモジュール
各処理の実行時間を測定・記録する機能を提供
"""
import time
import functools
from typing import Dict, List, Optional
from collections import defaultdict
import streamlit as st


class PerformanceProfiler:
    """パフォーマンスプロファイラー"""
    
    def __init__(self):
        self.timings: Dict[str, List[float]] = defaultdict(list)
        self.current_timings: Dict[str, float] = {}
        self.enabled = True
    
    def start(self, name: str) -> None:
        """処理の開始時刻を記録"""
        if self.enabled:
            self.current_timings[name] = time.time()
    
    def end(self, name: str) -> float:
        """処理の終了時刻を記録し、実行時間を返す"""
        if not self.enabled:
            return 0.0
        
        if name not in self.current_timings:
            return 0.0
        
        elapsed = time.time() - self.current_timings[name]
        self.timings[name].append(elapsed)
        del self.current_timings[name]
        return elapsed
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """統計情報を取得"""
        stats = {}
        for name, times in self.timings.items():
            if times:
                stats[name] = {
                    'count': len(times),
                    'total': sum(times),
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'latest': times[-1] if times else 0.0
                }
        return stats
    
    def get_summary(self) -> str:
        """サマリーを取得"""
        stats = self.get_stats()
        if not stats:
            return "実行時間データがありません。"
        
        lines = ["## ⏱️ 処理時間分析\n"]
        lines.append("| 処理名 | 実行回数 | 合計時間 | 平均時間 | 最小時間 | 最大時間 | 最新時間 |")
        lines.append("|--------|----------|----------|----------|----------|----------|----------|")
        
        # 合計時間でソート
        sorted_stats = sorted(stats.items(), key=lambda x: x[1]['total'], reverse=True)
        
        for name, stat in sorted_stats:
            lines.append(
                f"| {name} | {stat['count']}回 | "
                f"{stat['total']:.2f}秒 | {stat['average']:.2f}秒 | "
                f"{stat['min']:.2f}秒 | {stat['max']:.2f}秒 | {stat['latest']:.2f}秒 |"
            )
        
        # 合計時間も表示
        total_time = sum(s['total'] for s in stats.values())
        lines.append(f"\n**総実行時間: {total_time:.2f}秒**")
        
        return "\n".join(lines)
    
    def reset(self) -> None:
        """統計をリセット"""
        self.timings.clear()
        self.current_timings.clear()


# グローバルプロファイラーインスタンス
_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler:
    """プロファイラーインスタンスを取得"""
    return _profiler


def profile(func):
    """デコレータ：関数の実行時間を測定"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = get_profiler()
        func_name = f"{func.__module__}.{func.__name__}"
        profiler.start(func_name)
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = profiler.end(func_name)
            if elapsed > 1.0:  # 1秒以上かかった場合はログ出力
                print(f"[PROFILE] {func_name}: {elapsed:.2f}秒")
    return wrapper


def time_block(name: str):
    """コンテキストマネージャー：ブロックの実行時間を測定"""
    class TimeBlock:
        def __init__(self, name: str):
            self.name = name
            self.profiler = get_profiler()
        
        def __enter__(self):
            self.profiler.start(self.name)
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed = self.profiler.end(self.name)
            # すべての処理時間をターミナルに出力
            print(f"[PROFILE] {self.name}: {elapsed:.2f}秒")
            return False
    
    return TimeBlock(name)

