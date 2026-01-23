#!/usr/bin/env python3
"""
evaluate-answers.py - Evaluate answers using LLM-as-judge scoring (0-5).

Usage:
  python evaluate-answers.py --model gpt-4o --input-folder answers/ --output-folder scores/
"""

import os, sys, json, time, argparse
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

UNKNOWN = '[UNKNOWN]'


def load_api_keys(keys_file: Path) -> dict:
    keys = {}
    if not keys_file.exists():
        print(f"[ERROR] Keys file not found: {keys_file}", file=sys.stderr)
        sys.exit(1)
    with open(keys_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                keys[key.strip()] = value.strip()
    return keys


def detect_provider(model_id: str) -> str:
    model_lower = model_id.lower()
    if model_lower.startswith(('gpt-', 'o1-', 'o3-')):
        return 'openai'
    if model_lower.startswith('claude'):
        return 'anthropic'
    print(f"[ERROR] Cannot detect provider for model: {model_id}", file=sys.stderr)
    sys.exit(1)


def retry_with_backoff(fn, retries=3, backoff=(1, 2, 4)):
    last_error = None
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                wait = backoff[attempt] if attempt < len(backoff) else backoff[-1]
                time.sleep(wait)
    raise last_error


def log(worker_id: int, current: int, total: int, msg: str):
    print(f"[ worker {worker_id + 1} ] [ {current} / {total} ] {msg}", file=sys.stderr)


def atomic_write_json(path: Path, data: dict, lock: Lock):
    tmp_path = path.with_suffix('.tmp')
    with lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        tmp_path.rename(path)


def create_openai_client(keys: dict):
    from openai import OpenAI
    api_key = keys.get('OPENAI_API_KEY')
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found", file=sys.stderr)
        sys.exit(1)
    return OpenAI(api_key=api_key)


def create_anthropic_client(keys: dict):
    from anthropic import Anthropic
    api_key = keys.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEY not found", file=sys.stderr)
        sys.exit(1)
    return Anthropic(api_key=api_key)


def call_openai(client, model: str, prompt: str):
    # Use max_completion_tokens for newer models (gpt-5, o1, o3), max_tokens for older
    token_param = "max_completion_tokens" if any(x in model for x in ['gpt-5', 'o1-', 'o3-']) else "max_tokens"
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        **{token_param: 1024}
    )
    return {
        "text": response.choices[0].message.content,
        "usage": {"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens},
        "model": response.model
    }


def call_anthropic(client, model: str, prompt: str):
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return {
        "text": response.content[0].text,
        "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
        "model": response.model
    }


DEFAULT_JUDGE_PROMPT = """You are an evaluation judge. Score how well the model answer matches the reference answer.

Scoring criteria (0-5):
- 5: Perfect match - contains all key information, no errors
- 4: Good - minor omissions or phrasing differences, core facts correct
- 3: Acceptable - some key information present, some missing
- 2: Poor - significant errors or omissions, partially correct
- 1: Very poor - mostly incorrect or irrelevant
- 0: Wrong - completely incorrect or no relevant content

Question: {question}
Reference Answer: {reference_answer}
Model Answer: {model_answer}

Respond with ONLY a JSON object:
```json
{{"score": <0-5>, "rationale": "<brief explanation>"}}
```
"""


def build_judge_prompt(question: str, reference_answer: str, model_answer: str, custom_prompt: str = None) -> str:
    template = custom_prompt or DEFAULT_JUDGE_PROMPT
    return template.format(
        question=question,
        reference_answer=reference_answer,
        model_answer=model_answer
    )


def extract_json_from_response(text: str) -> dict:
    """Extract JSON object from response."""
    text = text.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        start = 1 if lines[0].startswith('```') else 0
        end = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == '```':
                end = i
                break
        text = '\n'.join(lines[start:end])
    
    return json.loads(text)


def process_answer(worker_id: int, a_idx: int, total: int, answer: dict,
                   args, client, provider: str, results: list, lock: Lock):
    question = answer.get("question", "")
    reference = answer.get("reference_answer", "")
    model_answer = answer.get("model_answer", "")
    
    log(worker_id, a_idx, total, f"Evaluating: {question[:50]}...")
    
    try:
        prompt = build_judge_prompt(question, reference, model_answer, args.judge_prompt)
        
        if provider == 'openai':
            result = retry_with_backoff(lambda: call_openai(client, args.model, prompt))
        else:
            result = retry_with_backoff(lambda: call_anthropic(client, args.model, prompt))
        
        evaluation = extract_json_from_response(result["text"])
        score = evaluation.get("score", 0)
        rationale = evaluation.get("rationale", "")
        
        score_data = {
            "question": question,
            "category": answer.get("category", ""),
            "reference_answer": reference,
            "model_answer": model_answer,
            "score": score,
            "rationale": rationale,
            "passed": score >= args.pass_threshold,
            "judge_model": result["model"],
            "source_file": answer.get("source_file", ""),
            "answer_model": answer.get("model", "")
        }
        
        with lock:
            results.append(score_data)
        
        status = "PASS" if score >= args.pass_threshold else "FAIL"
        log(worker_id, a_idx, total, f"Score: {score}/5 [{status}]")
        
    except Exception as e:
        log(worker_id, a_idx, total, f"ERROR: {e}")


def parse_args():
    parser = argparse.ArgumentParser(description='Evaluate answers using LLM-as-judge scoring.')
    parser.add_argument('--model', required=True, help='Judge model ID')
    parser.add_argument('--input-folder', type=Path, required=True, help='Folder with answer JSON files')
    parser.add_argument('--output-folder', type=Path, required=True, help='Output folder for scores')
    parser.add_argument('--method', choices=['llm', 'openai-eval'], default='llm', 
                        help='Evaluation method: llm (LLM-as-judge) or openai-eval (OpenAI Eval API)')
    parser.add_argument('--judge-prompt', type=str, help='Custom judge prompt (use {question}, {reference_answer}, {model_answer})')
    parser.add_argument('--pass-threshold', type=int, default=4, help='Pass threshold score (default: 4)')
    parser.add_argument('--workers', type=int, default=4, help='Parallel workers (default: 4)')
    parser.add_argument('--keys-file', type=Path, default=Path('.env'), help='API keys file')
    parser.add_argument('--clear-folder', action='store_true', help='Clear output folder before processing')
    return parser.parse_args()


def main():
    args = parse_args()
    
    if args.method == 'openai-eval':
        print("[ERROR] OpenAI Eval API method not yet implemented. Use --method llm", file=sys.stderr)
        sys.exit(1)
    
    if args.clear_folder and args.output_folder.exists():
        import shutil
        shutil.rmtree(args.output_folder)
        print(f"Cleared output folder: {args.output_folder}", file=sys.stderr)
    
    args.output_folder.mkdir(parents=True, exist_ok=True)
    
    keys = load_api_keys(args.keys_file)
    provider = detect_provider(args.model)
    
    if not args.input_folder.exists():
        print(f"[ERROR] Input folder not found: {args.input_folder}", file=sys.stderr)
        sys.exit(1)
    
    all_answers = []
    for f in args.input_folder.iterdir():
        if f.is_file() and f.suffix.lower() == '.json':
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                answers = data.get("answers", [])
                all_answers.extend(answers)
            except Exception as e:
                print(f"[WARN] Could not load {f}: {e}", file=sys.stderr)
    
    if not all_answers:
        print("[ERROR] No answers found in input folder", file=sys.stderr)
        sys.exit(1)
    
    print(f"Evaluating {len(all_answers)} answers with {args.workers} workers", file=sys.stderr)
    print(f"Judge model: {args.model}, Pass threshold: {args.pass_threshold}", file=sys.stderr)
    
    if provider == 'openai':
        client = create_openai_client(keys)
    else:
        client = create_anthropic_client(keys)
    
    results = []
    lock = Lock()
    
    args.output_folder.mkdir(parents=True, exist_ok=True)
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        for idx, answer in enumerate(all_answers, 1):
            worker_id = (idx - 1) % args.workers
            future = executor.submit(process_answer, worker_id, idx, len(all_answers), answer,
                                     args, client, provider, results, lock)
            futures[future] = answer
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"[ERROR] {e}", file=sys.stderr)
    
    passed = sum(1 for r in results if r.get("passed"))
    failed = len(results) - passed
    avg_score = sum(r.get("score", 0) for r in results) / len(results) if results else 0
    
    output = {
        "judge_model": args.model,
        "pass_threshold": args.pass_threshold,
        "total_evaluated": len(results),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / len(results) * 100, 1) if results else 0,
        "average_score": round(avg_score, 2),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "scores": results
    }
    
    output_file = args.output_folder / f"scores_{args.model.replace('/', '_')}.json"
    output_file.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')
    
    print(f"\nResults: {passed}/{len(results)} passed ({output['pass_rate']}%), avg score: {avg_score:.2f}", file=sys.stderr)
    print(f"Output: {output_file}", file=sys.stderr)


if __name__ == '__main__':
    main()
