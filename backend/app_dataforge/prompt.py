from langchain_core.prompts import PromptTemplate

PROMPT_TEMPLATE_CLASSIFY = """Please categorize the following document:
"{content}"
Category ctype Range: {ctype_list}
Category auth Range: {auth_list}
Category status Range: {status_list}
Please respond directly in the form: {demo}, and reply in {language}
"""

PROMPT_CLASSIFY = PromptTemplate(
    input_variables=["content", "ctype_list", "auth_list", "status_list", "demo", "language"],
    template=PROMPT_TEMPLATE_CLASSIFY,
)

PROMPT_TEMPLATE_TITLE = """Please provide a title for the following content in ten words or less:
"{content}"
Please answer directly, and reply in {language}
"""

PROMPT_TITLE = PromptTemplate(
    input_variables=["content", "language"],
    template=PROMPT_TEMPLATE_TITLE,
)

PROMPT_TEMPLATE_COMPREHENSIVE = """Please analyze the following content and provide three aspects of information in {language}:
Content: "{content}"

1. Title (in ten words or less)
2. Category Classification:
   - Category (ctype) options: {ctype_list}
   - Authority (auth) options: {auth_list}
   - Status options: {status_list}
3. Summary (within 200 characters)

Please format your response as a JSON object like:
{
    "title": "brief title",
    "category": {
        "ctype": "chosen category",
        "atype": "chosen authority",
        "status": "chosen status"
    },
    "summary": "content summary"
}
"""

PROMPT_COMPREHENSIVE = PromptTemplate(
    input_variables=["content", "language", "ctype_list", "auth_list", "status_list"],
    template=PROMPT_TEMPLATE_COMPREHENSIVE,
)
