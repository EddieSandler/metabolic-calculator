from dataclasses import dataclass

@dataclass
class ClientInput:
    first_name: str
    last_name: str
    sex: str
    age: int
    weight: float
    weight_unit: str
    height: float
    height_unit: str
    activity: str
    goal: str
    intensity: str = "moderate"
    preference: str = "balanced"


@dataclass
class MetricData:
    sex: str
    age: int
    weight_kg: float
    height_cm: float
    activity: str
    goal: str
    intensity: str
    preference: str


@dataclass
class MacroPlan:
    bmr: int
    tdee: int
    calories: int
    protein_g: int
    fat_g: int
    carb_g: int
    protein_kcal: int
    fat_kcal: int
    carb_kcal: int