from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from models import ClientInput
from calculator import MetabolicCalculator

app = FastAPI()
templates = Jinja2Templates(directory="templates")

from io import BytesIO
from fastapi.responses import StreamingResponse
from weasyprint import HTML

calculator = MetabolicCalculator()

from models import ClientInput, MacroPlan  # ensure MacroPlan is imported

def build_meal_plan(client: ClientInput, plan: MacroPlan):
    """
    Very simple, rule-based meal suggestions using goal + preference.
    Not 'perfect nutrition', but good enough for a professional-looking demo.
    """
    daily_cal = plan.calories
    # Rough split: 4 'eating events'
    per_meal = int(daily_cal * 0.25)

    goal_label = {
        "lose": "Fat loss–focused",
        "maintain": "Maintenance",
        "gain": "Muscle gain–focused"
    }.get(client.goal, "General")

    if client.preference == "low_carb":
        style = "Lower carb, higher fat"
        breakfast = f"Egg scramble with veggies, avocado, and a side of berries (~{per_meal} kcal)."
        lunch = f"Grilled chicken salad with olive oil dressing, nuts, and mixed greens (~{per_meal} kcal)."
        dinner = f"Salmon or lean steak, roasted non-starchy veggies, and a small portion of quinoa (~{per_meal} kcal)."
        snack = "Greek yogurt or cottage cheese with nuts, or a protein shake."
    elif client.preference == "high_carb":
        style = "Higher carb, lower fat"
        breakfast = f"Overnight oats with Greek yogurt, fruit, and a scoop of protein (~{per_meal} kcal)."
        lunch = f"Turkey or tofu grain bowl with rice, beans, veggies, and salsa (~{per_meal} kcal)."
        dinner = f"Stir-fry with lean protein, lots of vegetables, and rice or noodles (~{per_meal} kcal)."
        snack = "Fruit + protein (e.g., apple with string cheese, or banana + protein shake)."
    else:
        style = "Balanced carbs and fats"
        breakfast = f"Greek yogurt parfait with fruit, nuts, and a bit of granola (~{per_meal} kcal)."
        lunch = f"Whole-grain wrap with chicken or beans, veggies, and hummus (~{per_meal} kcal)."
        dinner = f"Baked fish or chicken, roasted potatoes, and mixed vegetables (~{per_meal} kcal)."
        snack = "Protein-focused snack: yogurt, cottage cheese, or a small protein shake."

    return {
        "label": goal_label,
        "style": style,
        "meals": [
            {"name": "Breakfast", "description": breakfast},
            {"name": "Lunch", "description": lunch},
            {"name": "Dinner", "description": dinner},
            {"name": "Snack / Flex", "description": snack},
        ],
    }

@app.get("/", response_class=HTMLResponse)
async def show_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/calculate", response_class=HTMLResponse)
async def calculate_view(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    sex: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    weight_unit: str = Form(...),
    height: float = Form(...),
    height_unit: str = Form(...),
    activity: str = Form(...),
    goal: str = Form(...),
    intensity: str = Form("moderate"),
    preference: str = Form("balanced"),
):
    client = ClientInput(
        first_name=first_name,
        last_name=last_name,
        sex=sex,
        age=age,
        weight=weight,
        weight_unit=weight_unit,
        height=height,
        height_unit=height_unit,
        activity=activity,
        goal=goal,
        intensity=intensity,
        preference=preference,
    )

    plan = calculator.calculate(client)

    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "client": client,
            "plan": plan
        }
    )
@app.post("/report", response_class=HTMLResponse)
async def report_pdf(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    sex: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    weight_unit: str = Form(...),
    height: float = Form(...),
    height_unit: str = Form(...),
    activity: str = Form(...),
    goal: str = Form(...),
    intensity: str = Form("moderate"),
    preference: str = Form("balanced"),
):
    # Rebuild client + plan from form data (stateless, no sessions needed)
    client = ClientInput(
        first_name=first_name,
        last_name=last_name,
        sex=sex,
        age=age,
        weight=weight,
        weight_unit=weight_unit,
        height=height,
        height_unit=height_unit,
        activity=activity,
        goal=goal,
        intensity=intensity,
        preference=preference,
    )

    plan = calculator.calculate(client)
    meal_plan = build_meal_plan(client, plan)

    # Render HTML for PDF
    html_template = templates.get_template("pdf_report.html")
    html_content = html_template.render(
        client=client,
        plan=plan,
        meal_plan=meal_plan
    )

    # Convert HTML to PDF
    pdf_io = BytesIO()
    HTML(string=html_content).write_pdf(pdf_io)
    pdf_io.seek(0)

    filename = "metabolic_plan.pdf"

    return StreamingResponse(
        pdf_io,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )  


    #execute the app: uvicorn main:app --reload --port $PORT