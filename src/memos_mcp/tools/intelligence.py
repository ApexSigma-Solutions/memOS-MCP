"""
TN-400 / TN-OA-006: Intelligence Tool for memOS (Mirmir Logic Adapter)
Integrates the Mirmir Protocol into the memOS MCP Server.
"""

import os
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from neo4j import GraphDatabase, basic_auth

# Configure Logger
logger = logging.getLogger("memos.mcp.intelligence")

# --- DATA MODELS ---

class CodexCitation(BaseModel):
    """Represents a specific rule or constraint from the Codex."""
    rule_id: str = Field(..., description="The Unique ID of the Codex rule (e.g., 'RULE-001').")
    content: str = Field(..., description="The text of the constraint.")
    severity: str = Field(..., description="CRITICAL, WARNING, or INFO.")

class MirmirVerdict(BaseModel):
    """The formal judgment returned by the Intelligence Layer."""
    approved: bool = Field(..., description="Whether the plan is allowed to proceed.")
    risk_score: float = Field(..., description="0.0 (Safe) to 1.0 (Catastrophic).")
    reasoning: str = Field(..., description="Explanation of the verdict.")
    citations: List[CodexCitation] = Field(default_factory=list, description="Relevant Codex rules citation.")
    suggested_modifications: Optional[str] = Field(None, description="How to fix the plan if rejected.")

# --- NEO4J CONNECTION ---
# Looks for env vars, defaults to standard local ports if missing
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def get_db_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))

# --- CORE LOGIC ---

async def consult_mirmir(
    plan_text: str,
    intended_outcome: str,
    affected_entities: List[str] = []
) -> MirmirVerdict:
    """
    Consults the Omega KG 'Mirmir Protocol' to validate a proposed action plan.
    
    Use this tool BEFORE executing high-risk changes (deletions, refactors).
    It checks the live Codex for architectural constraints.
    
    Args:
        plan_text: The natural language description of the action.
        intended_outcome: The goal (e.g., "Clean up legacy code").
        affected_entities: List of filenames or node IDs.
        
    Returns:
        MirmirVerdict: Approval status and constraints.
    """
    logger.info(f"Consulting Mirmir on plan: {intended_outcome}")
    
    citations = []
    risk_score = 0.0
    rejection_reasons = []

    # 1. HARDCODED SAFETY NET (The "Prime Directives")
    # Matches Omega Core logic: Protect 'domain/linear' and 'omega_kg' structure.
    if any("omega_kg" in e or "domain/linear" in e for e in affected_entities) and ("delete" in plan_text.lower() or "remove" in plan_text.lower()):
        citations.append(CodexCitation(
            rule_id="SYS-LOCK-001",
            content="Stabilized Domains (Linear/Omega Core) are Read-Only for removal operations.",
            severity="CRITICAL"
        ))
        risk_score += 0.9
        rejection_reasons.append("Attempted modification of locked Omega domain.")

    # 2. DYNAMIC CODEX LOOKUP (Neo4j)
    driver = None
    try:
        driver = get_db_driver()
        with driver.session() as session:
            # Query active CodexRules
            query = """
            MATCH (r:CodexRule {status: 'ACTIVE'})
            RETURN r.id AS id, r.content AS content, r.severity AS severity, r.keywords AS keywords
            """
            result = session.run(query)
            
            for record in result:
                rule_keywords = record.get("keywords", [])
                if rule_keywords and any(k.lower() in plan_text.lower() for k in rule_keywords):
                    citations.append(CodexCitation(
                        rule_id=record["id"],
                        content=record["content"],
                        severity=record["severity"]
                    ))
                    if record["severity"] == "CRITICAL":
                        risk_score += 0.6
                        rejection_reasons.append(f"Violates {record['id']}")

    except Exception as e:
        logger.error(f"Failed to query Mirmir Cortex: {e}")
        # Soft fail: If DB is down, proceed with caution (Warning) unless hardcoded rules tripped.
        if risk_score == 0:
             citations.append(CodexCitation(
                rule_id="WARN-CONN",
                content="Intelligence Layer connection unstable. Proceed with caution.",
                severity="WARNING"
            ))
    finally:
        if driver:
            driver.close()

    # 3. VERDICT SYNTHESIS
    is_approved = risk_score < 0.7
    
    reason = "Plan approved."
    if not is_approved:
        reason = "Plan REJECTED via Mirmir Protocol. " + " ".join(rejection_reasons)
    elif citations:
        reason = "Plan Approved with Cautions."

    return MirmirVerdict(
        approved=is_approved,
        risk_score=min(risk_score, 1.0),
        reasoning=reason,
        citations=citations,
        suggested_modifications="Review citations and adjust scope." if not is_approved else None
    )