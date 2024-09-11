from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Annotated
import models
from sessions import engine, SessionLocal
from sqlalchemy.orm import Session
import uvicorn
from auth import router as auth_router ,get_current_user
from file_handlers import router as file_handle_router
app = FastAPI()
app.include_router(auth_router)
app.include_router(file_handle_router)
models.Base.metadata.create_all(bind=engine)

class Choice(BaseModel):
    choice : str
    is_correct : bool

class Question(BaseModel):
    question : str
    choice : List[Choice]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@app.get("/", status_code=status.HTTP_200_OK)
async def user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    return {"User" : user}

@app.get("/question/{question_id}")
async def read_question(question_id : int, db : db_dependency):
    result = db.query(models.Questions).filter(models.Questions.id == question_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Question is not Found!")
    return result
    
@app.get("/choices/{question_id}")
async def get_choices(question_id : int , db: db_dependency):
    result = db.query(models.Choices).filter(models.Choices.question_id == question_id).all()
    if not result:
        raise HTTPException(status_code=404, detail="Choices is not Found!")
    return result

@app.post("/questions")
async def create_questions(question: Question, db : db_dependency):
    db_question = models.Questions(question=question.question)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    for choice in question.choice:
        db_choice = models.Choices(choice = choice.choice, is_correct= choice.is_correct, question_id = db_question.id)
        db.add(db_choice)
    db.commit()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)