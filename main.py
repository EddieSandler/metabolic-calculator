from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from models import ClientInput
from calculator import MetabolicCalculator

app = FastAPI()
templates = Jinja2Templates(directory="templates")

calculator = MetabolicCalculator()


@app.get("/", response_class=HTMLResponse)
async def show_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/calculate", response_class=HTMLResponse)
async def calculate_view(
    request: Request,
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