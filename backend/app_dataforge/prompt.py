from langchain_core.prompts import PromptTemplate

PROMPT_TEMPLATE_CLASSIFY = """Please categorize the following document:
"{content}"
Category ctype Range: {ctype_list}
Category auth Range: {auth_list}
Category status Range: {status_list}
Please respond directly in the form: {demo}
"""

PROMPT_CLASSIFY = PromptTemplate(
    input_variables=["content", "ctype_list", "auth_list", "status_list", "demo"],
    template=PROMPT_TEMPLATE_CLASSIFY,
)

PROMPT_TEMPLATE_TITLE = """Please provide a title for the following content in ten words or less:
"{content}"
Please answer directly, in the format: "{demo}"
"""

PROMPT_TITLE = PromptTemplate(
    input_variables=["content", "demo"],
    template=PROMPT_TEMPLATE_TITLE,
)
