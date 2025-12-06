RISK_VERDICT_TEMPLATE = """
Based on your analysis, provide a structured security verdict. Use the following format strictly:

VERDICT: [CRITICAL / HIGH / MEDIUM / LOW / VERY LOW]
REASONING: [Explain the specific tactics detected, e.g., 'False Urgency' or 'Unusual Sender Address'.]
ACTIONABLE_ADVICE: [Provide one to three concrete steps the user should take immediately.]
"""

TOOL_RUN_SUCCESS_TEMPLATE = """
The tool execution is complete. Use the provided information (TOOL_RESULT) to formulate a clear, safe verdict for the user.
TOOL_RESULT: {tool_result}
"""