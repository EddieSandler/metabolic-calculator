from models import ClientInput, MetricData, MacroPlan


class MetabolicCalculator:
    def to_metric(self, client: ClientInput) -> MetricData:
        if client.weight_unit == "lb":
            weight_kg = client.weight / 2.20462
        else:
            weight_kg = client.weight

        if client.height_unit == "in":
            height_cm = client.height * 2.54
        else:
            height_cm = client.height

        return MetricData(
            sex=client.sex,
            age=client.age,
            weight_kg=weight_kg,
            height_cm=height_cm,
            activity=client.activity,
            goal=client.goal,
            intensity=client.intensity,
            preference=client.preference
        )

    def calculate_bmr(self, sex: str, weight_kg: float, height_cm: float, age: int) -> float:
        sex = sex.lower()
        if sex == "male":
            return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    def activity_factor(self, level: str) -> float:
        mapping = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "very_active": 1.725,
            "extra_active": 1.9,
        }
        return mapping[level]

    def target_calories(self, tdee: float, goal: str, intensity: str) -> float:
        deltas = {
            "mild": 250,
            "moderate": 500,
            "aggressive": 750,
        }
        delta = deltas.get(intensity, 500)

        if goal == "lose":
            return max(tdee - delta, 1200)
        elif goal == "gain":
            return tdee + delta
        else:
            return tdee

    def compute_macros(self, weight_kg: float, calories: float, preference: str):
        protein_g = 2.0 * weight_kg
        protein_kcal = protein_g * 4

        if preference == "low_carb":
            fat_pct = 0.35
        elif preference == "high_carb":
            fat_pct = 0.25
        else:
            fat_pct = 0.30

        fat_kcal = calories * fat_pct
        fat_g = fat_kcal / 9

        carb_kcal = calories - (protein_kcal + fat_kcal)
        carb_g = carb_kcal / 4

        return (
            protein_g, fat_g, carb_g,
            protein_kcal, fat_kcal, carb_kcal
        )

    def calculate(self, client: ClientInput) -> MacroPlan:
        m = self.to_metric(client)

        bmr = self.calculate_bmr(m.sex, m.weight_kg, m.height_cm, m.age)
        tdee = bmr * self.activity_factor(m.activity)
        calories = self.target_calories(tdee, m.goal, m.intensity)

        protein_g, fat_g, carb_g, protein_kcal, fat_kcal, carb_kcal = \
            self.compute_macros(m.weight_kg, calories, m.preference)

        return MacroPlan(
            bmr=int(round(bmr)),
            tdee=int(round(tdee)),
            calories=int(round(calories)),
            protein_g=int(round(protein_g)),
            fat_g=int(round(fat_g)),
            carb_g=int(round(carb_g)),
            protein_kcal=int(round(protein_kcal)),
            fat_kcal=int(round(fat_kcal)),
            carb_kcal=int(round(carb_kcal)),
        )