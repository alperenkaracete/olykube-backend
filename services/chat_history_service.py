from sqlalchemy.orm import Session
import models

def save_chat_history(db: Session, agent_id: int, thread_id: str, messages: list):
    existing = db.query(models.ChatHistory).filter(
        models.ChatHistory.agent_id == agent_id,
        models.ChatHistory.thread_id == thread_id
    ).first()

    if existing:
        existing.messages = messages
        db.commit()

    else:
        history = models.ChatHistory(
            agent_id=agent_id,
            thread_id=thread_id,
            messages=messages
        )
        db.add(history)
        db.commit()            

def get_chat_history(db: Session, agent_id: int, thread_id: str):
    history = db.query(models.ChatHistory).filter(
        models.ChatHistory.agent_id == agent_id,
        models.ChatHistory.thread_id == thread_id
    ).first()

    if history:
        return history.messages
    else:
        return []