SUMMARY_THRESHOLD_PERCENT = 75  # % of MAX_CONTEXT_TOKENS that reveals the Summarize button
MAX_CONTEXT_TOKENS = 32768      # matches qwen3:1.7b's configured num_ctx (see llm_util.py) - verified live
                                 # this is the largest tier tested that still completes reliably on the
                                 # 4GB RTX 3050 (partial CPU offload, ~5.4GB total, ~56%/44% CPU/GPU split)
