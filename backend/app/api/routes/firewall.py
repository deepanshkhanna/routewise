"""Firewall policy APIs (isolated lab; never host Windows firewall)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.firewall import (
    FirewallRuleCreate,
    FirewallRuleOut,
    FirewallStatus,
    FirewallTestRequest,
    FirewallTestResult,
)
from app.services.firewall_service import FirewallService

router = APIRouter(tags=["firewall"])


@router.get(
    "/api/networks/{network_id}/firewall/status",
    response_model=FirewallStatus,
)
def firewall_status(network_id: int, db: Session = Depends(get_db)) -> FirewallStatus:
    try:
        return FirewallService(db).status(network_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/api/networks/{network_id}/firewall/rules",
    response_model=list[FirewallRuleOut],
)
def list_rules(network_id: int, db: Session = Depends(get_db)) -> list[FirewallRuleOut]:
    try:
        rules = FirewallService(db).list_rules(network_id)
        return [FirewallRuleOut.model_validate(r) for r in rules]
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/api/networks/{network_id}/firewall/rules",
    response_model=FirewallRuleOut,
    status_code=201,
)
def create_rule(
    network_id: int,
    payload: FirewallRuleCreate,
    db: Session = Depends(get_db),
) -> FirewallRuleOut:
    try:
        rule = FirewallService(db).create_rule(network_id, payload)
        return FirewallRuleOut.model_validate(rule)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete(
    "/api/networks/{network_id}/firewall/rules/{rule_id}",
    status_code=204,
)
def delete_rule(network_id: int, rule_id: int, db: Session = Depends(get_db)) -> None:
    try:
        FirewallService(db).delete_rule(network_id, rule_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/api/networks/{network_id}/firewall/rules/{rule_id}/enable",
    response_model=FirewallRuleOut,
)
def enable_rule(network_id: int, rule_id: int, db: Session = Depends(get_db)) -> FirewallRuleOut:
    try:
        rule = FirewallService(db).set_enabled(network_id, rule_id, True)
        return FirewallRuleOut.model_validate(rule)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/api/networks/{network_id}/firewall/rules/{rule_id}/disable",
    response_model=FirewallRuleOut,
)
def disable_rule(network_id: int, rule_id: int, db: Session = Depends(get_db)) -> FirewallRuleOut:
    try:
        rule = FirewallService(db).set_enabled(network_id, rule_id, False)
        return FirewallRuleOut.model_validate(rule)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/api/networks/{network_id}/firewall/test",
    response_model=FirewallTestResult,
)
def test_policy(
    network_id: int,
    payload: FirewallTestRequest,
    db: Session = Depends(get_db),
) -> FirewallTestResult:
    try:
        return FirewallService(db).test(network_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/networks/{network_id}/firewall/apply")
def apply_firewall(network_id: int, db: Session = Depends(get_db)) -> dict:
    """Push SQLite policies into isolated lab fw1 nftables (never host firewall)."""
    try:
        return FirewallService(db).apply_to_lab(network_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
