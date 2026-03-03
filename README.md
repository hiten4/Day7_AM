# Day 7 — Python Dev Environment Setup

## Files in this submission

| File | Purpose |
|---|---|
| `onboard.py` | Main script — Parts A & B |
| `requirements.txt` | Pinned dependencies |
| `.pylintrc` | Beginner-friendly pylint config — Part D |
| `setup_report.txt` | Auto-generated on each run |
| `ANSWERS.md` | Written answers for Parts C & D |

## How to run

```bash
# 1. Create and activate virtual environment
python -m venv onboarding_env
source onboarding_env/bin/activate   # Windows: onboarding_env\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run basic check
python onboard.py

# 4. Run with verbose output
python onboard.py --verbose

# 5. Run with auto-fix for missing packages
python onboard.py --fix

# 6. Format with Black
black onboard.py

# 7. Check with Pylint
pylint onboard.py --rcfile=.pylintrc
```
