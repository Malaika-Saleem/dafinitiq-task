import sys
import os
from sqlmodel import Session, select

# Ensure project root is on sys.path so 'app' package imports resolve
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.db import engine
from app.models import User
from app.auth import hash_password

email = 'malaikasaleem555@gmail.com'
newpass = 'hi'

with Session(engine) as s:
    q = select(User).where(User.email == email)
    user = s.exec(q).first()
    if not user:
        print('USER_NOT_FOUND')
        raise SystemExit(1)
    user.hashed_password = hash_password(newpass)
    s.add(user)
    s.commit()
    print('UPDATED', user.id, user.email)
