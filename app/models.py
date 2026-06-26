from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Profile(Base):
    """Профили пользователей."""
    __tablename__ = "profiles"

    profile_id = Column(Integer, primary_key=True, index=True)
    profile_name = Column(String(200), nullable=False)
    job_title = Column(String(200), nullable=True)
    company_name = Column(String(200), nullable=True)

    # Связи
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    sent_connections = relationship(
        "Connection", foreign_keys="Connection.from_profile_id",
        back_populates="from_profile", cascade="all, delete-orphan"
    )
    received_connections = relationship(
        "Connection", foreign_keys="Connection.to_profile_id",
        back_populates="to_profile", cascade="all, delete-orphan"
    )
    profile_skills = relationship("ProfileSkill", back_populates="profile", cascade="all, delete-orphan")
    sent_messages = relationship(
        "Message", foreign_keys="Message.sender_id",
        back_populates="sender", cascade="all, delete-orphan"
    )
    received_messages = relationship(
        "Message", foreign_keys="Message.receiver_id",
        back_populates="receiver", cascade="all, delete-orphan"
    )
    user = relationship("User", back_populates="profile", uselist=False)


class Connection(Base):
    """Профессиональные контакты между профилями."""
    __tablename__ = "connections"

    connection_id = Column(Integer, primary_key=True, index=True)
    from_profile_id = Column(Integer, ForeignKey("profiles.profile_id", ondelete="CASCADE"), nullable=False)
    to_profile_id = Column(Integer, ForeignKey("profiles.profile_id", ondelete="CASCADE"), nullable=False)

    from_profile = relationship("Profile", foreign_keys=[from_profile_id], back_populates="sent_connections")
    to_profile = relationship("Profile", foreign_keys=[to_profile_id], back_populates="received_connections")

    __table_args__ = (
        CheckConstraint("from_profile_id != to_profile_id", name="check_no_self_connection"),
    )


class Post(Base):
    """Публикации / сообщения."""
    __tablename__ = "posts"

    post_id = Column(Integer, primary_key=True, index=True)
    post_content = Column(Text, nullable=False)
    posted_by_profile_id = Column(Integer, ForeignKey("profiles.profile_id", ondelete="CASCADE"), nullable=False)
    creation_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    author = relationship("Profile", back_populates="posts")


class Skill(Base):
    """Навыки."""
    __tablename__ = "skills"

    skill_id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String(150), nullable=False, unique=True)

    profile_skills = relationship("ProfileSkill", back_populates="skill", cascade="all, delete-orphan")


class ProfileSkill(Base):
    """Связь профиля и навыка."""
    __tablename__ = "profile_skills"

    profile_skill_id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.profile_id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), nullable=False)

    profile = relationship("Profile", back_populates="profile_skills")
    skill = relationship("Skill", back_populates="profile_skills")

    __table_args__ = (
        UniqueConstraint("profile_id", "skill_id", name="uq_profile_skill"),
    )


class Message(Base):
    """Личные сообщения между профилями."""
    __tablename__ = "messages"

    message_id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("profiles.profile_id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("profiles.profile_id", ondelete="CASCADE"), nullable=False)
    message_body = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sender = relationship("Profile", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("Profile", foreign_keys=[receiver_id], back_populates="received_messages")


class User(Base):
    """Пользователи для авторизации."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # admin / user
    profile_id = Column(Integer, ForeignKey("profiles.profile_id", ondelete="SET NULL"), nullable=True)

    profile = relationship("Profile", back_populates="user")
