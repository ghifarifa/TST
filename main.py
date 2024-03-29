from fastapi import Depends, FastAPI, HTTPException, status
import json
from pydantic import BaseModel

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette.responses import RedirectResponse


app = FastAPI(title="Tugas TST - UTS 18219105")
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

dummies_db = {
    "asdf": {
        "username": "asdf",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$LgB0KEfyUGBvmdVtckmjdOZF77bXjBppuK4EOLXfPNTyI3OXW8gze",
        "disabled": False,
    }
}


class Item(BaseModel):
	id: int
	name: str

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str
  
with open("menu.json","r") as read_file:
	data = json.load(read_file)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(login: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(login, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(dummies_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(dummies_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username}
       )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get('/menu')
async def read_all_menu(current_user: User = Depends(get_current_active_user)):
	return data['menu']


@app.get('/menu/{item_id}')
async def read_menu(item_id: int, current_user: User = Depends(get_current_active_user)):
	for menu_item in data['menu']:
		if menu_item['id'] == item_id:
			return menu_item
	raise HTTPException(
		status_code=404, detail=f'item not found'
	)

@app.post('/menu')
async def add_menu(item: Item, current_user: User = Depends(get_current_active_user)):
	item_dict = item.dict()
	item_found = False
	for menu_item in data['menu']:
		if menu_item['id'] == item_dict['id']:
			item_found = True
			return "Menu ID "+str(item_dict['id'])+" exists."
	
	if not item_found:
		data['menu'].append(item_dict)
		with open("menu.json","w") as write_file:
			json.dump(data, write_file)

		return item_dict
	raise HTTPException(
		status_code=404, detail=f'item not found'
	)

@app.patch('/menu')
async def update_menu(item: Item, current_user: User = Depends(get_current_active_user)):
	item_dict = item.dict()
	item_found = False
	for menu_idx, menu_item in enumerate(data['menu']):
		if menu_item['id'] == item_dict['id']:
			item_found = True
			data['menu'][menu_idx]=item_dict
			
			with open("menu.json","w") as write_file:
				json.dump(data, write_file)
			return "updated"
	
	if not item_found:
		return "Menu ID not found."
	raise HTTPException(
		status_code=404, detail=f'item not found'
	)

@app.delete('/menu/{item_id}')
async def delete_menu(item_id: int, current_user: User = Depends(get_current_active_user)):

	item_found = False
	for menu_idx, menu_item in enumerate(data['menu']):
		if menu_item['id'] == item_id:
			item_found = True
			data['menu'].pop(menu_idx)
			
			with open("menu.json","w") as write_file:
				json.dump(data, write_file)
			return "updated"
	
	if not item_found:
		return "Menu ID not found."
	raise HTTPException(
		status_code=404, detail=f'item not found'
	)

@app.get("/")
async def docs_redirect():
    return RedirectResponse(url='/docs')