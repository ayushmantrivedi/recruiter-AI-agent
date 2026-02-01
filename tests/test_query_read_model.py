"""
Query Read Model Tests
Verifies API responses don't access non-existent DB fields
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from app.services.pipeline import recruiter_pipeline
from app.database import SessionLocal, Query, Lead

@pytest.mark.asyncio
async def test_query_status_returns_leads():
    """Verify get_query_status returns leads without errors."""
    query_text = "python developer"
    query_id = str(uuid.uuid4())
    
    # Create query and leads
    db = SessionLocal()
    try:
        query_record = Query(
            id=query_id,
            recruiter_id="test",
            query_text=query_text,
            processing_status="completed",
            created_at=datetime.utcnow()
        )
        db.add(query_record)
        
        # Add test lead
        lead = Lead(
            query_id=query_id,
            company_name="Test Corp",
            score=85.0,
            confidence=0.85,
            reasons=["test reason"]
        )
        db.add(lead)
        db.commit()
    finally:
        db.close()
    
    # Get query status
    result = await recruiter_pipeline.get_query_status(query_id)
    
    assert result is not None
    assert result["status"] == "completed"
    assert "leads" in result
    assert len(result["leads"]) > 0
    
    # Verify lead structure
    lead_data = result["leads"][0]
    assert "company" in lead_data
    assert "score" in lead_data
    assert "confidence" in lead_data
    assert "reasons" in lead_data
    # evidence_count should NOT be present
    assert "evidence_count" not in lead_data

def test_no_evidence_count_in_lead_model():
    """Verify Lead model doesn't have evidence_count attribute."""
    from app.database import Lead
    
    # Create a test lead
    lead = Lead(
        query_id="test-id",
        company_name="Test",
        score=80.0,
        confidence=0.8,
        reasons=[]
    )
    
    # Verify evidence_count doesn't exist
    assert not hasattr(lead, "evidence_count"), \
        "Lead model should not have evidence_count attribute"

@pytest.mark.asyncio
async def test_api_response_serialization():
    """Verify API responses can be serialized without errors."""
    import json
    
    query_text = "backend engineer"
    query_id = str(uuid.uuid4())
    
    # Create query and lead
    db = SessionLocal()
    try:
        query_record = Query(
            id=query_id,
            recruiter_id="test",
            query_text=query_text,
            processing_status="completed",
            created_at=datetime.utcnow()
        )
        db.add(query_record)
        
        lead = Lead(
            query_id=query_id,
            company_name="Serialization Test Corp",
            score=90.0,
            confidence=0.9,
            reasons=["reason 1", "reason 2"]
        )
        db.add(lead)
        db.commit()
    finally:
        db.close()
    
    # Get query status
    result = await recruiter_pipeline.get_query_status(query_id)
    
    # Verify it can be serialized to JSON
    try:
        json_str = json.dumps(result, default=str)
        assert len(json_str) > 0
    except Exception as e:
        pytest.fail(f"Failed to serialize API response: {e}")

@pytest.mark.asyncio
async def test_end_to_end_query_and_retrieve():
    """Integration test: Create query, process, retrieve results."""
    query_text = "senior data scientist in Mumbai"
    query_id = str(uuid.uuid4())
    
    # Create query record
    db = SessionLocal()
    try:
        query_record = Query(
            id=query_id,
            recruiter_id="integration-test",
            query_text=query_text,
            processing_status="processing",
            created_at=datetime.utcnow()
        )
        db.add(query_record)
        db.commit()
    finally:
        db.close()
    
    # Process query
    result = await recruiter_pipeline.process_recruiter_query(
        query_text,
        recruiter_id="integration-test",
        query_id=query_id
    )
    
    assert result["status"] == "completed"
    
    # Retrieve query status
    status = await recruiter_pipeline.get_query_status(query_id)
    
    assert status is not None
    assert status["status"] == "completed"
    assert "leads" in status
    
    # Verify all leads have required fields
    for lead in status["leads"]:
        assert "company" in lead
        assert "score" in lead
        assert "confidence" in lead
        # Should NOT have evidence_count
        assert "evidence_count" not in lead
