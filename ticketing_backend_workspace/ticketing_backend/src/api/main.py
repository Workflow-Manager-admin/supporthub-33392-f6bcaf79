from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from jose import jwt, JWTError


# App settings
SECRET_KEY = "CHANGE_ME_SECRET"  # In production, use .env for config!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


app = FastAPI(
    title="Ticketing System API",
    description=(
        "API backend for support ticketing system. "
        "Manages tickets, users, and authentication."
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "tickets", "description": "Ticket CRUD operations"},
        {"name": "users", "description": "User registration and authentication"},
    ],
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory "databases"
users_db: Dict[str, dict] = {}  # key: email, value: user dict
tickets_db: Dict[int, dict] = {}  # key: ticket_id, value: ticket dict
ticket_id_counter = 1

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


# Schemas


class UserBase(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Unique user email"
    )


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=6,
        description="Password (plaintext, do not use in production)"
    )


class User(UserBase):
    id: int = Field(
        ...,
        description="User ID"
    )


class Token(BaseModel):
    access_token: str
    token_type: str


class TicketBase(BaseModel):
    title: str = Field(
        ...,
        description="Brief summary of the issue"
    )
    description: str = Field(
        ...,
        description="Detailed description of the issue"
    )
    status: str = Field(
        default="open",
        description="Ticket status",
        examples=["open", "in_progress", "closed"]
    )


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(
        None,
        description="Ticket status",
        examples=["open", "in_progress", "closed"]
    )


class Ticket(TicketBase):
    id: int
    owner_email: EmailStr
    created_at: datetime


# Helper functions


def verify_password(plain_password, password_hash):
    # DO NOT use plain text in production!
    return plain_password == password_hash


def get_password_hash(password):
    # Use actual hashing in production; here just return the password
    return password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Dependency

# PUBLIC_INTERFACE
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Decode JWT and retrieve current user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None or email not in users_db:
            raise credentials_exception
        user_dict = users_db[email]
        return User(id=user_dict["id"], email=user_dict["email"])
    except JWTError:
        raise credentials_exception


# Routes


@app.get(
    "/",
    tags=["health"],
    summary="Health Check",
    description="Check API health"
)
def health_check():
    """Returns 'Healthy' if API is running."""
    return {"message": "Healthy"}


# User registration
@app.post(
    "/auth/register",
    response_model=User,
    tags=["users"],
    summary="Register user",
    description="Create a new user account"
)
def register_user(user: UserCreate):
    """
    Register a new user.

    - email: User email (unique).
    - password: Plain text (not for production).

    Returns user details.
    """
    if user.email in users_db:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    user_id = len(users_db) + 1
    users_db[user.email] = {
        "id": user_id,
        "email": user.email,
        "hashed_password": get_password_hash(user.password)
    }
    return User(id=user_id, email=user.email)


# User authentication/token
@app.post(
    "/auth/token",
    response_model=Token,
    tags=["users"],
    summary="User login",
    description="Authenticate user and get access token"
)
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return JWT access token.

    - username: User email
    - password: User password

    Returns JWT token if valid.
    """
    user_dict = users_db.get(form_data.username)
    if not user_dict or not verify_password(
        form_data.password, user_dict["hashed_password"]
    ):
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password"
        )
    access_token = create_access_token(
        data={"sub": user_dict["email"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Get current user (for testing)
@app.get(
    "/auth/me",
    response_model=User,
    tags=["users"],
    summary="Get current user",
    description="Returns current user info based on access token"
)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# Create ticket
@app.post(
    "/tickets/",
    response_model=Ticket,
    tags=["tickets"],
    summary="Create a ticket",
    description="Create a new support ticket. Authentication required.",
    status_code=201,
    responses={201: {"description": "Ticket created"}}
)
def create_ticket(
    ticket: TicketCreate, current_user: User = Depends(get_current_user)
):
    """
    Create a support ticket.

    - title: Brief summary
    - description: Detailed description

    Returns created ticket.
    """
    global ticket_id_counter
    new_ticket = {
        "id": ticket_id_counter,
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status,
        "owner_email": current_user.email,
        "created_at": datetime.utcnow()
    }
    tickets_db[ticket_id_counter] = new_ticket
    ticket_id_counter += 1
    return Ticket(**new_ticket)


# List tickets (own)
@app.get(
    "/tickets/",
    response_model=List[Ticket],
    tags=["tickets"],
    summary="List tickets",
    description="List all tickets created by the authenticated user."
)
def list_tickets(current_user: User = Depends(get_current_user)):
    """
    List all tickets owned by authenticated user.

    Returns a list of tickets.
    """
    return [
        Ticket(**ticket)
        for ticket in tickets_db.values()
        if ticket["owner_email"] == current_user.email
    ]


# Get ticket detail
@app.get(
    "/tickets/{ticket_id}",
    response_model=Ticket,
    tags=["tickets"],
    summary="Get ticket detail",
    description="Get details for a specific ticket by ticket_id."
)
def get_ticket(
    ticket_id: int, current_user: User = Depends(get_current_user)
):
    """
    Get detailed info about a specific ticket.

    Returns ticket data if owned by user.
    """
    ticket = tickets_db.get(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=404, detail="Ticket not found"
        )
    if ticket["owner_email"] != current_user.email:
        raise HTTPException(
            status_code=403, detail="Not authorized"
        )
    return Ticket(**ticket)


# Update ticket
@app.put(
    "/tickets/{ticket_id}",
    response_model=Ticket,
    tags=["tickets"],
    summary="Update a ticket",
    description="Update the title, description, or status of a ticket."
)
def update_ticket(
    ticket_id: int, ticket_update: TicketUpdate, current_user: User = Depends(get_current_user)
):
    """
    Update ticket properties.

    You can update: title, description, status.
    Only owner can update.
    """
    ticket = tickets_db.get(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=404, detail="Ticket not found"
        )
    if ticket["owner_email"] != current_user.email:
        raise HTTPException(
            status_code=403, detail="Not authorized"
        )
    update_data = ticket_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        ticket[field] = value
    tickets_db[ticket_id] = ticket
    return Ticket(**ticket)


# Delete ticket
@app.delete(
    "/tickets/{ticket_id}",
    status_code=204,
    tags=["tickets"],
    summary="Delete a ticket",
    description="Remove a ticket by ticket_id."
)
def delete_ticket(
    ticket_id: int, current_user: User = Depends(get_current_user)
):
    """
    Delete a ticket you own.
    """
    ticket = tickets_db.get(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=404, detail="Ticket not found"
        )
    if ticket["owner_email"] != current_user.email:
        raise HTTPException(
            status_code=403, detail="Not authorized"
        )
    del tickets_db[ticket_id]
    return


# --- Custom OpenAPI with WebSocket doc section (if you add real-time features in future) ---


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

