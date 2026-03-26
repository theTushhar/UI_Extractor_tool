import json
import logging

import openai


logger = logging.getLogger(__name__)


def generate_locators(dom_snippet: str, user_goal: str, api_key: str, model_name: str):
    """
    Generates locators using an OpenAI model based on the cleaned DOM and user goal.
    """
    logger.info(
        "Generating locators | model=%s | goal_preview=%s | dom_length=%s | api_key_present=%s",
        model_name,
        user_goal[:80],
        len(dom_snippet),
        bool(api_key),
    )
    openai.api_key = api_key

    prompt = f"""
You are an expert SDET (Software Development Engineer in Test).
Here is the CLEANED HTML of a webpage:
```html
{dom_snippet[:30000]}
```

USER GOAL: {user_goal}

Task:
1. Analyze the HTML to find the elements requested.
2. Generate ROBUST locators for THREE frameworks:
   - **Playwright**: Prefer user-facing locators (getByRole, getByLabel).
   - **Selenium**: Prefer 'By.id', 'By.cssSelector', or 'By.xpath'.
   - **Cypress**: Prefer 'cy.get()'. Use 'data-cy' or 'data-test' if available. Avoid XPath for Cypress.

3. Return a JSON array. Each object in the array should have the following keys:
   - `elementName`: (string) A descriptive name for the element.
   - `cssSelector`: (string) A CSS selector for the element.
   - `xpathSelector`: (string) An XPath selector for the element.
   - `playwrightLocator`: (string) A Playwright-specific locator.
   - `seleniumLocator`: (string) A Selenium-specific locator.
   - `cypressLocator`: (string) A Cypress-specific locator.
   - `reasoning`: (string) Explanation for the chosen locators.
"""
    try:
        logger.debug("Calling OpenAI chat completions API")
        response = openai.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert SDET (Software Development Engineer in Test) tasked with generating robust UI locators.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        logger.debug("OpenAI response content present: %s", bool(content))
        if content:
            parsed_content = json.loads(content)
            logger.debug("Parsed OpenAI response keys: %s", list(parsed_content) if isinstance(parsed_content, dict) else type(parsed_content).__name__)
            if isinstance(parsed_content, dict):
                for key, value in parsed_content.items():
                    if isinstance(value, list):
                        logger.info("Returning locators from response key: %s", key)
                        return value

            if isinstance(parsed_content, list):
                logger.info("Returning top-level list of locators")
                return parsed_content

            raise ValueError("AI response did not contain a list of locators in the expected format.")

        raise ValueError("No content received from AI.")

    except openai.APIError:
        logger.exception("OpenAI API Error while generating locators")
        raise
    except json.JSONDecodeError:
        logger.exception("JSON decode error while parsing locator response")
        raise
    except Exception:
        logger.exception("Unexpected error while generating locators")
        raise
