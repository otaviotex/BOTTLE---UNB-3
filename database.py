from sqlalchemy import create_engine, Column, Integer, String, Date, Time, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

engine = create_engine("sqlite:///clinica.db", echo=False)

Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class Medico(Base):
    __tablename__ = "medicos"

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    idade = Column(Integer, nullable=False)
    genero = Column(String, nullable=False)
    crm = Column(String, unique=True, nullable=False)
    especialidade = Column(String, nullable=False)
    senha = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    agendamentos = relationship("Agendamento", back_populates="medico")


class Agendamento(Base):
    __tablename__ = "agendamentos"

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    idade = Column(Integer, nullable=False)
    convenio = Column(String, nullable=False)
    especialidade = Column(String, nullable=False)
    data = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    email = Column(String, nullable=False)
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=True)
    medico = relationship("Medico", back_populates="agendamentos")


Base.metadata.create_all(engine)