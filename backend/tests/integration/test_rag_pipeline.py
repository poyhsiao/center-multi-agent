import pytest


@pytest.mark.asyncio
async def test_knowledge_approval_workflow():
    """Knowledge approval transitions state correctly."""
    from app.services.knowledge_service import Knowledge, KnowledgeStatus

    k = Knowledge(title="Test", content="Content")
    k.submit_for_review()
    assert k.status == KnowledgeStatus.PENDING_REVIEW

    k.approve()
    assert k.status == KnowledgeStatus.APPROVED


@pytest.mark.asyncio
async def test_failover_chain_order():
    """Model failover tries models in correct order."""
    from app.services.llm_gateway import LLMGateway, TaskType

    gateway = LLMGateway()
    chain = gateway.get_failover_chain(TaskType.COMPLEX_REASONING)

    assert chain[0].name == "gpt-4o"
    assert chain[1].name == "claude-3-5-sonnet"
