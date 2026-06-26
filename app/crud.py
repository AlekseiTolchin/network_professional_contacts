from sqlalchemy.orm import Session
from app.models import Profile, Connection, Post, Skill, ProfileSkill, Message, User
from app.auth import hash_password


# ==================== Profiles ====================

def get_profiles(db: Session):
    return db.query(Profile).order_by(Profile.profile_id).all()

def get_profile(db: Session, profile_id: int):
    return db.query(Profile).filter(Profile.profile_id == profile_id).first()

def create_profile(db: Session, profile_name: str, job_title: str, company_name: str):
    p = Profile(profile_name=profile_name, job_title=job_title, company_name=company_name)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def update_profile(db: Session, profile_id: int, profile_name: str, job_title: str, company_name: str):
    p = get_profile(db, profile_id)
    if p:
        p.profile_name = profile_name
        p.job_title = job_title
        p.company_name = company_name
        db.commit()
    return p

def delete_profile(db: Session, profile_id: int):
    p = get_profile(db, profile_id)
    if p:
        db.delete(p)
        db.commit()
    return p


# ==================== Connections ====================

def get_connections(db: Session):
    return db.query(Connection).order_by(Connection.connection_id).all()

def get_connection(db: Session, connection_id: int):
    return db.query(Connection).filter(Connection.connection_id == connection_id).first()

def create_connection(db: Session, from_profile_id: int, to_profile_id: int):
    c = Connection(from_profile_id=from_profile_id, to_profile_id=to_profile_id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

def update_connection(db: Session, connection_id: int, from_profile_id: int, to_profile_id: int):
    c = get_connection(db, connection_id)
    if c:
        c.from_profile_id = from_profile_id
        c.to_profile_id = to_profile_id
        db.commit()
    return c

def delete_connection(db: Session, connection_id: int):
    c = get_connection(db, connection_id)
    if c:
        db.delete(c)
        db.commit()
    return c


# ==================== Posts ====================

def get_posts(db: Session):
    return db.query(Post).order_by(Post.creation_date.desc()).all()

def get_post(db: Session, post_id: int):
    return db.query(Post).filter(Post.post_id == post_id).first()

def create_post(db: Session, post_content: str, posted_by_profile_id: int):
    p = Post(post_content=post_content, posted_by_profile_id=posted_by_profile_id)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def update_post(db: Session, post_id: int, post_content: str, posted_by_profile_id: int):
    p = get_post(db, post_id)
    if p:
        p.post_content = post_content
        p.posted_by_profile_id = posted_by_profile_id
        db.commit()
    return p

def delete_post(db: Session, post_id: int):
    p = get_post(db, post_id)
    if p:
        db.delete(p)
        db.commit()
    return p


# ==================== Skills ====================

def get_skills(db: Session):
    return db.query(Skill).order_by(Skill.skill_id).all()

def get_skill(db: Session, skill_id: int):
    return db.query(Skill).filter(Skill.skill_id == skill_id).first()

def create_skill(db: Session, skill_name: str):
    s = Skill(skill_name=skill_name)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

def update_skill(db: Session, skill_id: int, skill_name: str):
    s = get_skill(db, skill_id)
    if s:
        s.skill_name = skill_name
        db.commit()
    return s

def delete_skill(db: Session, skill_id: int):
    s = get_skill(db, skill_id)
    if s:
        db.delete(s)
        db.commit()
    return s


# ==================== ProfileSkills ====================

def get_profile_skills(db: Session):
    return db.query(ProfileSkill).order_by(ProfileSkill.profile_skill_id).all()

def get_profile_skill(db: Session, profile_skill_id: int):
    return db.query(ProfileSkill).filter(ProfileSkill.profile_skill_id == profile_skill_id).first()

def create_profile_skill(db: Session, profile_id: int, skill_id: int):
    ps = ProfileSkill(profile_id=profile_id, skill_id=skill_id)
    db.add(ps)
    db.commit()
    db.refresh(ps)
    return ps

def update_profile_skill(db: Session, profile_skill_id: int, profile_id: int, skill_id: int):
    ps = get_profile_skill(db, profile_skill_id)
    if ps:
        ps.profile_id = profile_id
        ps.skill_id = skill_id
        db.commit()
    return ps

def delete_profile_skill(db: Session, profile_skill_id: int):
    ps = get_profile_skill(db, profile_skill_id)
    if ps:
        db.delete(ps)
        db.commit()
    return ps


# ==================== Messages ====================

def get_messages(db: Session):
    return db.query(Message).order_by(Message.sent_at.desc()).all()

def get_message(db: Session, message_id: int):
    return db.query(Message).filter(Message.message_id == message_id).first()

def create_message(db: Session, sender_id: int, receiver_id: int, message_body: str):
    m = Message(sender_id=sender_id, receiver_id=receiver_id, message_body=message_body)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

def update_message(db: Session, message_id: int, sender_id: int, receiver_id: int, message_body: str):
    m = get_message(db, message_id)
    if m:
        m.sender_id = sender_id
        m.receiver_id = receiver_id
        m.message_body = message_body
        db.commit()
    return m

def delete_message(db: Session, message_id: int):
    m = get_message(db, message_id)
    if m:
        db.delete(m)
        db.commit()
    return m


# ==================== Users ====================

def get_users(db: Session):
    return db.query(User).order_by(User.id).all()

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, password: str, role: str, profile_id: int | None = None):
    u = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        profile_id=profile_id
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

def update_user(db: Session, user_id: int, username: str, role: str, profile_id: int | None, password: str | None = None):
    u = get_user(db, user_id)
    if u:
        u.username = username
        u.role = role
        u.profile_id = profile_id
        if password:
            u.password_hash = hash_password(password)
        db.commit()
    return u

def delete_user(db: Session, user_id: int):
    u = get_user(db, user_id)
    if u:
        db.delete(u)
        db.commit()
    return u
