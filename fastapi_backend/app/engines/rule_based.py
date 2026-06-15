import re
from typing import Literal, NamedTuple

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.base import SimulationEngine
from app.models.branch import Branch
from app.models.operations import Operation
from app.models.sales import Sales
from app.schemas.simulation import ComparisonEntry, LocationConditions, SimulationResult

FALLBACK_THRESHOLD = 5
EV_CORRECTION = 1.08
# Tier 3 (all-branch) and percentile queries are capped to prevent full-table scan DoS.
BRANCH_QUERY_LIMIT = 500

# Normalize metropolitan/special city designations for consistent address matching.
_METRO_RE = re.compile(r"(광역|특별자치|특별)시")


class _BranchMetrics(NamedTuple):
    branch_name: str
    area_sqm: float
    monthly_rent: float
    address: str
    avg_monthly_revenue: float
    avg_ops_cost: float
    total_units: int
    avg_rented_units: float


def extract_gu(address: str) -> str:
    m = re.search(r"\w+구", address)
    return m.group(0) if m else ""


def extract_si(address: str) -> str:
    # Normalize metropolitan designations so "인천광역시" → "인천시" for LIKE matching.
    normalized = _METRO_RE.sub("시", address)
    m = re.search(r"\w+시", normalized)
    return m.group(0) if m else ""


def _calc_verdict(percentile: float) -> Literal["추천", "검토필요", "비추천"]:
    # top 30% (≥70th pctile) → 추천, middle 30% → 검토필요, bottom 40% → 비추천
    if percentile >= 70.0:
        return "추천"
    if percentile >= 40.0:
        return "검토필요"
    return "비추천"


async def _query_branches(
    db: AsyncSession,
    area_min: float,
    area_max: float,
    rent_min: float,
    rent_max: float,
    addr_filter: str,
) -> list[Branch]:
    filters = [
        Branch.area_sqm.between(area_min, area_max),
        Branch.monthly_rent.between(rent_min, rent_max),
    ]
    if addr_filter:
        filters.append(Branch.address.like(f"%{addr_filter}%"))
    result = await db.execute(select(Branch).where(and_(*filters)))
    return list(result.scalars().all())


async def _fetch_metrics(db: AsyncSession, branch_names: list[str]) -> list[_BranchMetrics]:
    if not branch_names:
        return []

    monthly_rev_sq = (
        select(
            Sales.branch_name,
            func.extract("year", Sales.sale_date).label("yr"),
            func.extract("month", Sales.sale_date).label("mo"),
            func.sum(Sales.daily_revenue).label("monthly_rev"),
        )
        .where(Sales.branch_name.in_(branch_names))
        .group_by(Sales.branch_name, "yr", "mo")
        .subquery()
    )
    avg_rev_sq = (
        select(
            monthly_rev_sq.c.branch_name,
            func.avg(monthly_rev_sq.c.monthly_rev).label("avg_rev"),
        )
        .group_by(monthly_rev_sq.c.branch_name)
        .subquery()
    )

    avg_ops_sq = (
        select(
            Operation.branch_name,
            func.avg(
                func.coalesce(Operation.electricity_fee, 0) + func.coalesce(Operation.operating_cost, 0)
            ).label("avg_ops"),
            func.avg(Operation.rented_units).label("avg_rented"),
        )
        .where(Operation.branch_name.in_(branch_names))
        .group_by(Operation.branch_name)
        .subquery()
    )

    stmt = (
        select(
            Branch.branch_name,
            Branch.area_sqm,
            Branch.monthly_rent,
            Branch.address,
            Branch.total_units,
            func.coalesce(avg_rev_sq.c.avg_rev, 0.0).label("avg_rev"),
            func.coalesce(avg_ops_sq.c.avg_ops, 0.0).label("avg_ops"),
            func.coalesce(avg_ops_sq.c.avg_rented, 0.0).label("avg_rented"),
        )
        .select_from(Branch)
        .outerjoin(avg_rev_sq, Branch.branch_name == avg_rev_sq.c.branch_name)
        .outerjoin(avg_ops_sq, Branch.branch_name == avg_ops_sq.c.branch_name)
        .where(Branch.branch_name.in_(branch_names))
    )

    result = await db.execute(stmt)
    return [
        _BranchMetrics(
            branch_name=row.branch_name,
            area_sqm=float(row.area_sqm or 0),
            monthly_rent=float(row.monthly_rent or 0),
            address=row.address or "",
            avg_monthly_revenue=float(row.avg_rev or 0),
            avg_ops_cost=float(row.avg_ops or 0),
            total_units=int(row.total_units or 0),
            avg_rented_units=float(row.avg_rented or 0),
        )
        for row in result.all()
    ]


def _weighted_average(metrics: list[_BranchMetrics], gu: str, location: LocationConditions) -> tuple[float, float, float, float | None]:
    """Return (weighted_revenue, weighted_ops_cost, total_weight, weighted_occupancy_rate_pct)."""
    pairs: list[tuple[_BranchMetrics, float]] = []
    for m in metrics:
        area_sim = max(0.0, 1.0 - abs(m.area_sqm - location.area_sqm) / max(location.area_sqm, 1.0))
        rent_sim = max(0.0, 1.0 - abs(m.monthly_rent - location.monthly_rent) / max(location.monthly_rent, 1.0))
        # `gu and` guard prevents empty-string matching every address ("" in any_str is True)
        region_sim = 1.0 if gu and gu in m.address else 0.0
        weight = 0.45 * area_sim + 0.30 * rent_sim + 0.25 * region_sim
        pairs.append((m, max(weight, 1e-9)))

    total_w = sum(w for _, w in pairs)
    weighted_rev = sum(m.avg_monthly_revenue * w for m, w in pairs) / total_w
    weighted_ops = sum(m.avg_ops_cost * w for m, w in pairs) / total_w

    # Real occupancy rate from actual rented/total unit counts
    valid_occ = [(m, w) for m, w in pairs if m.total_units > 0 and m.avg_rented_units > 0]
    if valid_occ:
        valid_w = sum(w for _, w in valid_occ)
        weighted_occ: float | None = (
            sum((m.avg_rented_units / m.total_units) * w for m, w in valid_occ) / valid_w * 100.0
        )
    else:
        weighted_occ = None

    return weighted_rev, weighted_ops, total_w, weighted_occ


def _default_estimate(location: LocationConditions) -> SimulationResult:
    est_rev = location.monthly_rent * 2.0
    if location.ev_charging:
        est_rev *= EV_CORRECTION
    net = max(0.0, est_rev - location.monthly_rent - (location.monthly_maintenance or 0))
    return SimulationResult(
        estimated_monthly_revenue=round(est_rev, 2),
        occupancy_rate=65.0,
        net_profit=round(net, 2),
        percentile=50.0,
        verdict="검토필요",
        similar_branch_count=0,
        fallback_used=True,
    )


class RuleBasedEngine(SimulationEngine):
    async def predict(self, location: LocationConditions, db: AsyncSession) -> SimulationResult:
        gu = extract_gu(location.address)
        si = extract_si(location.address)

        fallback_used = False
        area_min1 = location.area_sqm * 0.7
        area_max1 = location.area_sqm * 1.3
        rent_min1 = location.monthly_rent * 0.7
        rent_max1 = location.monthly_rent * 1.3

        # Tier 1: ±30%, same 구 (skip if no 구 in address to avoid nationwide query)
        if gu:
            raw = await _query_branches(db, area_min1, area_max1, rent_min1, rent_max1, gu)
        else:
            raw = []

        # Tier 2: ±50%, same 시 — geographic expansion, not a data-quality fallback.
        # Does NOT set fallback_used; city-level similarity is still a valid geographic match.
        if len(raw) < FALLBACK_THRESHOLD:
            area_min2 = location.area_sqm * 0.5
            area_max2 = location.area_sqm * 1.5
            rent_min2 = location.monthly_rent * 0.5
            rent_max2 = location.monthly_rent * 1.5
            if si:
                raw = await _query_branches(db, area_min2, area_max2, rent_min2, rent_max2, si)
            else:
                raw = []

        # Tier 3: all branches — true data-quality fallback, triggers warning banner.
        if len(raw) < FALLBACK_THRESHOLD:
            result = await db.execute(select(Branch).limit(BRANCH_QUERY_LIMIT))
            raw = list(result.scalars().all())
            fallback_used = True

        if not raw:
            return _default_estimate(location)

        branch_names = [b.branch_name for b in raw]
        metrics = await _fetch_metrics(db, branch_names)

        with_revenue = [m for m in metrics if m.avg_monthly_revenue > 0]
        effective = with_revenue if with_revenue else metrics
        if not effective:
            return _default_estimate(location)

        weighted_rev, weighted_ops, _, weighted_occ = _weighted_average(effective, gu, location)

        # Guard against zero/negative revenue (all branches have no sales data)
        if weighted_rev <= 0:
            return _default_estimate(location)

        if location.ev_charging:
            weighted_rev *= EV_CORRECTION

        # Occupancy rate: use real rented/total unit ratio when available;
        # fall back to revenue proxy (revenue / 2×rent) if unit data is missing.
        if weighted_occ is not None:
            occupancy_rate = min(99.0, max(0.0, weighted_occ))
        else:
            occupancy_rate = min(99.0, max(0.0, weighted_rev / max(location.monthly_rent * 2.0, 1.0) * 100.0))

        # Net profit: revenue minus all monthly costs for this location.
        # weighted_ops covers peer branches' electricity + operating costs (not rent, which is separate).
        net_profit = (
            weighted_rev
            - location.monthly_rent
            - (location.monthly_maintenance or 0.0)
            - weighted_ops
        )

        # Percentile: fraction of all branches with revenue strictly below predicted value.
        # Using strict < (not <=) gives the standard "percent of population below" definition.
        all_names_res = await db.execute(select(Branch.branch_name).limit(BRANCH_QUERY_LIMIT))
        all_names = list(all_names_res.scalars().all())
        all_metrics = await _fetch_metrics(db, all_names)
        all_revenues = [m.avg_monthly_revenue for m in all_metrics if m.avg_monthly_revenue > 0]

        if all_revenues:
            rank = sum(1 for r in all_revenues if r < weighted_rev)
            percentile = rank / len(all_revenues) * 100.0
        else:
            percentile = 50.0

        if fallback_used:
            comparison_data = []
        else:
            top5 = sorted(effective, key=lambda m: m.avg_monthly_revenue, reverse=True)[:5]
            comparison_data = [
                ComparisonEntry(
                    name=(m.branch_name[:12] + "…" if len(m.branch_name) > 12 else m.branch_name),
                    monthly_revenue=round(m.avg_monthly_revenue, 2),
                )
                for m in top5
            ]

        return SimulationResult(
            estimated_monthly_revenue=round(weighted_rev, 2),
            occupancy_rate=round(occupancy_rate, 2),
            net_profit=round(net_profit, 2),
            percentile=round(percentile, 2),
            verdict=_calc_verdict(percentile),
            similar_branch_count=len(effective),
            fallback_used=fallback_used,
            comparison_data=comparison_data,
        )
