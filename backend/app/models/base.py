# backend/app/models/base.py
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.sql import text

class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:    
        return cls.__name__.lower() + "s"     

    __allow_unmapped__ = True                    

    def __repr__(self) -> str:   
        pk = getattr(self, "id", "∅")
        return f"<{self.__class__.__name__} {pk}>"
