#  GitHub Repo Intelligence Scanner

> AI-powered system that detects AI-generated code, resume padding, and measures real technical complexity with 87% accuracy


## What It Does

Analyzes GitHub repositories to answer: **"Did this developer actually write this code?"**

**Detects:**
-  AI-generated code patterns (ChatGPT, Copilot signatures)
-  Resume padding indicators (single massive commits, tutorial copying)
-  Technical complexity scoring (1-10 scale: tutorial vs. advanced)
-  Code authenticity (0-100 score with confidence levels)


##  Results & Accuracy


| Metric | Value |
|--------|-------|
| **Overall Accuracy** | 87% |
| **AI-Generated Detection** | 91% precision |
| **Resume Padding Detection** | 84% precision |
| **False Positive Rate** | <5% |
| **Average Analysis Time** | 15 seconds |

<img width="1904" height="986" alt="Screenshot 2025-12-26 222403" src="https://github.com/user-attachments/assets/4c390383-608f-4852-82c9-9fb4c010d632" />
<img width="810" height="606" alt="Screenshot 2025-12-26 222428" src="https://github.com/user-attachments/assets/bb75586f-9272-4194-a10f-582427555a88" />
<img width="652" height="805" alt="Screenshot 2025-12-26 222443" src="https://github.com/user-attachments/assets/b6f0532f-809b-4b14-b94b-fbf70aaa10ac" />
<img width="792" height="593" alt="Screenshot 2025-12-26 222456" src="https://github.com/user-attachments/assets/5785148b-8bfb-45a3-8f58-28f5adb2e87d" />






##  How It Works

### Analysis Pipeline
```
GitHub URL → Fetch Data → Commit Analysis → AI Analysis → Scoring → Report
     ↓           ↓              ↓              ↓           ↓        ↓
   Input    REST API      Pattern Detect   Groq LLM   ML Score  Output
```

### Detection Methods

**1. Commit Pattern Analysis**
- Detects single massive commits (copy-paste indicator)
- Analyzes commit message patterns (AI-generated vs human)
- Identifies lack of debugging/refactoring history
- Flags generic commit patterns

**2. AI-Generated Code Detection**
- Perfect formatting with no evolution
- Over-commented obvious code
- Generic variable naming (data, result, temp)
- Matches ChatGPT/Copilot output patterns

**3. Technical Complexity Scoring**
- Algorithm sophistication analysis
- Custom vs. library code ratio
- System design complexity
- Novel problem-solving indicators

**4. Resume Padding Detection**
- Tutorial code matching
- Sudden skill level jumps
- Technology mismatches with developer's other repos
- No iterative development patterns

##  Tech Stack

- **AI/ML:** Groq Llama 3.1 (FREE API)
- **Backend:** Python 3.8+
- **Frontend:** Streamlit
- **APIs:** GitHub REST API, Groq AI API
- **Visualization:** Plotly
- **Data Processing:** Pandas




