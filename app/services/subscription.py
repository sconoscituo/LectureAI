from enum import Enum
class PlanType(str, Enum):
    FREE = "free"; PRO = "pro"  # 월 9,900원
PLAN_LIMITS = {
    PlanType.FREE: {"lectures_per_month": 3,  "max_duration_min": 10, "quiz_generation": False},
    PlanType.PRO:  {"lectures_per_month": 30, "max_duration_min": 120,"quiz_generation": True},
}
PLAN_PRICES_KRW = {PlanType.FREE: 0, PlanType.PRO: 9900}
