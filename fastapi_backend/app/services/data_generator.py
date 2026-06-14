import asyncio
import random
from datetime import date

import asyncpg

from app.config import settings

# 모듈 레벨 상태 (Railway Hobby 단일 인스턴스에서 안전)
_STATUS: dict = {"value": "idle"}

# 수도권 22개 지역 (서울 11 + 인천 3 + 경기 8)
_REGIONS = [
    ("강남구", (37.495, 37.530), (127.025, 127.090)),
    ("강서구", (37.540, 37.570), (126.820, 126.880)),
    ("마포구", (37.540, 37.570), (126.895, 126.945)),
    ("서초구", (37.475, 37.510), (126.990, 127.050)),
    ("송파구", (37.490, 37.530), (127.095, 127.145)),
    ("영등포구", (37.520, 37.545), (126.895, 126.935)),
    ("종로구", (37.570, 37.600), (126.960, 127.010)),
    ("중구", (37.555, 37.575), (126.970, 127.010)),
    ("노원구", (37.640, 37.670), (127.055, 127.100)),
    ("관악구", (37.460, 37.490), (126.925, 126.975)),
    ("은평구", (37.600, 37.640), (126.900, 126.950)),
    ("부평구", (37.485, 37.510), (126.715, 126.755)),
    ("남동구", (37.445, 37.475), (126.725, 126.775)),
    ("연수구", (37.405, 37.435), (126.665, 126.710)),
    ("수원시", (37.245, 37.295), (126.975, 127.045)),
    ("성남시", (37.415, 37.460), (127.115, 127.170)),
    ("고양시", (37.640, 37.680), (126.820, 126.885)),
    ("부천시", (37.495, 37.525), (126.765, 126.810)),
    ("안양시", (37.385, 37.420), (126.925, 126.975)),
    ("화성시", (37.165, 37.220), (126.820, 126.890)),
    ("용인시", (37.220, 37.270), (127.075, 127.155)),
    ("남양주시", (37.615, 37.665), (127.155, 127.240)),
]

_BUILDING_USAGES = ["창고", "근린생활시설", "상업용", "기타"]


def _generate_branches() -> list[tuple]:
    """220개 수도권 가상 지점 생성 (22개 지역 × 10개 지점)"""
    records = []
    for region_name, lat_range, lon_range in _REGIONS:
        for i in range(1, 11):
            branch_name = f"다락 {region_name} {i:02d}호점"
            lat = round(random.uniform(*lat_range), 6)
            lon = round(random.uniform(*lon_range), 6)
            area_sqm = round(random.uniform(150, 600), 1)
            monthly_rent = round(random.uniform(200, 800) * 10000)
            maintenance_fee = round(monthly_rent * random.uniform(0.08, 0.15))
            building_usage = random.choice(_BUILDING_USAGES)
            ev_charging = random.random() < 0.3
            parking_count = random.randint(0, 20)
            address = f"가상 {region_name} 테스트로 {random.randint(1, 200)}"
            records.append((
                branch_name, address, area_sqm, monthly_rent, maintenance_fee,
                building_usage, ev_charging, parking_count, lat, lon,
            ))
    return records


def _generate_members(branches: list[tuple]) -> list[tuple]:
    """지점당 5개 가상 회원 생성 (총 1,100개)"""
    records = []
    for idx, branch in enumerate(branches):
        for j in range(1, 6):
            email = f"member{idx * 5 + j}@dalock-virtual.com"
            name = f"가상회원{idx * 5 + j:04d}"
            phone = f"010-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
            address = branch[1]
            records.append((email, name, phone, address))
    return records


def _generate_operations(branch_name: str) -> list[tuple]:
    """지점의 2016-01 ~ 2025-12 월별 운영비 120개"""
    records = []
    base_monthly_revenue = random.uniform(3_000_000, 15_000_000)
    for year in range(2016, 2026):
        growth = 1.03 ** (year - 2016)
        for month in range(1, 13):
            monthly_rev = base_monthly_revenue * growth * random.uniform(0.85, 1.15)
            electricity_fee = round(monthly_rev * random.uniform(0.12, 0.18))
            operating_cost = round(monthly_rev * random.uniform(0.08, 0.14))
            month_date = date(year, month, 1)
            records.append((branch_name, month_date, electricity_fee, operating_cost))
    return records


def _generate_sales(branch_name: str, member_emails: list[str]) -> list[tuple]:
    """지점의 2016-01-01 ~ 2025-12-31 일별 매출 (~3,650개)"""
    records = []
    base_daily = random.uniform(100_000, 800_000)
    current = date(2016, 1, 1)
    end = date(2025, 12, 31)
    day_count = 0
    while current <= end:
        year_growth = 1.03 ** (current.year - 2016)
        daily_rev = round(base_daily * year_growth * random.uniform(0.7, 1.3))
        member_email = member_emails[day_count % len(member_emails)]
        records.append((branch_name, member_email, current, daily_rev))
        current = date.fromordinal(current.toordinal() + 1)
        day_count += 1
    return records


async def generate_all_data() -> None:
    """전체 가상 데이터 생성 (asyncpg COPY 프로토콜 — 지점별 청크)"""
    # asyncpg raw connection: SQLAlchemy+asyncpg URL → asyncpg URL 변환
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = None
    try:
        conn = await asyncpg.connect(db_url)
        async with conn.transaction():
            # 1. 기존 데이터 삭제 (FK 역순)
            await conn.execute("DELETE FROM sales")
            await conn.execute("DELETE FROM operations")
            await conn.execute("DELETE FROM members")
            await conn.execute("DELETE FROM branches")

            # 2. branches INSERT
            branches = _generate_branches()
            await conn.executemany(
                "INSERT INTO branches"
                " (branch_name, address, area_sqm, monthly_rent, maintenance_fee,"
                "  building_usage, ev_charging, parking_count, latitude, longitude)"
                " VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)",
                branches,
            )

            # 3. members INSERT
            members = _generate_members(branches)
            await conn.executemany(
                "INSERT INTO members (email, name, phone, address) VALUES ($1,$2,$3,$4)",
                members,
            )

            # 4. 지점별 청크: operations COPY + sales COPY (메모리 최적화)
            branch_member_map: dict[str, list[str]] = {}
            for idx, b in enumerate(branches):
                branch_member_map[b[0]] = [members[idx * 5 + j][0] for j in range(5)]

            for branch_name in branch_member_map:
                op_records = _generate_operations(branch_name)
                await conn.copy_records_to_table(
                    "operations",
                    records=op_records,
                    columns=["branch_name", "month", "electricity_fee", "operating_cost"],
                )
                sales_records = _generate_sales(branch_name, branch_member_map[branch_name])
                await conn.copy_records_to_table(
                    "sales",
                    records=sales_records,
                    columns=["branch_name", "member_email", "sale_date", "daily_revenue"],
                )
                await asyncio.sleep(0)  # 이벤트 루프 양보
    finally:
        if conn:
            await conn.close()
        _STATUS["value"] = "idle"


async def delete_all_data() -> None:
    """sales, operations, members 전체 삭제 (branches 보존, 멱등성 보장)"""
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = None
    try:
        conn = await asyncpg.connect(db_url)
        async with conn.transaction():
            await conn.execute("DELETE FROM sales")
            await conn.execute("DELETE FROM operations")
            await conn.execute("DELETE FROM members")
    finally:
        if conn:
            await conn.close()
