#!/usr/bin/env python3
"""Quick test script for Phase 5 chat backend.

This script tests the chat functionality without needing the frontend.
"""

import os
import sys
from pathlib import Path

# Disable tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv  # noqa: E402

load_dotenv(project_root / ".env")

from llm_engine.chat_model import ChatModel  # noqa: E402


def test_chat_general():
    """Test general CVE chat."""
    print("\n" + "=" * 60)
    print("TEST 1: General CVE Chat")
    print("=" * 60)

    try:
        chat = ChatModel()
        print(f"✓ ChatModel initialized: {chat}")

        query = "What are SQL injection vulnerabilities?"
        print(f"\nQuery: {query}")
        print("\nResponse:")
        print("-" * 60)

        response = chat.chat_general(query=query, top_k=3)
        print(response)

        print("\n" + "-" * 60)
        print("✓ General chat test passed")

        # Show usage stats
        stats = chat.get_usage_stats()
        print("\nUsage Stats:")
        print(f"  Input tokens: {stats['total_input_tokens']}")
        print(f"  Output tokens: {stats['total_output_tokens']}")
        if "estimated_cost_usd" in stats:
            print(f"  Estimated cost: ${stats['estimated_cost_usd']:.4f}")

        return True

    except Exception as e:
        print(f"❌ General chat test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_chat_streaming():
    """Test streaming chat."""
    print("\n" + "=" * 60)
    print("TEST 2: Streaming Chat")
    print("=" * 60)

    try:
        chat = ChatModel()

        query = "What is a CVSS score?"
        print(f"\nQuery: {query}")
        print("\nStreaming Response:")
        print("-" * 60)

        response_stream = chat.chat_general(query=query, top_k=3, stream=True)

        full_response = []
        for chunk in response_stream:
            print(chunk, end="", flush=True)
            full_response.append(chunk)

        print("\n" + "-" * 60)
        print("✓ Streaming chat test passed")
        print(f"  Total response length: {len(''.join(full_response))} characters")

        return True

    except Exception as e:
        print(f"❌ Streaming chat test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PHASE 5 CHAT BACKEND TESTS")
    print("=" * 60)

    results = []

    # Test 1: General chat
    results.append(("General Chat", test_chat_general()))

    # Test 2: Streaming chat
    results.append(("Streaming Chat", test_chat_streaming()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
