import pytest

def test_select_model_complex_reasoning():
    """Complex reasoning task selects GPT-4o."""
    from app.services.llm_gateway import LLMGateway, TaskType

    gateway = LLMGateway()
    model = gateway.select_model(TaskType.COMPLEX_REASONING)

    assert model.name == "gpt-4o"
    assert model.supports_reasoning == True

def test_select_model_general():
    """General task selects GPT-4o-mini."""
    from app.services.llm_gateway import LLMGateway, TaskType

    gateway = LLMGateway()
    model = gateway.select_model(TaskType.GENERAL)

    assert model.name == "gpt-4o-mini"
    assert model.cost_tier == "medium"

def test_get_failover_chain():
    """Failover chain returns all models in priority order."""
    from app.services.llm_gateway import LLMGateway, TaskType

    gateway = LLMGateway()
    chain = gateway.get_failover_chain(TaskType.COMPLEX_REASONING)

    assert len(chain) == 2
    assert chain[0].name == "gpt-4o"
    assert chain[1].name == "claude-3-5-sonnet"

def test_model_config_attributes():
    """Model configs have correct attributes."""
    from app.services.llm_gateway import LLMGateway

    gateway = LLMGateway()
    gpt4o = gateway.MODELS["gpt-4o"]

    assert gpt4o.provider == "openai"
    assert gpt4o.context_window == 128000
    assert gpt4o.supports_reasoning == True
