# Agent 1: LinkedIn Extraction Logic - Hackathon Enhanced

## Hackathon Detection Keywords
- "hackathon", "hack day", "coding competition"
- "48-hour build", "weekend hack", "innovation challenge"
- Platform-specific: "AngelHack", "TechCrunch Disrupt", "Junction"
- Achievement indicators: "winner", "finalist", "best hack", "people's choice"

## Achievement Pattern Recognition
- **Recent wins** (last 6 months): 6 points + 4x multiplier = 24 points
- **Team leadership**: "led team of X", "organized hackathon team"
- **Technical innovation**: "built AI solution", "implemented ML model"
- **Speed indicators**: "24-hour build", "rapid prototype"

## Extraction Priority Matrix
1. **Recency weight**: 4x for last 3 months, 2x for last 6 months
2. **Achievement level**: Winner (6pts), Finalist (4pts), Participant (2pts)
3. **Technical complexity**: AI/ML solutions get 2x multiplier
4. **Team dynamics**: Leadership roles get 1.5x multiplier

## Learning Velocity Signals
- Course completions with timestamps
- New tool adoption patterns in project descriptions
- GitHub activity showing technology exploration
- Certification dates and progression patterns

**Output**: Structured JSON with hackathon scores, recency weights, and learning velocity metrics