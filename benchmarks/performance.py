#!/usr/bin/env python3
"""
Performance benchmarks (FAANG-grade metrics)
Measures: latency, throughput, cache hit rate, cost
"""
import asyncio
import time
import statistics
from typing import List, Dict, Any
from rag.retrieve_async import search_async
from rag.cache import query_cache, embedding_cache, tool_cache

async def benchmark_retrieval(queries: List[str], iterations: int = 10) -> Dict[str, Any]:
    """
    Benchmark retrieval performance.
    
    Returns:
        {
            "p50_latency_ms": float,
            "p95_latency_ms": float,
            "p99_latency_ms": float,
            "mean_latency_ms": float,
            "cache_hit_rate": float,
            "queries_per_second": float
        }
    """
    latencies = []
    cache_hits = 0
    total_queries = 0
    
    # Clear cache for first run
    query_cache.clear()
    embedding_cache.clear()
    
    print(f"Benchmarking {len(queries)} queries, {iterations} iterations each...")
    
    # Warm-up (first iteration, no cache)
    for query in queries:
        await search_async(query)
    
    # Actual benchmarks
    for iteration in range(iterations):
        for query in queries:
            total_queries += 1
            start = time.time()
            
            cached = query_cache.get(query)
            if cached:
                cache_hits += 1
            
            await search_async(query)
            
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)
    
    latencies.sort()
    n = len(latencies)
    
    results = {
        "p50_latency_ms": latencies[int(n * 0.50)],
        "p95_latency_ms": latencies[int(n * 0.95)],
        "p99_latency_ms": latencies[int(n * 0.99)],
        "mean_latency_ms": statistics.mean(latencies),
        "std_latency_ms": statistics.stdev(latencies) if n > 1 else 0,
        "cache_hit_rate": cache_hits / total_queries if total_queries > 0 else 0,
        "queries_per_second": 1000 / statistics.mean(latencies) if latencies else 0,
        "total_queries": total_queries,
        "cache_hits": cache_hits
    }
    
    return results

async def benchmark_throughput(queries: List[str], concurrent: int = 10) -> Dict[str, Any]:
    """
    Benchmark throughput under concurrent load.
    
    Measures QPS before degradation.
    """
    print(f"Benchmarking throughput with {concurrent} concurrent requests...")
    
    async def single_request(query: str):
        start = time.time()
        await search_async(query)
        return time.time() - start
    
    start_total = time.time()
    
    # Run concurrent requests
    tasks = [single_request(query) for query in queries * concurrent]
    latencies = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_total
    total_requests = len(tasks)
    
    results = {
        "total_requests": total_requests,
        "total_time_seconds": total_time,
        "requests_per_second": total_requests / total_time,
        "mean_latency_ms": statistics.mean([l * 1000 for l in latencies]),
        "p95_latency_ms": sorted([l * 1000 for l in latencies])[int(len(latencies) * 0.95)]
    }
    
    return results

def print_benchmark_results(results: Dict[str, Any], title: str):
    """Print formatted benchmark results."""
    print("\n" + "=" * 70)
    print(f"BENCHMARK: {title}")
    print("=" * 70)
    print()
    
    if "p50_latency_ms" in results:
        print("Latency Percentiles:")
        print(f"  p50: {results['p50_latency_ms']:.2f} ms")
        print(f"  p95: {results['p95_latency_ms']:.2f} ms")
        print(f"  p99: {results['p99_latency_ms']:.2f} ms")
        print(f"  Mean: {results['mean_latency_ms']:.2f} ms (±{results.get('std_latency_ms', 0):.2f})")
        print()
    
    if "cache_hit_rate" in results:
        print("Cache Performance:")
        print(f"  Hit Rate: {results['cache_hit_rate']*100:.1f}%")
        print(f"  Hits: {results['cache_hits']}/{results['total_queries']}")
        print()
    
    if "queries_per_second" in results:
        print("Throughput:")
        print(f"  QPS: {results['queries_per_second']:.2f}")
        print()
    
    if "requests_per_second" in results:
        print("Concurrent Load:")
        print(f"  Total Requests: {results['total_requests']}")
        print(f"  Total Time: {results['total_time_seconds']:.2f}s")
        print(f"  RPS: {results['requests_per_second']:.2f}")
        print(f"  Mean Latency: {results['mean_latency_ms']:.2f} ms")
        print(f"  p95 Latency: {results['p95_latency_ms']:.2f} ms")
        print()

async def main():
    """Run all benchmarks."""
    test_queries = [
        "Explain BM25 keyword search in RAG systems",
        "What is hybrid retrieval?",
        "How does reranking work?",
        "What are dense vectors?",
        "Explain sparse retrieval",
    ]
    
    print("=" * 70)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 70)
    print()
    
    # Benchmark 1: Latency & Cache
    results1 = await benchmark_retrieval(test_queries, iterations=5)
    print_benchmark_results(results1, "Retrieval Latency & Cache Hit Rate")
    
    # Benchmark 2: Throughput
    results2 = await benchmark_throughput(test_queries, concurrent=10)
    print_benchmark_results(results2, "Concurrent Throughput")
    
    print("=" * 70)
    print("✅ Benchmarks complete")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
