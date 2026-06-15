from typing import Literal, Optional

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_async_session
from app.schemas.sales import SalesListResponse, SalesRow

router = APIRouter(prefix="/sales", tags=["sales"])

SortBy = Literal[
    "branch_name", "sale_date", "monthly_revenue", "net_profit", "occupancy_rate"
]
Order = Literal["asc", "desc"]

_SORT_COL_MAP: dict[str, str] = {
    "branch_name": "ms.branch_name",
    "sale_date": "ms.sale_month",
    "monthly_revenue": "ms.monthly_revenue",
    "net_profit": "net_profit",
    "occupancy_rate": "occupancy_rate",
}


async def require_admin(access_token: str | None = Cookie(None)) -> str:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return str(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.get("", response_model=SalesListResponse)
async def list_sales(
    sort_by: SortBy = Query(default="sale_date"),
    order: Order = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    year: Optional[int] = Query(default=None),
    branch_name: Optional[str] = Query(default=None),
    _: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
) -> SalesListResponse:
    sort_col = _SORT_COL_MAP[sort_by]
    order_dir = "ASC" if order == "asc" else "DESC"
    offset = (page - 1) * limit

    params: dict = {
        "year": year,
        "branch_name_pattern": f"%{branch_name}%" if branch_name else None,
        "limit": limit,
        "offset": offset,
    }

    base_cte = """
        WITH monthly_stats AS (
            SELECT
                s.branch_name,
                DATE_TRUNC('month', s.sale_date) AS sale_month,
                SUM(s.daily_revenue)             AS monthly_revenue
            FROM sales s
            WHERE (CAST(:year AS integer) IS NULL OR EXTRACT(YEAR FROM s.sale_date) = CAST(:year AS integer))
              AND (CAST(:branch_name_pattern AS text) IS NULL OR s.branch_name ILIKE CAST(:branch_name_pattern AS text))
            GROUP BY s.branch_name, DATE_TRUNC('month', s.sale_date)
        )
    """

    # COUNT(*) OVER() 윈도우 함수로 count+data를 단일 쿼리로 처리
    data_sql = text(
        base_cte
        + f"""
        SELECT
            ms.branch_name,
            b.address,
            TO_CHAR(ms.sale_month, 'YYYY-MM')       AS sale_month,
            ms.monthly_revenue::float,
            COALESCE(o.electricity_fee, 0)::float   AS electricity_fee,
            COALESCE(o.operating_cost, 0)::float    AS operating_cost,
            (
                ms.monthly_revenue
                - COALESCE(o.electricity_fee, 0)
                - COALESCE(o.operating_cost, 0)
            )::float                                AS net_profit,
            COALESCE(
                ROUND(
                    COALESCE(o.rented_units, 0)::float / NULLIF(b.total_units, 0) * 100,
                    1
                ),
                0
            )::float                                AS occupancy_rate,
            COUNT(*) OVER()                         AS total_count
        FROM monthly_stats ms
        JOIN branches b  ON b.branch_name = ms.branch_name
        LEFT JOIN operations o
            ON o.branch_name = ms.branch_name
           AND o.month       = ms.sale_month
        ORDER BY {sort_col} {order_dir}
        LIMIT :limit OFFSET :offset
        """
    )

    data_result = await db.execute(data_sql, params)
    rows = data_result.mappings().all()
    total = int(rows[0]["total_count"]) if rows else 0

    return SalesListResponse(
        data=[SalesRow(**{k: v for k, v in row.items() if k != "total_count"}) for row in rows],
        total=total,
        page=page,
        limit=limit,
    )
