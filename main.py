import json
from fastapi import Request, FastAPI, HTTPException
from starlette.responses import RedirectResponse


app = FastAPI()


with open('menu.json', 'r') as read_file:
    data = json.load(read_file)


def saveJson(obj):
    with open('menu.json', 'w') as dumpFile:
        json.dump(obj, dumpFile)


menu = data['menu']


# routing

@app.get('/')
def root():
    return RedirectResponse('/docs')


@app.get('/menu/')
async def read_menu():
    try:
        return menu
    except:
        raise HTTPException(status_code=404, detail=f'item not found')


@app.get('/menu/{item_id}')
async def read_menu(item_id: int):
    for menu_item in menu:
        if menu_item['id'] == item_id:
            return(menu_item)
    raise HTTPException(status_code=404, detail=f'item not found')


@app.post('/menu/')
async def add_menu(request: Request):
    menuObjTemp = {'id': len(menu)+1}
    # get request body in json format
    req = await request.json()
    # add the new menu name from request body to menuObjTemp
    menuObjTemp['name'] = req['name']

    # rewrite data menu with new menu
    menu.append(menuObjTemp)
    data['menu'] = menu

    saveJson(data)
    return(menuObjTemp)


@app.patch('/menu/{item_id}')
async def update_menu(item_id: int, request: Request):
    req = await request.json()
    for menu_item in menu:
        if menu_item['id'] == item_id:
            menu_item['name'] = req['name']
            return(menu_item)
    data['menu'] = menu
    saveJson(data)


@app.delete('/menu/{item_id}')
async def delete_menu(item_id: int):
    for menu_item in menu:
        if menu_item['id'] == item_id:
            menu.remove(menu_item)
            data['menu'] = menu
            saveJson(data)
            return(menu_item, "deleted")

    raise HTTPException(status_code=404, detail=f'item not found')