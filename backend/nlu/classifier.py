import re
from typing import Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from backend.nlu.normalize import normalize_text
from backend.nlu.intents import Intent
from backend.nlu.entities import extract_entities

TRAINING_CORPUS = [
    # GET_ATTENDANCE
    ("show my attendance", Intent.GET_ATTENDANCE),
    ("what is my attendance", Intent.GET_ATTENDANCE),
    ("check my attendance percentage", Intent.GET_ATTENDANCE),
    ("attendance details", Intent.GET_ATTENDANCE),
    ("how much attendance do i have", Intent.GET_ATTENDANCE),
    ("view attendance", Intent.GET_ATTENDANCE),
    
    # GET_TIMETABLE
    ("show my timetable", Intent.GET_TIMETABLE),
    ("what is my schedule today", Intent.GET_TIMETABLE),
    ("class timetable", Intent.GET_TIMETABLE),
    ("view class schedule", Intent.GET_TIMETABLE),
    ("what classes do i have today", Intent.GET_TIMETABLE),
    
    # GET_HOLIDAYS
    ("show holidays", Intent.GET_HOLIDAYS),
    ("when is the next holiday", Intent.GET_HOLIDAYS),
    ("college holiday list", Intent.GET_HOLIDAYS),
    ("upcoming holidays", Intent.GET_HOLIDAYS),
    
    # GET_EXAM_DATES
    ("show exam dates", Intent.GET_EXAM_DATES),
    ("when are the exams", Intent.GET_EXAM_DATES),
    ("exam schedule", Intent.GET_EXAM_DATES),
    ("midterm dates", Intent.GET_EXAM_DATES),
    ("calendar exams", Intent.GET_EXAM_DATES),
    
    # GET_MY_REQUESTS
    ("show my requests", Intent.GET_MY_REQUESTS),
    ("my leave status", Intent.GET_MY_REQUESTS),
    ("check my request status", Intent.GET_MY_REQUESTS),
    ("view submitted requests", Intent.GET_MY_REQUESTS),
    
    # SUBMIT_LEAVE
    ("i need leave", Intent.SUBMIT_LEAVE),
    ("apply for leave", Intent.SUBMIT_LEAVE),
    ("i want to take leave tomorrow", Intent.SUBMIT_LEAVE),
    ("submit a leave request", Intent.SUBMIT_LEAVE),
    ("request leave", Intent.SUBMIT_LEAVE),
    
    # SUBMIT_ON_DUTY
    ("apply for on duty", Intent.SUBMIT_ON_DUTY),
    ("i need od", Intent.SUBMIT_ON_DUTY),
    ("submit on duty request", Intent.SUBMIT_ON_DUTY),
    ("od for hackathon", Intent.SUBMIT_ON_DUTY),
    
    # LIST_PENDING
    ("show pending requests", Intent.LIST_PENDING),
    ("list pending leave requests", Intent.LIST_PENDING),
    ("pending approvals", Intent.LIST_PENDING),
    ("view student requests to approve", Intent.LIST_PENDING),
    
    # APPROVE_REQUEST
    ("approve request", Intent.APPROVE_REQUEST),
    ("approve request REQ-9012", Intent.APPROVE_REQUEST),
    ("accept the request", Intent.APPROVE_REQUEST),
    ("approve it", Intent.APPROVE_REQUEST),
    
    # REJECT_REQUEST
    ("reject request", Intent.REJECT_REQUEST),
    ("reject request REQ-9012", Intent.REJECT_REQUEST),
    ("deny the request", Intent.REJECT_REQUEST),
    
    # GET_COURSES
    ("what courses do you offer", Intent.GET_COURSES),
    ("courses offered", Intent.GET_COURSES),
    ("list of engineering degrees", Intent.GET_COURSES),
    ("available branches in btech", Intent.GET_COURSES),
    
    # GET_ELIGIBILITY
    ("what are the admission requirements", Intent.GET_ELIGIBILITY),
    ("admission eligibility criteria", Intent.GET_ELIGIBILITY),
    ("who is eligible for btech", Intent.GET_ELIGIBILITY),
    
    # GET_COLLEGE_INFO
    ("college information", Intent.GET_COLLEGE_INFO),
    ("tell me about kit", Intent.GET_COLLEGE_INFO),
    ("about knotopian institute of technology", Intent.GET_COLLEGE_INFO),
    ("where is kit located", Intent.GET_COLLEGE_INFO),
    
    # CONFIRM_ACTION
    ("yes", Intent.CONFIRM_ACTION),
    ("confirm", Intent.CONFIRM_ACTION),
    ("yes submit it", Intent.CONFIRM_ACTION),
    ("proceed", Intent.CONFIRM_ACTION),
    ("yes please", Intent.CONFIRM_ACTION),
    
    # CANCEL_ACTION
    ("no", Intent.CANCEL_ACTION),
    ("cancel", Intent.CANCEL_ACTION),
    ("do not submit", Intent.CANCEL_ACTION),
    ("stop", Intent.CANCEL_ACTION),
    ("never mind", Intent.CANCEL_ACTION)
]

class IntentClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        self.model = LogisticRegression(max_iter=200, random_state=42)
        self._train()
        
    def _train(self):
        texts = [normalize_text(t) for t, _ in TRAINING_CORPUS]
        labels = [intent.value for _, intent in TRAINING_CORPUS]
        
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)
        
    def classify(self, text: str) -> Tuple[str, float, Dict[str, Any]]:
        norm = normalize_text(text)
        entities = extract_entities(text)
        
        # 1. Fast path for strict confirmation/cancellation
        if norm in ["yes", "confirm", "proceed", "yes submit it", "yes please", "sure"]:
            return Intent.CONFIRM_ACTION.value, 1.0, entities
        if norm in ["no", "cancel", "stop", "abort", "never mind"]:
            return Intent.CANCEL_ACTION.value, 1.0, entities
            
        # 2. Fast path for exact matches
        for phrase, intent in TRAINING_CORPUS:
            if norm == normalize_text(phrase):
                return intent.value, 0.99, entities
                
        # 3. Statistical TF-IDF classification
        X = self.vectorizer.transform([norm])
        probs = self.model.predict_proba(X)[0]
        best_idx = probs.argmax()
        best_score = float(probs[best_idx])
        best_intent = self.model.classes_[best_idx]
        
        # Rejection threshold
        if best_score < 0.25:
            return Intent.UNKNOWN.value, best_score, entities
            
        return best_intent, round(best_score, 3), entities

intent_classifier = IntentClassifier()

