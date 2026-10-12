"""Swappable integrations. Defaults deliberately avoid external transmissions."""
from dataclasses import dataclass
from typing import Protocol
import re

@dataclass(frozen=True)
class FitResult:
    score:int
    explanation:str
    matched:list[str]
    missing:list[str]

class AIService(Protocol):
    def assess_fit(self,requirements:str,evidence:str)->FitResult: ...
    def generate_job_description(self,title:str,department:str)->str: ...

class LocalAIService:
    """Transparent keyword heuristic, not a predictive hiring model."""
    STOP={'para','com','uma','por','dos','das','que','entre','como','nos','nas','ser','ter'}
    def assess_fit(self,requirements:str,evidence:str)->FitResult:
        required=set(re.findall(r'\w{3,}',requirements.lower()))-self.STOP
        observed=set(re.findall(r'\w{3,}',evidence.lower()))
        matched=sorted(required&observed)
        missing=sorted(required-observed)
        score=round(100*len(matched)/len(required)) if required else 50
        explanation=f'Heurística local — termos atendidos: {", ".join(matched) or "nenhum"}. Ausentes: {", ".join(missing) or "nenhum"}. Não substitui avaliação humana.'
        return FitResult(score,explanation,matched,missing)
    def generate_job_description(self,title:str,department:str)->str:
        return f'Buscamos uma pessoa para atuar como {title} em {department}, com colaboração, responsabilidade e foco em melhoria contínua.'

class CommunicationProvider(Protocol):
    def queue(self,db,company_id:int,application_id:int,channel:str,subject:str,body:str):...

class MockCommunicationProvider:
    """Persists messages; never sends mail, WhatsApp or external notifications."""
    def queue(self,db,company_id:int,application_id:int,channel:str,subject:str,body:str):
        from .models import Communication
        msg=Communication(company_id=company_id,application_id=application_id,channel=channel,subject=subject,body=body,status='queued_mock')
        db.add(msg)
        return msg

class EmailProvider(MockCommunicationProvider):pass
class WhatsAppProvider(MockCommunicationProvider):pass

class StorageProvider(Protocol):
    def store(self,company_id:int,key:str,content:bytes):...

class LocalPrivateStorage:
    def __init__(self,root):self.root=root
    def store(self,company_id:int,key:str,content:bytes):
        folder=self.root/str(company_id);folder.mkdir(parents=True,exist_ok=True)
        target=folder/key;target.write_bytes(content)
        return target

ai_service:AIService=LocalAIService()
communications:CommunicationProvider=MockCommunicationProvider()
