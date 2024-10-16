import os
import json
import logging
import uvicorn
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request

# create a logger with the name app.log and set the logging level to INFO
logging.basicConfig(filename="app.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# load the env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

# Accessing data
mongodb = os.getenv("MONGO_URI")

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# MongoDB connection setup
client = MongoClient(mongodb)
db = client["user_data"]
collection = db["users"]


# CORS middleware configuration
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if not mongodb:
    raise Exception("MONGO_URI is not set. Please check the .env file.")


# Pydantic model for user input
class UserInput(BaseModel):
    name: str
    surname: str
    day: str
    month: str
    year: str
    sex: str
    placeOfBirth: str


# Month mapping for Codice Fiscale
month_mapping = {
    "1": "A", "2": "B", "3": "C", "4": "D", "5": "E",
    "6": "H", "7": "L", "8": "M", "9": "P", "10": "R",
    "11": "S", "12": "T"
}


def get_consonants(name):
    return [c for c in name.upper() if c not in "AEIOU"]


def get_vowels(name):
    return [c for c in name.upper() if c in "AEIOU"]


def process_surname(surname):
    consonants = get_consonants(surname)
    vowels = get_vowels(surname)
    result = consonants[:3] + vowels[:3 - len(consonants)]
    return (result + ['X', 'X', 'X'])[:3]


def process_name(name):
    consonants = get_consonants(name)
    vowels = get_vowels(name)
    if len(consonants) >= 4:
        result = [consonants[0], consonants[2], consonants[3]]
    else:
        result = consonants[:3] + vowels[:3 - len(consonants)]
    return (result + ['X', 'X', 'X'])[:3]


def process_year(year):
    return year[-2:]


def process_month(month):
    return month_mapping[month]


def process_day_and_sex(day, sex):
    day = int(day)
    if sex.upper() == "FEMALE":
        day += 40
    return f"{day:02}"


# Placeholder for place of birth code (requires ISTAT codes for Italian towns)
def process_place_of_birth(country_of_birth):
    istat = json.load(open("static/ISTAT.json"))
    for item in istat.keys():
        if country_of_birth.lower() in str(item):
            return istat[item]
    return "Z000"

def calculate_check_character(codice):
    # Values for characters in odd positions (1, 3, 5, ..., 15)
    odd_values = {
        '0': 1, '1': 0, '2': 5, '3': 7, '4': 9, '5': 13, '6': 15, '7': 17, '8': 19, '9': 21,
        'A': 1, 'B': 0, 'C': 5, 'D': 7, 'E': 9, 'F': 13, 'G': 15, 'H': 17, 'I': 19, 'J': 21,
        'K': 2, 'L': 4, 'M': 18, 'N': 20, 'O': 11, 'P': 3, 'Q': 6, 'R': 8, 'S': 12, 'T': 14,
        'U': 16, 'V': 10, 'W': 22, 'X': 25, 'Y': 24, 'Z': 23
    }

    # Values for characters in even positions (2, 4, 6, ..., 14)
    even_values = {
        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7, 'I': 8, 'J': 9,
        'K': 10, 'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P': 15, 'Q': 16, 'R': 17, 'S': 18, 'T': 19,
        'U': 20, 'V': 21, 'W': 22, 'X': 23, 'Y': 24, 'Z': 25
    }

    # Check if codice is the correct length
    if len(codice) != 15:
        raise ValueError("Codice must be 15 characters long")

    # Calculate the sum based on odd and even position rules
    total = 0
    for index, char in enumerate(codice):
        if (index + 1) % 2 == 0:  # Even index (odd position in human terms)
            total += even_values[char]
        else:                     # Odd index (even position in human terms)
            total += odd_values[char]

    # Determine the check character from the sum
    check_character = chr((total % 26) + ord('A'))

    return check_character


def generate_codice_fiscale(data: UserInput):
    # check all the parameters are not empty
    # The name and surname must be string
    # The day must be string and between 1 and 31
    # The month must be string and between 1 and 12
    # The year must be string and between 1900 and 2024
    # The Sex must be string and Male or Female
    # The place of birth must be string

    if not data.name or not data.surname or not data.day or not data.month or not data.year or not data.sex or not data.placeOfBirth:
        raise HTTPException(status_code=400, detail="All fields are required")
    if not isinstance(data.name, str) or not isinstance(data.surname, str):
        raise HTTPException(status_code=400, detail="Name and surname must be string")
    if not isinstance(data.day, str) or not 1 <= int(data.day) <= 31:
        raise HTTPException(status_code=400, detail="Day must be a string between 1 and 31")
    if not isinstance(data.month, str) or data.month not in month_mapping.keys():
        raise HTTPException(status_code=400, detail="Month must be a string among January to December")
    if not isinstance(data.year, str) or not 1900 <= int(data.year) <= 2024:
        raise HTTPException(status_code=400, detail="Year must be a string between 1900 to 2024")
    if not isinstance(data.sex, str) or (data.sex.upper() not in ["MALE", "FEMALE"]):
        raise HTTPException(status_code=400, detail="Sex must be a string and one of the Male or Female")
    if not isinstance(data.placeOfBirth, str):
        raise HTTPException(status_code=400, detail="Place of birth must be a string")

    name_part = "".join(process_name(data.name))
    surname_part = "".join(process_surname(data.surname))
    year_part = process_year(data.year)
    month_part = process_month(data.month)
    day_sex_part = process_day_and_sex(data.day, data.sex)
    place_of_birth_part = process_place_of_birth(data.placeOfBirth)

    # Combine the first 15 characters of the Codice Fiscale
    partial_cf = f"{surname_part}{name_part}{year_part}{month_part}{day_sex_part}{place_of_birth_part}"

    # Calculate the check character
    check_character = calculate_check_character(partial_cf)

    # Return the complete Codice Fiscale
    return f"{partial_cf}{check_character}"


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "message": "Hello World"})



@app.post("/generate_cf")
async def generate_cf(user: UserInput):
    # Check if user data already exists
    existing_user = collection.find_one({
        "surname": user.surname,
        "name": user.name,
        "day": user.day,
        "month": user.month,
        "year": user.year
    })

    if existing_user:
        codice_fiscale = existing_user['codice_fiscale']
        return {"codiceFiscale exist": codice_fiscale}

    # Generate codice fiscale
    codice_fiscale = generate_codice_fiscale(user)

    # Insert new user data into MongoDB
    try:
        # Create a new document with the user data and codice_fiscale
        document_to_insert = {**user.dict(), "codice_fiscale": codice_fiscale}
        logging.info(f"Inserting document: {document_to_insert}")

        collection.insert_one(document_to_insert)
        logging.info("Data inserted successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert data into MongoDB: {str(e)}")

    return {"codiceFiscale": codice_fiscale}
