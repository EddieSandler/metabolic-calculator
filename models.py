from dataclasses import dataclass
from datetime import date


@dataclass
class ClientInput:
    first_name: str
    last_name: str
    email: str
    sex: str
    age: int
    weight: float
    weight_unit: str
    height: float
    height_unit: str
    activity: str              # sedentary, lightly_active, ...
    goal: str                  # lose, maintain, gain
    intensity: str             # for future use
    preference: str            # balanced, low_carb, high_carb
    goal_weight: float
    goal_weight_unit: str
    goal_date: date


@dataclass
class PlanResult:
    bmr: int
    tdee: int
    calories: int

    protein_g: int
    fat_g: int
    carb_g: int
    protein_kcal: int
    fat_kcal: int
    carb_kcal: int

    activity_factor: float
    lbs_to_lose: float
    weeks_to_goal: float
    weekly_loss: float
    daily_deficit: int

    portion_protein: int
    portion_carbs: int
    portion_fats: int