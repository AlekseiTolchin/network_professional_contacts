from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os

from app.database import engine, get_db, Base
from app.models import Profile, Skill, User, Post, Connection, Message
from app.auth import (
    verify_password, create_session_token, get_current_user,
    require_login, require_admin, RequireLoginException,
)
from app import crud
from app.seed import seed_data

# Создание таблиц и начальных данных
Base.metadata.create_all(bind=engine)
_init_db = next(get_db())
seed_data(_init_db)
_init_db.close()

app = FastAPI(title="Социальная сеть профессиональных контактов")

# Подключение шаблонов и статики
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.exception_handler(RequireLoginException)
async def require_login_handler(request: Request, exc: RequireLoginException):
    """При отсутствии авторизации — редирект на страницу входа."""
    return RedirectResponse("/login", status_code=302)


# ====================== Вспомогательная функция ======================

def ctx(request: Request, db: Session, **kwargs):
    """Сформировать базовый контекст шаблона."""
    user = get_current_user(request, db)
    return {"request": request, "current_user": user, **kwargs}


# ====================== Авторизация ======================

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
def login_action(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин или пароль"})
    response = RedirectResponse("/", status_code=302)
    response.set_cookie("session_token", create_session_token(user.id), httponly=True)
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("session_token")
    return response


# ====================== Главная / Dashboard ======================

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = require_login(request, db)
    profiles_count = db.query(Profile).count()
    skills_count = db.query(Skill).count()
    posts_count = db.query(Post).count()
    connections_count = db.query(Connection).count()
    messages_count = db.query(Message).count()
    users_count = db.query(User).count()
    return templates.TemplateResponse("dashboard.html", ctx(
        request, db,
        profiles_count=profiles_count,
        skills_count=skills_count,
        posts_count=posts_count,
        connections_count=connections_count,
        messages_count=messages_count,
        users_count=users_count,
    ))


# ====================== Profiles ======================

@app.get("/profiles", response_class=HTMLResponse)
def profiles_list(request: Request, db: Session = Depends(get_db)):
    user = require_login(request, db)
    profiles = crud.get_profiles(db)
    return templates.TemplateResponse("profiles.html", ctx(request, db, profiles=profiles))


@app.get("/profiles/add", response_class=HTMLResponse)
def profile_add_form(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    return templates.TemplateResponse("profile_form.html", ctx(request, db, profile=None, error=None))


@app.post("/profiles/add", response_class=HTMLResponse)
def profile_add(request: Request, profile_name: str = Form(...), job_title: str = Form(""), company_name: str = Form(""), db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        crud.create_profile(db, profile_name, job_title, company_name)
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse("profile_form.html", ctx(request, db, profile=None, error="Ошибка при создании профиля"))
    return RedirectResponse("/profiles", status_code=302)


@app.get("/profiles/edit/{profile_id}", response_class=HTMLResponse)
def profile_edit_form(profile_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    profile = crud.get_profile(db, profile_id)
    if not profile:
        return RedirectResponse("/profiles", status_code=302)
    return templates.TemplateResponse("profile_form.html", ctx(request, db, profile=profile, error=None))


@app.post("/profiles/edit/{profile_id}", response_class=HTMLResponse)
def profile_edit(profile_id: int, request: Request, profile_name: str = Form(...), job_title: str = Form(""), company_name: str = Form(""), db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        crud.update_profile(db, profile_id, profile_name, job_title, company_name)
    except IntegrityError:
        db.rollback()
        profile = crud.get_profile(db, profile_id)
        return templates.TemplateResponse("profile_form.html", ctx(request, db, profile=profile, error="Ошибка при обновлении"))
    return RedirectResponse("/profiles", status_code=302)


@app.post("/profiles/delete/{profile_id}")
def profile_delete(profile_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        crud.delete_profile(db, profile_id)
    except IntegrityError:
        db.rollback()
    return RedirectResponse("/profiles", status_code=302)


# ====================== Skills ======================

@app.get("/skills", response_class=HTMLResponse)
def skills_list(request: Request, db: Session = Depends(get_db)):
    require_login(request, db)
    skills = crud.get_skills(db)
    return templates.TemplateResponse("skills.html", ctx(request, db, skills=skills))


@app.get("/skills/add", response_class=HTMLResponse)
def skill_add_form(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    return templates.TemplateResponse("skill_form.html", ctx(request, db, skill=None, error=None))


@app.post("/skills/add", response_class=HTMLResponse)
def skill_add(request: Request, skill_name: str = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        crud.create_skill(db, skill_name)
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse("skill_form.html", ctx(request, db, skill=None, error="Навык с таким именем уже существует"))
    return RedirectResponse("/skills", status_code=302)


@app.get("/skills/edit/{skill_id}", response_class=HTMLResponse)
def skill_edit_form(skill_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    skill = crud.get_skill(db, skill_id)
    if not skill:
        return RedirectResponse("/skills", status_code=302)
    return templates.TemplateResponse("skill_form.html", ctx(request, db, skill=skill, error=None))


@app.post("/skills/edit/{skill_id}", response_class=HTMLResponse)
def skill_edit(skill_id: int, request: Request, skill_name: str = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        crud.update_skill(db, skill_id, skill_name)
    except IntegrityError:
        db.rollback()
        skill = crud.get_skill(db, skill_id)
        return templates.TemplateResponse("skill_form.html", ctx(request, db, skill=skill, error="Навык с таким именем уже существует"))
    return RedirectResponse("/skills", status_code=302)


@app.post("/skills/delete/{skill_id}")
def skill_delete(skill_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        crud.delete_skill(db, skill_id)
    except IntegrityError:
        db.rollback()
    return RedirectResponse("/skills", status_code=302)


# ====================== Posts ======================

@app.get("/posts", response_class=HTMLResponse)
def posts_list(request: Request, db: Session = Depends(get_db)):
    require_login(request, db)
    posts = crud.get_posts(db)
    return templates.TemplateResponse("posts.html", ctx(request, db, posts=posts))


@app.get("/posts/add", response_class=HTMLResponse)
def post_add_form(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    profiles = crud.get_profiles(db)
    return templates.TemplateResponse("post_form.html", ctx(request, db, post=None, profiles=profiles, error=None))


@app.post("/posts/add", response_class=HTMLResponse)
def post_add(request: Request, post_content: str = Form(...), posted_by_profile_id: int = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        crud.create_post(db, post_content, posted_by_profile_id)
    except IntegrityError:
        db.rollback()
        profiles = crud.get_profiles(db)
        return templates.TemplateResponse("post_form.html", ctx(request, db, post=None, profiles=profiles, error="Ошибка при создании поста"))
    return RedirectResponse("/posts", status_code=302)


@app.get("/posts/edit/{post_id}", response_class=HTMLResponse)
def post_edit_form(post_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    post = crud.get_post(db, post_id)
    if not post:
        return RedirectResponse("/posts", status_code=302)
    profiles = crud.get_profiles(db)
    return templates.TemplateResponse("post_form.html", ctx(request, db, post=post, profiles=profiles, error=None))


@app.post("/posts/edit/{post_id}", response_class=HTMLResponse)
def post_edit(post_id: int, request: Request, post_content: str = Form(...), posted_by_profile_id: int = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        crud.update_post(db, post_id, post_content, posted_by_profile_id)
    except IntegrityError:
        db.rollback()
        post = crud.get_post(db, post_id)
        profiles = crud.get_profiles(db)
        return templates.TemplateResponse("post_form.html", ctx(request, db, post=post, profiles=profiles, error="Ошибка при обновлении"))
    return RedirectResponse("/posts", status_code=302)


@app.post("/posts/delete/{post_id}")
def post_delete(post_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        crud.delete_post(db, post_id)
    except IntegrityError:
        db.rollback()
    return RedirectResponse("/posts", status_code=302)


# ====================== Connections ======================

@app.get("/connections", response_class=HTMLResponse)
def connections_list(request: Request, db: Session = Depends(get_db)):
    require_login(request, db)
    connections = crud.get_connections(db)
    return templates.TemplateResponse("connections.html", ctx(request, db, connections=connections))


@app.get("/connections/add", response_class=HTMLResponse)
def connection_add_form(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    profiles = crud.get_profiles(db)
    return templates.TemplateResponse("connection_form.html", ctx(request, db, connection=None, profiles=profiles, error=None))


@app.post("/connections/add", response_class=HTMLResponse)
def connection_add(request: Request, from_profile_id: int = Form(...), to_profile_id: int = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    if from_profile_id == to_profile_id:
        profiles = crud.get_profiles(db)
        return templates.TemplateResponse("connection_form.html", ctx(request, db, connection=None, profiles=profiles, error="Нельзя создать связь профиля с самим собой"))
    try:
        crud.create_connection(db, from_profile_id, to_profile_id)
    except IntegrityError:
        db.rollback()
        profiles = crud.get_profiles(db)
        return templates.TemplateResponse("connection_form.html", ctx(request, db, connection=None, profiles=profiles, error="Ошибка: такая связь уже существует или нарушено ограничение"))
    return RedirectResponse("/connections", status_code=302)


@app.get("/connections/edit/{connection_id}", response_class=HTMLResponse)
def connection_edit_form(connection_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    connection = crud.get_connection(db, connection_id)
    if not connection:
        return RedirectResponse("/connections", status_code=302)
    profiles = crud.get_profiles(db)
    return templates.TemplateResponse("connection_form.html", ctx(request, db, connection=connection, profiles=profiles, error=None))


@app.post("/connections/edit/{connection_id}", response_class=HTMLResponse)
def connection_edit(connection_id: int, request: Request, from_profile_id: int = Form(...), to_profile_id: int = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    if from_profile_id == to_profile_id:
        connection = crud.get_connection(db, connection_id)
        profiles = crud.get_profiles(db)
        return templates.TemplateResponse("connection_form.html", ctx(request, db, connection=connection, profiles=profiles, error="Нельзя создать связь профиля с самим собой"))
    try:
        crud.update_connection(db, connection_id, from_profile_id, to_profile_id)
    except IntegrityError:
        db.rollback()
        connection = crud.get_connection(db, connection_id)
        profiles = crud.get_profiles(db)
        return templates.TemplateResponse("connection_form.html", ctx(request, db, connection=connection, profiles=profiles, error="Ошибка при обновлении"))
    return RedirectResponse("/connections", status_code=302)


@app.post("/connections/delete/{connection_id}")
def connection_delete(connection_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    crud.delete_connection(db, connection_id)
    return RedirectResponse("/connections", status_code=302)


# ====================== ProfileSkills ======================

@app.get("/profile-skills", response_class=HTMLResponse)
def profile_skills_list(request: Request, db: Session = Depends(get_db)):
    require_login(request, db)
    ps_list = crud.get_profile_skills(db)
    return templates.TemplateResponse("profile_skills.html", ctx(request, db, profile_skills=ps_list))


@app.get("/profile-skills/add", response_class=HTMLResponse)
def profile_skill_add_form(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    profiles = crud.get_profiles(db)
    skills = crud.get_skills(db)
    return templates.TemplateResponse("profile_skill_form.html", ctx(request, db, ps=None, profiles=profiles, skills=skills, error=None))


@app.post("/profile-skills/add", response_class=HTMLResponse)
def profile_skill_add(request: Request, profile_id: int = Form(...), skill_id: int = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        crud.create_profile_skill(db, profile_id, skill_id)
    except IntegrityError:
        db.rollback()
        profiles = crud.get_profiles(db)
        skills = crud.get_skills(db)
        return templates.TemplateResponse("profile_skill_form.html", ctx(request, db, ps=None, profiles=profiles, skills=skills, error="Эта связь уже существует"))
    return RedirectResponse("/profile-skills", status_code=302)


@app.get("/profile-skills/edit/{ps_id}", response_class=HTMLResponse)
def profile_skill_edit_form(ps_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    ps = crud.get_profile_skill(db, ps_id)
    if not ps:
        return RedirectResponse("/profile-skills", status_code=302)
    profiles = crud.get_profiles(db)
    skills = crud.get_skills(db)
    return templates.TemplateResponse("profile_skill_form.html", ctx(request, db, ps=ps, profiles=profiles, skills=skills, error=None))


@app.post("/profile-skills/edit/{ps_id}", response_class=HTMLResponse)
def profile_skill_edit(ps_id: int, request: Request, profile_id: int = Form(...), skill_id: int = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        crud.update_profile_skill(db, ps_id, profile_id, skill_id)
    except IntegrityError:
        db.rollback()
        ps = crud.get_profile_skill(db, ps_id)
        profiles = crud.get_profiles(db)
        skills = crud.get_skills(db)
        return templates.TemplateResponse("profile_skill_form.html", ctx(request, db, ps=ps, profiles=profiles, skills=skills, error="Эта связь уже существует"))
    return RedirectResponse("/profile-skills", status_code=302)


@app.post("/profile-skills/delete/{ps_id}")
def profile_skill_delete(ps_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    crud.delete_profile_skill(db, ps_id)
    return RedirectResponse("/profile-skills", status_code=302)


# ====================== Messages ======================

@app.get("/messages", response_class=HTMLResponse)
def messages_list(request: Request, db: Session = Depends(get_db)):
    require_login(request, db)
    messages = crud.get_messages(db)
    return templates.TemplateResponse("messages.html", ctx(request, db, messages=messages))


@app.get("/messages/add", response_class=HTMLResponse)
def message_add_form(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    profiles = crud.get_profiles(db)
    return templates.TemplateResponse("message_form.html", ctx(request, db, message=None, profiles=profiles, error=None))


@app.post("/messages/add", response_class=HTMLResponse)
def message_add(request: Request, sender_id: int = Form(...), receiver_id: int = Form(...), message_body: str = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        crud.create_message(db, sender_id, receiver_id, message_body)
    except IntegrityError:
        db.rollback()
        profiles = crud.get_profiles(db)
        return templates.TemplateResponse("message_form.html", ctx(request, db, message=None, profiles=profiles, error="Ошибка при создании сообщения"))
    return RedirectResponse("/messages", status_code=302)


@app.get("/messages/edit/{message_id}", response_class=HTMLResponse)
def message_edit_form(message_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    message = crud.get_message(db, message_id)
    if not message:
        return RedirectResponse("/messages", status_code=302)
    profiles = crud.get_profiles(db)
    return templates.TemplateResponse("message_form.html", ctx(request, db, message=message, profiles=profiles, error=None))


@app.post("/messages/edit/{message_id}", response_class=HTMLResponse)
def message_edit(message_id: int, request: Request, sender_id: int = Form(...), receiver_id: int = Form(...), message_body: str = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        crud.update_message(db, message_id, sender_id, receiver_id, message_body)
    except IntegrityError:
        db.rollback()
        message = crud.get_message(db, message_id)
        profiles = crud.get_profiles(db)
        return templates.TemplateResponse("message_form.html", ctx(request, db, message=message, profiles=profiles, error="Ошибка при обновлении"))
    return RedirectResponse("/messages", status_code=302)


@app.post("/messages/delete/{message_id}")
def message_delete(message_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    crud.delete_message(db, message_id)
    return RedirectResponse("/messages", status_code=302)


# ====================== Users (только admin) ======================

@app.get("/users", response_class=HTMLResponse)
def users_list(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    users = crud.get_users(db)
    return templates.TemplateResponse("users.html", ctx(request, db, users=users))


@app.get("/users/add", response_class=HTMLResponse)
def user_add_form(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    profiles = crud.get_profiles(db)
    return templates.TemplateResponse("user_form.html", ctx(request, db, edit_user=None, profiles=profiles, error=None))


@app.post("/users/add", response_class=HTMLResponse)
def user_add(request: Request, username: str = Form(...), password: str = Form(...), role: str = Form("user"), profile_id: str = Form(""), db: Session = Depends(get_db)):
    require_admin(request, db)
    pid = int(profile_id) if profile_id else None
    try:
        crud.create_user(db, username, password, role, pid)
    except IntegrityError:
        db.rollback()
        profiles = crud.get_profiles(db)
        return templates.TemplateResponse("user_form.html", ctx(request, db, edit_user=None, profiles=profiles, error="Пользователь с таким именем уже существует"))
    return RedirectResponse("/users", status_code=302)


@app.get("/users/edit/{user_id}", response_class=HTMLResponse)
def user_edit_form(user_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    edit_user = crud.get_user(db, user_id)
    if not edit_user:
        return RedirectResponse("/users", status_code=302)
    profiles = crud.get_profiles(db)
    return templates.TemplateResponse("user_form.html", ctx(request, db, edit_user=edit_user, profiles=profiles, error=None))


@app.post("/users/edit/{user_id}", response_class=HTMLResponse)
def user_edit(user_id: int, request: Request, username: str = Form(...), role: str = Form("user"), profile_id: str = Form(""), password: str = Form(""), db: Session = Depends(get_db)):
    require_admin(request, db)
    pid = int(profile_id) if profile_id else None
    pwd = password if password else None
    try:
        crud.update_user(db, user_id, username, role, pid, pwd)
    except IntegrityError:
        db.rollback()
        edit_user = crud.get_user(db, user_id)
        profiles = crud.get_profiles(db)
        return templates.TemplateResponse("user_form.html", ctx(request, db, edit_user=edit_user, profiles=profiles, error="Ошибка: имя уже занято"))
    return RedirectResponse("/users", status_code=302)


@app.post("/users/delete/{user_id}")
def user_delete(user_id: int, request: Request, db: Session = Depends(get_db)):
    current = require_admin(request, db)
    if current.id == user_id:
        return RedirectResponse("/users", status_code=302)  # нельзя удалить себя
    crud.delete_user(db, user_id)
    return RedirectResponse("/users", status_code=302)
