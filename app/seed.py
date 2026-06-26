from sqlalchemy.orm import Session
from app.models import Profile, Connection, Post, Skill, ProfileSkill, Message, User
from app.auth import hash_password
from datetime import datetime, timezone, timedelta


def seed_data(db: Session):
    """Заполнить БД начальными данными, если таблицы пусты."""

    # Проверяем, есть ли уже данные
    if db.query(User).first():
        return

    # ---------- Профили ----------
    profiles = [
        Profile(profile_name="Иванов Иван", job_title="Backend-разработчик", company_name="ООО Технологии"),
        Profile(profile_name="Петрова Мария", job_title="Data Scientist", company_name="DataLab"),
        Profile(profile_name="Сидоров Алексей", job_title="DevOps-инженер", company_name="CloudHost"),
        Profile(profile_name="Козлова Елена", job_title="Project Manager", company_name="ООО Технологии"),
        Profile(profile_name="Администратор", job_title="Системный администратор", company_name="Admin Corp"),
    ]
    db.add_all(profiles)
    db.flush()

    # ---------- Навыки ----------
    skills = [
        Skill(skill_name="Python"),
        Skill(skill_name="SQL"),
        Skill(skill_name="Docker"),
        Skill(skill_name="Machine Learning"),
        Skill(skill_name="FastAPI"),
        Skill(skill_name="Linux"),
    ]
    db.add_all(skills)
    db.flush()

    # ---------- Связь профилей и навыков ----------
    profile_skills = [
        ProfileSkill(profile_id=profiles[0].profile_id, skill_id=skills[0].skill_id),
        ProfileSkill(profile_id=profiles[0].profile_id, skill_id=skills[1].skill_id),
        ProfileSkill(profile_id=profiles[0].profile_id, skill_id=skills[4].skill_id),
        ProfileSkill(profile_id=profiles[1].profile_id, skill_id=skills[0].skill_id),
        ProfileSkill(profile_id=profiles[1].profile_id, skill_id=skills[3].skill_id),
        ProfileSkill(profile_id=profiles[2].profile_id, skill_id=skills[2].skill_id),
        ProfileSkill(profile_id=profiles[2].profile_id, skill_id=skills[5].skill_id),
        ProfileSkill(profile_id=profiles[3].profile_id, skill_id=skills[1].skill_id),
    ]
    db.add_all(profile_skills)
    db.flush()

    # ---------- Контакты ----------
    connections = [
        Connection(from_profile_id=profiles[0].profile_id, to_profile_id=profiles[1].profile_id),
        Connection(from_profile_id=profiles[0].profile_id, to_profile_id=profiles[2].profile_id),
        Connection(from_profile_id=profiles[1].profile_id, to_profile_id=profiles[3].profile_id),
        Connection(from_profile_id=profiles[2].profile_id, to_profile_id=profiles[3].profile_id),
    ]
    db.add_all(connections)
    db.flush()

    # ---------- Посты ----------
    now = datetime.now(timezone.utc)
    posts = [
        Post(
            post_content="Начал изучать FastAPI — отличный фреймворк!",
            posted_by_profile_id=profiles[0].profile_id,
            creation_date=now - timedelta(days=3),
        ),
        Post(
            post_content="Завершила курс по Machine Learning на Coursera.",
            posted_by_profile_id=profiles[1].profile_id,
            creation_date=now - timedelta(days=2),
        ),
        Post(
            post_content="Настроил CI/CD пайплайн с Docker и GitHub Actions.",
            posted_by_profile_id=profiles[2].profile_id,
            creation_date=now - timedelta(days=1),
        ),
        Post(
            post_content="Ищу разработчиков в команду — пишите в личные сообщения!",
            posted_by_profile_id=profiles[3].profile_id,
            creation_date=now,
        ),
    ]
    db.add_all(posts)
    db.flush()

    # ---------- Сообщения ----------
    messages = [
        Message(
            sender_id=profiles[0].profile_id,
            receiver_id=profiles[1].profile_id,
            message_body="Привет! Как дела с проектом по ML?",
            sent_at=now - timedelta(hours=5),
        ),
        Message(
            sender_id=profiles[1].profile_id,
            receiver_id=profiles[0].profile_id,
            message_body="Привет! Всё отлично, заканчиваю модель.",
            sent_at=now - timedelta(hours=4),
        ),
        Message(
            sender_id=profiles[3].profile_id,
            receiver_id=profiles[2].profile_id,
            message_body="Алексей, можешь помочь настроить деплой?",
            sent_at=now - timedelta(hours=2),
        ),
    ]
    db.add_all(messages)
    db.flush()

    # ---------- Пользователи ----------
    admin_user = User(
        username="admin",
        password_hash=hash_password("admin123"),
        role="admin",
        profile_id=profiles[4].profile_id,
    )
    regular_user = User(
        username="user",
        password_hash=hash_password("user123"),
        role="user",
        profile_id=profiles[0].profile_id,
    )
    db.add_all([admin_user, regular_user])

    db.commit()
