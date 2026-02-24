"""
VelocityHire Agent 3: Final Evaluation Agent
Production-ready implementation with comprehensive candidate evaluation and decision making
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import redis
import aiohttp
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog
from enum import Enum
import statistics

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
EVALUATION_REQUESTS = Counter('evaluation_requests_total', 'Total evaluation requests')
EVALUATION_DURATION = Histogram('evaluation_duration_seconds', 'Time spent on evaluations')
EVALUATIONS_COMPLETED = Gauge('evaluations_completed_current', 'Current completed evaluations')
EVALUATION_ERRORS = Counter('evaluation_errors_total', 'Total evaluation errors', ['error_type'])
HIRE_RECOMMENDATIONS = Counter('hire_recommendations_total', 'Total hire recommendations', ['decision'])

class HiringDecision(Enum):
    STRONG_HIRE = "strong_hire"
    HIRE = "hire"
    NO_HIRE = "no_hire"
    STRONG_NO_HIRE = "strong_no_hire"

class EvaluationCriteria(Enum):
    TECHNICAL_SKILLS = "technical_skills"
    PROBLEM_SOLVING = "problem_solving"
    COMMUNICATION = "communication"
    CULTURAL_FIT = "cultural_fit"
    EXPERIENCE_MATCH = "experience_match"
    GROWTH_POTENTIAL = "growth_potential"

@dataclass
class CandidateProfile:
    """Complete candidate profile for evaluation"""
    candidate_id: str
    name: str
    email: str
    skills: List[str]
    experience_years: int
    location: str
    resume_score: float
    source_platform: str
    
    # Assessment results
    assessment_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Additional evaluation data
    portfolio_url: Optional[str] = None
    references: List[Dict[str, Any]] = field(default_factory=list)
    salary_expectation: Optional[float] = None
    availability_date: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'candidate_id': self.candidate_id,
            'name': self.name,
            'email': self.email,
            'skills': self.skills,
            'experience_years': self.experience_years,
            'location': self.location,
            'resume_score': self.resume_score,
            'source_platform': self.source_platform,
            'assessment_results': self.assessment_results,
            'portfolio_url': self.portfolio_url,
            'references': self.references,
            'salary_expectation': self.salary_expectation,
            'availability_date': self.availability_date
        }

@dataclass
class EvaluationScore:
    """Individual evaluation criterion score"""
    criteria: EvaluationCriteria
    score: float  # 0-100
    weight: float  # Importance weight
    reasoning: str
    confidence: float  # 0-1

@dataclass
class FinalEvaluation:
    """Final evaluation result"""
    candidate_id: str
    evaluation_id: str
    overall_score: float
    decision: HiringDecision
    criteria_scores: List[EvaluationScore]
    strengths: List[str]
    concerns: List[str]
    recommendation_summary: str
    evaluator_notes: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'candidate_id': self.candidate_id,
            'evaluation_id': self.evaluation_id,
            'overall_score': self.overall_score,
            'decision': self.decision.value,
            'criteria_scores': [
                {
                    'criteria': score.criteria.value,
                    'score': score.score,
                    'weight': score.weight,
                    'reasoning': score.reasoning,
                    'confidence': score.confidence
                }
                for score in self.criteria_scores
            ],
            'strengths': self.strengths,
            'concerns': self.concerns,
            'recommendation_summary': self.recommendation_summary,
            'evaluator_notes': self.evaluator_notes,
            'timestamp': self.timestamp.isoformat()
        }

class CircuitBreaker:
    """Circuit breaker for external services"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'
    
    async def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
            
            raise e

class FinalEvaluationAgent:
    """Production-ready final evaluation agent with comprehensive decision making"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.circuit_breaker = CircuitBreaker()
        self.session = None
        self.logger = logger.bind(agent="evaluation")
        
        # Evaluation criteria weights (configurable per role)
        self.default_criteria_weights = {
            EvaluationCriteria.TECHNICAL_SKILLS: 0.30,
            EvaluationCriteria.PROBLEM_SOLVING: 0.25,
            EvaluationCriteria.COMMUNICATION: 0.15,
            EvaluationCriteria.CULTURAL_FIT: 0.10,
            EvaluationCriteria.EXPERIENCE_MATCH: 0.15,
            EvaluationCriteria.GROWTH_POTENTIAL: 0.05
        }
        
        # Decision thresholds
        self.decision_thresholds = {
            HiringDecision.STRONG_HIRE: 85.0,
            HiringDecision.HIRE: 70.0,
            HiringDecision.NO_HIRE: 50.0,
            HiringDecision.STRONG_NO_HIRE: 0.0
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check endpoint"""
        try:
            # Check Redis connection
            redis_status = self.redis_client.ping()
            
            # Check evaluation criteria configuration
            criteria_count = len(self.default_criteria_weights)
            
            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'redis': redis_status,
                'evaluation_criteria': criteria_count,
                'circuit_breaker': self.circuit_breaker.state,
                'decision_thresholds': {k.value: v for k, v in self.decision_thresholds.items()}
            }
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    async def evaluate_candidate(self, candidate_profile: CandidateProfile, 
                               job_requirements: Dict[str, Any],
                               custom_weights: Optional[Dict[str, float]] = None) -> FinalEvaluation:
        """Perform comprehensive candidate evaluation"""
        EVALUATION_REQUESTS.inc()
        start_time = time.time()
        
        try:
            self.logger.info(
                "Starting candidate evaluation",
                candidate_id=candidate_profile.candidate_id,
                job_title=job_requirements.get('title', 'Unknown')
            )
            
            evaluation_id = str(uuid.uuid4())
            
            # Use custom weights if provided, otherwise use defaults
            criteria_weights = custom_weights or self.default_criteria_weights
            
            # Evaluate each criterion
            criteria_scores = []
            
            # Technical Skills Evaluation
            tech_score = await self._evaluate_technical_skills(
                candidate_profile, job_requirements
            )
            criteria_scores.append(EvaluationScore(
                criteria=EvaluationCriteria.TECHNICAL_SKILLS,
                score=tech_score['score'],
                weight=criteria_weights[EvaluationCriteria.TECHNICAL_SKILLS],
                reasoning=tech_score['reasoning'],
                confidence=tech_score['confidence']
            ))
            
            # Problem Solving Evaluation
            problem_solving_score = await self._evaluate_problem_solving(
                candidate_profile, job_requirements
            )
            criteria_scores.append(EvaluationScore(
                criteria=EvaluationCriteria.PROBLEM_SOLVING,
                score=problem_solving_score['score'],
                weight=criteria_weights[EvaluationCriteria.PROBLEM_SOLVING],
                reasoning=problem_solving_score['reasoning'],
                confidence=problem_solving_score['confidence']
            ))
            
            # Communication Evaluation
            comm_score = await self._evaluate_communication(
                candidate_profile, job_requirements
            )
            criteria_scores.append(EvaluationScore(
                criteria=EvaluationCriteria.COMMUNICATION,
                score=comm_score['score'],
                weight=criteria_weights[EvaluationCriteria.COMMUNICATION],
                reasoning=comm_score['reasoning'],
                confidence=comm_score['confidence']
            ))
            
            # Cultural Fit Evaluation
            culture_score = await self._evaluate_cultural_fit(
                candidate_profile, job_requirements
            )
            criteria_scores.append(EvaluationScore(
                criteria=EvaluationCriteria.CULTURAL_FIT,
                score=culture_score['score'],
                weight=criteria_weights[EvaluationCriteria.CULTURAL_FIT],
                reasoning=culture_score['reasoning'],
                confidence=culture_score['confidence']
            ))
            
            # Experience Match Evaluation
            exp_score = await self._evaluate_experience_match(
                candidate_profile, job_requirements
            )
            criteria_scores.append(EvaluationScore(
                criteria=EvaluationCriteria.EXPERIENCE_MATCH,
                score=exp_score['score'],
                weight=criteria_weights[EvaluationCriteria.EXPERIENCE_MATCH],
                reasoning=exp_score['reasoning'],
                confidence=exp_score['confidence']
            ))
            
            # Growth Potential Evaluation
            growth_score = await self._evaluate_growth_potential(
                candidate_profile, job_requirements
            )
            criteria_scores.append(EvaluationScore(
                criteria=EvaluationCriteria.GROWTH_POTENTIAL,
                score=growth_score['score'],
                weight=criteria_weights[EvaluationCriteria.GROWTH_POTENTIAL],
                reasoning=growth_score['reasoning'],
                confidence=growth_score['confidence']
            ))
            
            # Calculate overall score
            overall_score = sum(
                score.score * score.weight for score in criteria_scores
            )
            
            # Determine hiring decision
            decision = self._determine_hiring_decision(overall_score)
            
            # Generate strengths and concerns
            strengths, concerns = self._analyze_strengths_concerns(criteria_scores)
            
            # Generate recommendation summary
            recommendation_summary = self._generate_recommendation_summary(
                candidate_profile, overall_score, decision, strengths, concerns
            )
            
            # Create final evaluation
            evaluation = FinalEvaluation(
                candidate_id=candidate_profile.candidate_id,
                evaluation_id=evaluation_id,
                overall_score=overall_score,
                decision=decision,
                criteria_scores=criteria_scores,
                strengths=strengths,
                concerns=concerns,
                recommendation_summary=recommendation_summary,
                evaluator_notes=f"Automated evaluation completed for {job_requirements.get('title', 'position')}"
            )
            
            # Store evaluation
            await self._store_evaluation(evaluation)
            
            # Update metrics
            EVALUATIONS_COMPLETED.inc()
            EVALUATION_DURATION.observe(time.time() - start_time)
            HIRE_RECOMMENDATIONS.labels(decision=decision.value).inc()
            
            self.logger.info(
                "Candidate evaluation completed",
                candidate_id=candidate_profile.candidate_id,
                overall_score=overall_score,
                decision=decision.value,
                duration=time.time() - start_time
            )
            
            return evaluation
            
        except Exception as e:
            EVALUATION_ERRORS.labels(error_type='evaluation').inc()
            self.logger.error("Candidate evaluation failed", error=str(e))
            raise
    
    async def _evaluate_technical_skills(self, candidate: CandidateProfile, 
                                       job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate technical skills based on assessments and requirements"""
        required_skills = set(skill.lower() for skill in job_requirements.get('skills', []))
        candidate_skills = set(skill.lower() for skill in candidate.skills)
        
        # Skill match percentage
        skill_match = len(required_skills & candidate_skills) / len(required_skills) if required_skills else 0
        
        # Assessment scores
        assessment_scores = []
        for assessment in candidate.assessment_results:
            if assessment.get('assessment_type') == 'coding_challenge':
                score_pct = (assessment.get('score', 0) / assessment.get('max_score', 1)) * 100
                assessment_scores.append(score_pct)
        
        avg_assessment_score = statistics.mean(assessment_scores) if assessment_scores else 50
        
        # Combined technical score
        technical_score = (skill_match * 40) + (avg_assessment_score * 0.6)
        
        reasoning = f"Skill match: {skill_match:.1%}, Assessment average: {avg_assessment_score:.1f}%"
        confidence = 0.9 if assessment_scores else 0.6
        
        return {
            'score': min(technical_score, 100),
            'reasoning': reasoning,
            'confidence': confidence
        }
    
    async def _evaluate_problem_solving(self, candidate: CandidateProfile, 
                                      job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate problem-solving abilities"""
        # Look for system design and coding challenge results
        problem_solving_scores = []
        
        for assessment in candidate.assessment_results:
            if assessment.get('assessment_type') in ['coding_challenge', 'system_design']:
                score_pct = (assessment.get('score', 0) / assessment.get('max_score', 1)) * 100
                problem_solving_scores.append(score_pct)
        
        if problem_solving_scores:
            avg_score = statistics.mean(problem_solving_scores)
            reasoning = f"Based on {len(problem_solving_scores)} problem-solving assessments"
            confidence = 0.8
        else:
            # Fallback to experience-based estimation
            exp_years = candidate.experience_years
            avg_score = min(50 + (exp_years * 5), 85)  # Experience-based estimation
            reasoning = "Estimated based on experience level (no direct assessments)"
            confidence = 0.4
        
        return {
            'score': avg_score,
            'reasoning': reasoning,
            'confidence': confidence
        }
    
    async def _evaluate_communication(self, candidate: CandidateProfile, 
                                    job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate communication skills"""
        # Look for technical interview results
        comm_scores = []
        
        for assessment in candidate.assessment_results:
            if assessment.get('assessment_type') == 'technical_interview':
                detailed_results = assessment.get('detailed_results', {})
                avg_response_length = detailed_results.get('average_response_length', 0)
                
                # Score based on response quality
                if avg_response_length > 100:
                    comm_scores.append(85)
                elif avg_response_length > 50:
                    comm_scores.append(70)
                else:
                    comm_scores.append(55)
        
        if comm_scores:
            avg_score = statistics.mean(comm_scores)
            reasoning = f"Based on technical interview performance"
            confidence = 0.7
        else:
            # Default score based on experience
            avg_score = 65  # Neutral assumption
            reasoning = "No direct communication assessment available"
            confidence = 0.3
        
        return {
            'score': avg_score,
            'reasoning': reasoning,
            'confidence': confidence
        }
    
    async def _evaluate_cultural_fit(self, candidate: CandidateProfile, 
                                   job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate cultural fit"""
        # Simple heuristics for cultural fit
        score = 70  # Base score
        
        # Location match
        job_location = job_requirements.get('location', '').lower()
        candidate_location = candidate.location.lower()
        
        if 'remote' in job_location or 'remote' in candidate_location:
            score += 10  # Remote flexibility bonus
        elif job_location in candidate_location or candidate_location in job_location:
            score += 5   # Location match bonus
        
        # Experience level match
        required_exp = job_requirements.get('experience_years', 0)
        exp_diff = abs(candidate.experience_years - required_exp)
        
        if exp_diff <= 1:
            score += 10
        elif exp_diff <= 3:
            score += 5
        
        reasoning = f"Location compatibility and experience level alignment"
        confidence = 0.5  # Cultural fit is subjective
        
        return {
            'score': min(score, 100),
            'reasoning': reasoning,
            'confidence': confidence
        }
    
    async def _evaluate_experience_match(self, candidate: CandidateProfile, 
                                       job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate experience match"""
        required_exp = job_requirements.get('experience_years', 0)
        candidate_exp = candidate.experience_years
        
        # Calculate experience match score
        if candidate_exp >= required_exp:
            # Candidate meets or exceeds requirements
            excess_exp = candidate_exp - required_exp
            if excess_exp <= 2:
                score = 90  # Perfect match
            elif excess_exp <= 5:
                score = 85  # Good match with extra experience
            else:
                score = 75  # May be overqualified
        else:
            # Candidate has less experience than required
            exp_deficit = required_exp - candidate_exp
            if exp_deficit <= 1:
                score = 80  # Close enough
            elif exp_deficit <= 2:
                score = 65  # Moderate gap
            else:
                score = 40  # Significant gap
        
        reasoning = f"Candidate has {candidate_exp} years vs {required_exp} required"
        confidence = 0.9
        
        return {
            'score': score,
            'reasoning': reasoning,
            'confidence': confidence
        }
    
    async def _evaluate_growth_potential(self, candidate: CandidateProfile, 
                                       job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate growth potential"""
        # Factors for growth potential
        score = 60  # Base score
        
        # Age/experience ratio (younger candidates with good skills = high potential)
        if candidate.experience_years < 3 and candidate.resume_score > 0.7:
            score += 20  # High potential junior
        elif candidate.experience_years < 7 and candidate.resume_score > 0.8:
            score += 15  # Strong mid-level with potential
        
        # Assessment performance
        for assessment in candidate.assessment_results:
            score_pct = (assessment.get('score', 0) / assessment.get('max_score', 1)) * 100
            if score_pct > 85:
                score += 10  # Excellent performance indicates potential
            elif score_pct > 70:
                score += 5   # Good performance
        
        # Portfolio/GitHub presence
        if candidate.portfolio_url:
            score += 10  # Shows initiative and continuous learning
        
        reasoning = "Based on performance, experience level, and demonstrated initiative"
        confidence = 0.6
        
        return {
            'score': min(score, 100),
            'reasoning': reasoning,
            'confidence': confidence
        }
    
    def _determine_hiring_decision(self, overall_score: float) -> HiringDecision:
        """Determine hiring decision based on overall score"""
        if overall_score >= self.decision_thresholds[HiringDecision.STRONG_HIRE]:
            return HiringDecision.STRONG_HIRE
        elif overall_score >= self.decision_thresholds[HiringDecision.HIRE]:
            return HiringDecision.HIRE
        elif overall_score >= self.decision_thresholds[HiringDecision.NO_HIRE]:
            return HiringDecision.NO_HIRE
        else:
            return HiringDecision.STRONG_NO_HIRE
    
    def _analyze_strengths_concerns(self, criteria_scores: List[EvaluationScore]) -> Tuple[List[str], List[str]]:
        """Analyze strengths and concerns from criteria scores"""
        strengths = []
        concerns = []
        
        for score in criteria_scores:
            if score.score >= 80:
                strengths.append(f"Strong {score.criteria.value.replace('_', ' ')}: {score.reasoning}")
            elif score.score < 60:
                concerns.append(f"Weak {score.criteria.value.replace('_', ' ')}: {score.reasoning}")
        
        return strengths, concerns
    
    def _generate_recommendation_summary(self, candidate: CandidateProfile, 
                                       overall_score: float, decision: HiringDecision,
                                       strengths: List[str], concerns: List[str]) -> str:
        """Generate comprehensive recommendation summary"""
        summary_parts = [
            f"Overall evaluation score: {overall_score:.1f}/100",
            f"Recommendation: {decision.value.replace('_', ' ').title()}"
        ]
        
        if strengths:
            summary_parts.append(f"Key strengths: {len(strengths)} areas of excellence")
        
        if concerns:
            summary_parts.append(f"Areas of concern: {len(concerns)} items to consider")
        
        if decision in [HiringDecision.STRONG_HIRE, HiringDecision.HIRE]:
            summary_parts.append("Candidate demonstrates strong potential for success in this role.")
        else:
            summary_parts.append("Candidate may not be the best fit for current requirements.")
        
        return " | ".join(summary_parts)
    
    async def get_evaluation_summary(self, candidate_ids: List[str]) -> Dict[str, Any]:
        """Get evaluation summary for multiple candidates"""
        try:
            evaluations = []
            
            for candidate_id in candidate_ids:
                evaluation_data = await self._get_evaluation(candidate_id)
                if evaluation_data:
                    evaluations.append(evaluation_data)
            
            if not evaluations:
                return {'message': 'No evaluations found'}
            
            # Calculate summary statistics
            scores = [eval_data['overall_score'] for eval_data in evaluations]
            decisions = [eval_data['decision'] for eval_data in evaluations]
            
            summary = {
                'total_candidates': len(evaluations),
                'average_score': statistics.mean(scores),
                'score_range': {'min': min(scores), 'max': max(scores)},
                'decisions': {
                    decision.value: decisions.count(decision.value) 
                    for decision in HiringDecision
                },
                'evaluations': evaluations
            }
            
            return summary
            
        except Exception as e:
            self.logger.error("Failed to get evaluation summary", error=str(e))
            raise
    
    async def _store_evaluation(self, evaluation: FinalEvaluation):
        """Store evaluation in Redis"""
        try:
            self.redis_client.setex(
                f"evaluation:{evaluation.candidate_id}",
                86400,  # 24 hours TTL
                json.dumps(evaluation.to_dict())
            )
        except Exception as e:
            self.logger.error("Failed to store evaluation", error=str(e))
            raise
    
    async def _get_evaluation(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve evaluation from Redis"""
        try:
            data = self.redis_client.get(f"evaluation:{candidate_id}")
            return json.loads(data) if data else None
        except Exception as e:
            self.logger.error("Failed to retrieve evaluation", error=str(e))
            return None

# FastAPI integration
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Union

app = FastAPI(title="VelocityHire Evaluation Agent", version="1.0.0")

# Global agent instance
evaluation_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize the evaluation agent on startup"""
    global evaluation_agent
    evaluation_agent = FinalEvaluationAgent()
    await evaluation_agent.__aenter__()
    
    # Start Prometheus metrics server
    start_http_server(8003)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global evaluation_agent
    if evaluation_agent:
        await evaluation_agent.__aexit__(None, None, None)

class EvaluateRequest(BaseModel):
    candidate_profile: Dict[str, Any]
    job_requirements: Dict[str, Any]
    custom_weights: Optional[Dict[str, float]] = None

class SummaryRequest(BaseModel):
    candidate_ids: List[str]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not evaluation_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return await evaluation_agent.health_check()

@app.post("/evaluate-candidate")
async def evaluate_candidate_endpoint(request: EvaluateRequest):
    """Evaluate candidate endpoint"""
    if not evaluation_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Convert dict to CandidateProfile
        candidate_profile = CandidateProfile(**request.candidate_profile)
        
        evaluation = await evaluation_agent.evaluate_candidate(
            candidate_profile,
            request.job_requirements,
            request.custom_weights
        )
        
        return {
            "status": "success",
            "evaluation": evaluation.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluation-summary")
async def evaluation_summary_endpoint(request: SummaryRequest):
    """Get evaluation summary endpoint"""
    if not evaluation_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        summary = await evaluation_agent.get_evaluation_summary(request.candidate_ids)
        return {
            "status": "success",
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get evaluation metrics"""
    return {
        "requests_total": EVALUATION_REQUESTS._value._value,
        "evaluations_completed": EVALUATIONS_COMPLETED._value._value,
        "errors_total": EVALUATION_ERRORS._value._value,
        "hire_recommendations": {
            decision.value: HIRE_RECOMMENDATIONS.labels(decision=decision.value)._value._value
            for decision in HiringDecision
        },
        "circuit_breaker_state": evaluation_agent.circuit_breaker.state if evaluation_agent else "unknown"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)