from datetime import date
from typing import Tuple

from models import ClientInput, PlanResult


ACTIVITY_MAP = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "extremely_active": 1.9,
}


class MetabolicCalculator:
    """
    Core logic:
    - Convert units
    - Compute BMR
    - Apply activity factor -> TDEE
    - Use goal weight + goal date to set a safe weekly loss (0.5–2 lb/week)
    - Derive daily deficit
    - Compute macros and hand portions
    """

    def _weight_kg(self, weight: float, unit: str) -> float:
        if unit == "kg":
            return weight
        return weight * 0.45359237  # lb -> kg

    def _weight_lb(self, weight: float, unit: str) -> float:
        if unit == "lb":
            return weight
        return weight / 0.45359237  # kg -> lb

    def _height_cm(self, height: float, unit: str) -> float:
        if unit == "cm":
            return height
        return height * 2.54  # in -> cm

    def _bmr(self, sex: str, age: int, weight_kg: float, height_cm: float) -> int:
        if sex.lower() == "male":
            val = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            val = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
        return int(round(val))

    def _weight_profile(
        self, client: ClientInput, weight_lb: float
    ) -> Tuple[float, float, float]:
        """
        Returns: (lbs_to_lose, weeks_to_goal, weekly_loss_target)
        weekly_loss_target is clamped to 0.5–2.0 lb/week if goal is 'lose'.
        """
        today = date.today()
        days = max((client.goal_date - today).days, 1)
        weeks = days / 7.0

        goal_weight_lb = self._weight_lb(client.goal_weight, client.goal_weight_unit)
        lbs_to_lose = max(weight_lb - goal_weight_lb, 0.0)

        if client.goal != "lose" or lbs_to_lose <= 0:
            return lbs_to_lose, weeks, 0.0

        weekly_loss_raw = lbs_to_lose / weeks if weeks > 0 else 0.0
        weekly_loss = min(max(weekly_loss_raw, 0.5), 2.0)
        return lbs_to_lose, weeks, weekly_loss

    def _macros_and_portions(
        self, calories: int, weight_lb: float
    ):
        """
        Returns:
          protein_g, fat_g, carb_g,
          protein_kcal, fat_kcal, carb_kcal,
          portion_protein, portion_carbs, portion_fats
        """

        # Protein: 1 g / lb
        protein_g = int(round(weight_lb * 1.0))
        protein_kcal = protein_g * 4

        # Fat: ~30% of calories
        fat_kcal = calories * 0.30
        fat_g = int(round(fat_kcal / 9))

        # Remaining for carbs
        remaining_kcal = max(calories - (protein_kcal + fat_kcal), 0)
        carb_g = int(round(remaining_kcal / 4))
        carb_kcal = carb_g * 4

        # Hand portions (PN-style)
        portion_protein = max(int(round(protein_g / 24)), 1)  # palms
        portion_carbs = max(int(round(carb_g / 24)), 1)       # cupped handfuls
        portion_fats = max(int(round(fat_g / 10)), 1)         # thumbs

        return (
            protein_g,
            fat_g,
            carb_g,
            protein_kcal,
            int(round(fat_kcal)),
            carb_kcal,
            portion_protein,
            portion_carbs,
            portion_fats,
        )

    def calculate_plan(self, client: ClientInput) -> PlanResult:
        # Conversions
        weight_kg = self._weight_kg(client.weight, client.weight_unit)
        weight_lb = self._weight_lb(client.weight, client.weight_unit)
        height_cm = self._height_cm(client.height, client.height_unit)

        # BMR
        bmr = self._bmr(client.sex, client.age, weight_kg, height_cm)

        # TDEE
        activity_factor = ACTIVITY_MAP.get(client.activity, 1.2)
        tdee = int(round(bmr * activity_factor))

        # Weight loss profile
        lbs_to_lose, weeks_to_goal, weekly_loss = self._weight_profile(
            client, weight_lb
        )

        if client.goal == "lose" and weekly_loss > 0:
            daily_deficit = int(round(weekly_loss * 500))  # 3500/7 = 500
            daily_deficit = max(min(daily_deficit, 1000), 250)
        else:
            daily_deficit = 0

        # Calories
        if client.goal == "lose":
            calories = tdee - daily_deficit
        elif client.goal == "gain":
            calories = tdee + 250
        else:  # maintain
            calories = tdee

        # Never below BMR + 200
        min_safe = bmr + 200
        if calories < min_safe:
            calories = min_safe

        calories = int(round(calories))

        (
            protein_g,
            fat_g,
            carb_g,
            protein_kcal,
            fat_kcal,
            carb_kcal,
            portion_protein,
            portion_carbs,
            portion_fats,
        ) = self._macros_and_portions(calories, weight_lb)

        return PlanResult(
            bmr=bmr,
            tdee=tdee,
            calories=calories,
            protein_g=protein_g,
            fat_g=fat_g,
            carb_g=carb_g,
            protein_kcal=protein_kcal,
            fat_kcal=fat_kcal,
            carb_kcal=carb_kcal,
            activity_factor=activity_factor,
            lbs_to_lose=round(lbs_to_lose, 1),
            weeks_to_goal=round(weeks_to_goal, 1),
            weekly_loss=round(weekly_loss, 2),
            daily_deficit=daily_deficit,
            portion_protein=portion_protein,
            portion_carbs=portion_carbs,
            portion_fats=portion_fats,
        )