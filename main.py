from datetime import date
from io import BytesIO
from dotenv import load_dotenv
from fastapi import Request, HTTPException, Depends
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from weasyprint import HTML

from calculator import MetabolicCalculator
from models import ClientInput

from stripe_paywall.checkout import router as stripe_checkout_router
from stripe_paywall.verify import router as stripe_verify_router    


import os
load_dotenv()
print("KEY:", os.getenv("STRIPE_SECRET_KEY")[:10], "...")
print("PRICE:", os.getenv("STRIPE_PRICE_ID"))




app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.include_router(stripe_checkout_router)
app.include_router(stripe_verify_router)
calculator = MetabolicCalculator()

def require_access(request: Request):
    access = request.cookies.get("calculator_access")
    if access != "granted":
        # Redirect to paywall instead of 403 if you want
        raise HTTPException(status_code=403, detail="Access denied. Please purchase access.")



def build_meal_plan(client: ClientInput, plan) -> dict:
    """
    Rule-based meal suggestions using goal + preference.
    """
    daily_cal = plan.calories
    per_meal = int(daily_cal * 0.25)

    goal_label = {
        "lose": "Fat loss–focused",
        "maintain": "Maintenance",
        "gain": "Muscle gain–focused",
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
        snack = "Fruit + protein (e.g., apple with cheese, or banana + protein shake)."
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
async def home(request: Request):
    access = request.cookies.get("calculator_access")

    if access == "granted":
        # User has paid → show calculator form
        return templates.TemplateResponse(
            "form.html",
            {"request": request, "error": None},
        )
    else:
        # User has NOT paid → show paywall
        return templates.TemplateResponse(
            "paywall.html",
            {"request": request},
        )

# @app.get("/paywall", response_class=HTMLResponse)
# async def paywall_view(request: Request):
#     return templates.TemplateResponse("paywall.html", {"request": request})


@app.post("/calculate", response_class=HTMLResponse)

async def calculate_view(
    request: Request,
    _=Depends(require_access),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
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
    goal_weight: float = Form(...),
    goal_weight_unit: str = Form(...),
    goal_date: str = Form(...),
):
    # Validate goal date server-side
    try:
        goal_dt = date.fromisoformat(goal_date)
    except ValueError:
        return templates.TemplateResponse(
            "form.html",
            {"request": request, "error": "Please enter a valid goal date."},
            status_code=400,
        )

    if goal_dt <= date.today():
        return templates.TemplateResponse(
            "form.html",
            {"request": request, "error": "Goal date must be in the future."},
            status_code=400,
        )

    client = ClientInput(
        first_name=first_name,
        last_name=last_name,
        email=email,
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
        goal_weight=goal_weight,
        goal_weight_unit=goal_weight_unit,
        goal_date=goal_dt,
    )

    plan = calculator.calculate_plan(client)
    meal_plan = build_meal_plan(client, plan)

    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "client": client,
            "plan": plan,
            "meal_plan": meal_plan,
        },
    )


@app.post("/report", response_class=HTMLResponse)
async def report_pdf(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
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
    goal_weight: float = Form(...),
    goal_weight_unit: str = Form(...),
    goal_date: str = Form(...),
):
    try:
        goal_dt = date.fromisoformat(goal_date)
    except ValueError:
        goal_dt = date.today()

    client = ClientInput(
        first_name=first_name,
        last_name=last_name,
        email=email,
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
        goal_weight=goal_weight,
        goal_weight_unit=goal_weight_unit,
        goal_date=goal_dt,
    )

    plan = calculator.calculate_plan(client)
    meal_plan = build_meal_plan(client, plan)

    template = templates.get_template("pdf_report.html")
    html_content = template.render(
        client=client,
        plan=plan,
        meal_plan=meal_plan,
    )

    pdf_io = BytesIO()
    HTML(string=html_content).write_pdf(pdf_io)
    pdf_io.seek(0)

    filename = f"metabolic_plan_{client.last_name or 'report'}.pdf"

    return StreamingResponse(
        pdf_io,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )