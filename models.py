from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from sessions import Base

class Questions(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key = True, index=True)
    question = Column(String, index=True)

class Choices(Base):
    __tablename__ = 'choices'

    id =  Column(Integer, primary_key = True, index=True)
    choice = Column(String, index=True)
    is_correct = Column(Boolean, default=False)
    question_id = Column(Integer, ForeignKey("questions.id"))

class Users(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key = True, index=True)
    username = Column(String, unique= True)
    hashed_password = Column(String)