"""直接调试 SSE 流内容"""
import asyncio
import json
import httpx

API = "http://127.0.0.1:8000/api/query"

async def test_sse(query: str):
    print(f"\n{'='*60}")
    print(f"测试: {query}")
    print('='*60)

    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST", API,
            json={"query": query, "context": {"user_id": "debug_sse", "session_id": f"debug_{id(query)}"}},
        ) as resp:
            buffer = ""
            async for chunk in resp.aiter_text():
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue
                    try:
                        pkt = json.loads(line[5:].strip())
                        ct = pkt.get("content", {}).get("contentType", "")
                        kind = pkt.get("content", ).get("kind", "")
                        text = pkt.get("content", {}).get("text", "")
                        ask = pkt.get("is_ask_user", False)
                        short = text[:80] if text else ""
                        print(f"  [{ct}] kind={kind} ask={ask} | {short}")
                    except:
                        print(f"  [RAW] {line[:100]}")

async def main():
    await test_sse("你好，今天天气真不错")

asyncio.run(main())
