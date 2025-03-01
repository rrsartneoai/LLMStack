import logging
from enum import Enum

from anthropic import AI_PROMPT, HUMAN_PROMPT, Anthropic
from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class CompletionsModel(str, Enum):
    CLAUDE_2 = "claude-2.0"
    CLAUDE_INSTANT = "claude-instant-1.2"
    CLAUDE_2_1 = "claude-2.1"

    def __str__(self):
        return self.value


class CompletionsInput(ApiProcessorSchema):
    prompt: str = Field(
        default="",
        description="The prompt that you want Claude to complete.",
    )


class CompletionsOutput(ApiProcessorSchema):
    completion: str = Field(
        default="",
        description="The generated completion.",
        json_schema_extra={"widget": "textarea"},
    )


class CompletionsConfiguration(ApiProcessorSchema):
    model: CompletionsModel = Field(
        default=CompletionsModel.CLAUDE_2,
        description="The model that will complete your prompt.",
        json_schema_extra={"advanced_parameter": False},
    )
    max_tokens_to_sample: int = Field(
        ge=1,
        default=256,
        description="The maximum number of tokens to generate before stopping.",
        json_schema_extra={"advanced_parameter": False},
    )
    temperature: float = Field(
        default=0.0,
        description="Amount of randomness injected into the response.",
        multiple_of=0.1,
        ge=0.0,
        le=1.0,
        json_schema_extra={"advanced_parameter": False},
    )


class CompletionsProcessor(
    ApiProcessorInterface[CompletionsInput, CompletionsOutput, CompletionsConfiguration],
):
    @staticmethod
    def name() -> str:
        return "Completions"

    @staticmethod
    def slug() -> str:
        return "completions"

    @staticmethod
    def description() -> str:
        return "Claude text completions"

    @staticmethod
    def provider_slug() -> str:
        return "anthropic"

    @classmethod
    def get_output_template(cls) -> OutputTemplate:
        return OutputTemplate(
            markdown="""{{completion}}""",
        )

    def process(self) -> dict:
        anthropic_provider_config = self.get_provider_config(model_slug=self._config.model.value)

        for chunk in Anthropic(api_key=anthropic_provider_config.api_key).completions.create(
            prompt=f"{HUMAN_PROMPT}\n{self._input.prompt}\n{AI_PROMPT}",
            max_tokens_to_sample=self._config.max_tokens_to_sample,
            model=self._config.model.value,
            temperature=self._config.temperature,
            stream=True,
        ):
            async_to_sync(self._output_stream.write)(
                CompletionsOutput(completion=chunk.completion),
            )

        output = self._output_stream.finalize()
        return output
