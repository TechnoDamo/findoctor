"""vLLM benchmark script. Called by Makefile with URL, model, iterations, concurrency as args."""
import json
import statistics
import sys
import time
import urllib.request
import concurrent.futures

HEADER = "\033[1m"
CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
NC = "\033[0m"
SEP = "\u2500" * 72


def nonstream_request(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read())
            elapsed = time.time() - t0
            text = body["choices"][0]["message"].get("content", "")
            tokens = body.get("usage", {}).get("completion_tokens", 0)
    except Exception as e:
        return {"error": str(e), "elapsed": time.time() - t0}
    return {
        "elapsed": elapsed,
        "tokens": tokens,
        "tps": tokens / elapsed if elapsed > 0 else 0,
        "text": text[:60].replace("\n", " "),
    }


def streaming_ttft(url, payload):
    spayload = dict(payload, stream=True)
    data = json.dumps(spayload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    t0 = time.time()
    ttft = None
    total_tokens = 0
    text = ""
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            buf = b""
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line or not line.startswith(b"data: "):
                        continue
                    s = line[6:].decode("utf-8", errors="replace")
                    if s == "[DONE]":
                        break
                    try:
                        d = json.loads(s)
                        delta = d["choices"][0].get("delta", {})
                        c = delta.get("content", "")
                        if c and ttft is None:
                            ttft = time.time() - t0
                        if c:
                            text += c
                            total_tokens += 1
                    except Exception:
                        pass
            elapsed = time.time() - t0
    except Exception as e:
        return {"error": str(e), "elapsed": time.time() - t0, "ttft": None}
    return {
        "ttft": ttft,
        "elapsed": elapsed,
        "tokens": total_tokens,
        "tps": total_tokens / elapsed if elapsed > 0 else 0,
        "text": text[:40].replace("\n", " "),
    }


def main():
    url = sys.argv[1]
    model = sys.argv[2]
    iterations = int(sys.argv[3])
    concurrency = int(sys.argv[4])

    payload_seq = {
        "model": model,
        "messages": [{"role": "user", "content": "Explain briefly what inflation is in three sentences."}],
        "temperature": 0,
        "max_tokens": 150,
    }
    payload_short = {
        "model": model,
        "messages": [{"role": "user", "content": "Answer with one word: what is your name?"}],
        "temperature": 0,
        "max_tokens": 10,
    }

    print(f"{HEADER}Configuration{NC}")
    print(f"  Model:     {model}")
    print(f"  URL:       {url}")
    try:
        models_url = url.rsplit("/chat/", 1)[0] + "/models"
        resp = json.loads(urllib.request.urlopen(models_url, timeout=5).read())
        model_id = resp.get("data", [{}])[0].get("id", model)
        print(f"  Loaded as: {model_id}")
    except Exception:
        pass
    print(f"  Seq iter:  {iterations}")
    print(f"  Parallel:  {concurrency}")
    print()

    avg_ttft = None
    overall_tps = None
    seq_mean_elapsed = None
    conc_tps = None
    conc_wall_time = None

    print(f"{HEADER}{CYAN}1) Time-To-First-Token (TTFT) — 3 streaming requests{NC}")
    ttft_results = []
    for i in range(3):
        sys.stdout.write(f"  [{i+1}/3] ")
        sys.stdout.flush()
        r = streaming_ttft(url, payload_short)
        if "error" not in r and r["ttft"] is not None:
            print(f'TTFT={r["ttft"]*1000:.0f}ms  total={r["elapsed"]:.2f}s  {r["tokens"]}tok  "{r["text"]}"')
            ttft_results.append(r)
        else:
            print(f"{YELLOW}ERROR{NC}: {r.get('error', 'no TTFT data')}")
    if ttft_results:
        avg_ttft = statistics.mean(r["ttft"] for r in ttft_results)
        print(f"  Avg TTFT:  {avg_ttft*1000:.0f} ms ({avg_ttft:.3f}s)")

    print()
    print(f"{HEADER}{CYAN}2) Sequential throughput — {iterations} requests{NC}")
    print(f"  {SEP}")
    seq_results = []
    for i in range(iterations):
        sys.stdout.write(f"  [{i+1}/{iterations}] ")
        sys.stdout.flush()
        r = nonstream_request(url, payload_seq)
        if "error" in r:
            print(f'{YELLOW}ERROR{NC}: {r["error"]}')
        else:
            print(f'{r["elapsed"]:.2f}s  {r["tokens"]}tok  {r["tps"]:.1f} tok/s  "{r["text"]}"')
        seq_results.append(r)

    good = [r for r in seq_results if "error" not in r]
    if good:
        elapsed_list = [r["elapsed"] for r in good]
        tps_list = [r["tps"] for r in good]
        tokens_list = [r["tokens"] for r in good]
        total_tokens_all = sum(tokens_list)
        total_time_all = sum(elapsed_list)
        overall_tps = total_tokens_all / total_time_all if total_time_all > 0 else 0
        seq_mean_elapsed = statistics.mean(elapsed_list)
        print(f"  {SEP}")
        print(f"  {GREEN}Avg time:     {seq_mean_elapsed:.2f}s{NC}")
        print(f"  {GREEN}Min/Max time: {min(elapsed_list):.2f}s / {max(elapsed_list):.2f}s{NC}")
        print(f"  {GREEN}Avg tokens:   {statistics.mean(tokens_list):.1f}{NC}")
        print(f"  {GREEN}Avg tok/s:    {statistics.mean(tps_list):.1f}{NC}")
        print(f"  {GREEN}Throughput:   {overall_tps:.1f} tok/s{NC}")
        if len(elapsed_list) >= 2:
            print(f"  {GREEN}StdDev:       {statistics.stdev(elapsed_list):.2f}s{NC}")

    print()
    print(f"{HEADER}{CYAN}3) Parallel throughput — {concurrency} concurrent requests{NC}")
    print(f"  {SEP}")
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
        conc_results = list(ex.map(lambda _: nonstream_request(url, payload_seq), range(concurrency)))
    wall_time = time.time() - t0
    conc_wall_time = wall_time

    good_conc = [r for r in conc_results if "error" not in r]
    if good_conc:
        total_tokens_conc = sum(r["tokens"] for r in good_conc)
        conc_tps = total_tokens_conc / wall_time if wall_time > 0 else 0
        elapsed_conc = [r["elapsed"] for r in good_conc]
        ideal_single = statistics.mean(elapsed_conc) if elapsed_conc else 0
        speedup = ideal_single * concurrency / wall_time if wall_time > 0 else 0
        print(f"  {GREEN}Total tokens:     {total_tokens_conc}{NC}")
        print(f"  {GREEN}Wall time:        {wall_time:.2f}s{NC}")
        print(f"  {GREEN}Avg latency:      {statistics.mean(elapsed_conc):.2f}s{NC}")
        print(f"  {GREEN}Min/Max latency:  {min(elapsed_conc):.2f}s / {max(elapsed_conc):.2f}s{NC}")
        print(f"  {GREEN}Throughput:       {conc_tps:.1f} tok/s{NC}")
        print(f"  {GREEN}Speedup:          {speedup:.2f}x (ideal {concurrency:.1f}x){NC}")
        for i, r in enumerate(conc_results):
            if "error" in r:
                print(f'  [{i+1}] {YELLOW}ERROR{NC}: {r["error"]}')
            else:
                print(f'  [{i+1}] {r["elapsed"]:.2f}s  {r["tokens"]}tok  {r["tps"]:.1f} tok/s')

    print()
    print(f"  {SEP}")
    print(f"  {HEADER}BENCHMARK SUMMARY{NC}")
    if avg_ttft is not None:
        print(f"  TTFT (avg):            {avg_ttft*1000:.0f} ms")
    if overall_tps is not None and seq_mean_elapsed is not None:
        print(f"  Seq throughput:        {overall_tps:.1f} tok/s ({iterations} requests, avg {seq_mean_elapsed:.2f}s)")
    if conc_tps is not None and conc_wall_time is not None:
        print(f"  Parallel throughput:   {conc_tps:.1f} tok/s ({concurrency} concurrent, wall {conc_wall_time:.2f}s)")
    print(f"  {SEP}")


if __name__ == "__main__":
    main()
