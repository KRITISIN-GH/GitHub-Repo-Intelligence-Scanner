from groq import Groq
import requests
from typing import Dict, List
import re
import json

class GitHubRepoAnalyzer:
    """
    Analyzes GitHub repositories to detect AI-generated code, 
    resume padding, and technical complexity
    """
    
    def __init__(self, groq_key: str):
        self.groq_client = Groq(api_key=groq_key)
        self.headers = {}
    
    def fetch_repo_data(self, repo_url: str) -> Dict:
        """Fetch repository data from GitHub API"""
        parts = repo_url.rstrip('/').split('/')
        
        if len(parts) < 2:
            return {"error": "Invalid GitHub URL"}
        
        owner, repo = parts[-2], parts[-1]
        
        try:
            # Repo info
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            repo_data = response.json()
            
            # Commits
            commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
            commits_response = requests.get(commits_url, timeout=10)
            commits = commits_response.json() if commits_response.ok else []
            
            # Languages
            languages_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
            lang_response = requests.get(languages_url, timeout=10)
            languages = lang_response.json() if lang_response.ok else {}
            
            # README
            readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
            readme_response = requests.get(readme_url, timeout=10)
            readme_content = ""
            if readme_response.ok:
                import base64
                readme_data = readme_response.json()
                readme_content = base64.b64decode(readme_data.get('content', '')).decode('utf-8', errors='ignore')
            
            return {
                "name": repo_data.get("name"),
                "description": repo_data.get("description", ""),
                "stars": repo_data.get("stargazers_count", 0),
                "forks": repo_data.get("forks_count", 0),
                "created_at": repo_data.get("created_at"),
                "updated_at": repo_data.get("updated_at"),
                "language": repo_data.get("language"),
                "languages": languages,
                "commits": commits[:20],
                "readme": readme_content[:5000],
                "owner": owner,
                "repo": repo
            }
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {"error": "Repository not found"}
            elif e.response.status_code == 403:
                return {"error": "Rate limit exceeded. Wait 1 hour."}
            else:
                return {"error": f"GitHub API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Failed to fetch repo: {str(e)}"}
    
    def analyze_commit_patterns(self, commits: List) -> Dict:
        """Analyze commit patterns"""
        if not commits:
            return {
                "total_commits": 0,
                "red_flags": ["No commit data available"],
                "commit_messages": [],
                "pattern_score": 20
            }
        
        commit_messages = []
        red_flags = []
        
        for commit in commits:
            msg = commit.get('commit', {}).get('message', '')
            commit_messages.append(msg)
        
        # Check patterns
        if len(commit_messages) > 0:
            perfect_count = sum(1 for msg in commit_messages 
                              if len(msg) > 50 and msg[0].isupper() and '.' in msg)
            if perfect_count / len(commit_messages) > 0.8:
                red_flags.append("Most commits have perfect grammar (AI-generated?)")
        
        if len(commits) < 5:
            red_flags.append("Very few commits (< 5)")
        
        generic_words = ['update', 'fix', 'initial commit', 'first commit', 'changes']
        if len(commit_messages) > 0:
            generic_count = sum(1 for msg in commit_messages 
                              if any(word in msg.lower() for word in generic_words))
            if generic_count / len(commit_messages) > 0.6:
                red_flags.append("Over 60% generic commit messages")
        
        return {
            "total_commits": len(commits),
            "red_flags": red_flags,
            "commit_messages": commit_messages[:10],
            "pattern_score": len(red_flags) * 15
        }
    
    def analyze_with_groq(self, repo_data: Dict) -> Dict:
        """Use Groq AI to analyze repository"""
        
        commit_msgs = []
        for commit in repo_data.get('commits', [])[:10]:
            msg = commit.get('commit', {}).get('message', '')
            if msg:
                commit_msgs.append(msg)
        
        prompt = f"""Analyze this GitHub repository for authenticity and technical complexity.

Repository: {repo_data.get('name')}
Description: {repo_data.get('description') or 'No description'}
Language: {repo_data.get('language') or 'Unknown'}
Stars: {repo_data.get('stars')}

Recent Commits:
{chr(10).join(commit_msgs) if commit_msgs else 'No commits'}

README:
{repo_data.get('readme', 'No README')[:2000]}

Analyze:
1. AI-Generated Code Score (0-100)
2. Resume Padding Score (0-100)
3. Technical Complexity (1-10)
4. Authenticity Score (0-100)

Respond with ONLY valid JSON:
{{
    "ai_generated_score": 45,
    "ai_indicators": ["indicator1", "indicator2"],
    "resume_padding_score": 30,
    "padding_indicators": ["indicator1"],
    "technical_complexity": 5,
    "complexity_reasoning": "explanation",
    "authenticity_score": 65,
    "authenticity_reasoning": "explanation",
    "overall_assessment": "SUSPICIOUS",
    "red_flags": ["flag1", "flag2"],
    "hiring_recommendation": "recommendation"
}}"""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",  # ✅ FIXED: Changed from llama-3.1-70b-versatile
                messages=[
                    {"role": "system", "content": "You are a code analyst. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*', '', response_text)
            
            try:
                return json.loads(response_text)
            except:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                return {"error": "Could not parse response"}
            
        except Exception as e:
            return {"error": f"Groq analysis failed: {str(e)}"}
    
    def calculate_final_score(self, groq_analysis: Dict, commit_analysis: Dict) -> Dict:
        """Calculate final authenticity score"""
        
        base_score = groq_analysis.get('authenticity_score', 50)
        commit_penalty = commit_analysis.get('pattern_score', 0)
        final_score = max(0, min(100, base_score - commit_penalty))
        
        if final_score >= 75:
            category = "✅ AUTHENTIC"
            risk = "Low"
            color = "green"
        elif final_score >= 50:
            category = "⚠️ SUSPICIOUS"
            risk = "Medium"
            color = "yellow"
        elif final_score >= 25:
            category = "🚨 LIKELY PADDED"
            risk = "High"
            color = "orange"
        else:
            category = "💀 FAKE/COPIED"
            risk = "Critical"
            color = "red"
        
        all_red_flags = []
        all_red_flags.extend(groq_analysis.get('red_flags', []))
        all_red_flags.extend(groq_analysis.get('ai_indicators', []))
        all_red_flags.extend(commit_analysis.get('red_flags', []))
        
        return {
            "authenticity_score": round(final_score, 1),
            "category": category,
            "risk_level": risk,
            "color": color,
            "ai_generated_score": groq_analysis.get('ai_generated_score', 0),
            "technical_complexity": groq_analysis.get('technical_complexity', 5),
            "red_flags": all_red_flags[:10],
            "hiring_recommendation": groq_analysis.get('hiring_recommendation', ''),
            "groq_analysis": groq_analysis,
            "commit_analysis": commit_analysis
        }
    
    def generate_report(self, repo_data: Dict, final_analysis: Dict) -> str:
        """Generate markdown report"""
        
        report = f"""# 🔍 GITHUB REPOSITORY ANALYSIS

## Repository: {repo_data.get('name')}
**URL:** https://github.com/{repo_data.get('owner')}/{repo_data.get('repo')}  
**Stars:** ⭐ {repo_data.get('stars')}

---

## 🎯 AUTHENTICITY SCORE: {final_analysis['authenticity_score']}/100

**Category:** {final_analysis['category']}  
**Risk Level:** {final_analysis['risk_level']}

---

## 📊 KEY METRICS

| Metric | Score |
|--------|-------|
| **AI-Generated Code** | {final_analysis['ai_generated_score']}/100 |
| **Technical Complexity** | {final_analysis['technical_complexity']}/10 |
| **Resume Padding Risk** | {final_analysis['groq_analysis'].get('resume_padding_score', 0)}/100 |

---

## 🚩 RED FLAGS ({len(final_analysis['red_flags'])})

"""
        
        if final_analysis['red_flags']:
            for i, flag in enumerate(final_analysis['red_flags'], 1):
                report += f"{i}. {flag}\n"
        else:
            report += "*No major red flags detected*\n"
        
        report += f"""
---

## 💡 HIRING RECOMMENDATION

{final_analysis['hiring_recommendation']}

---

## 🔬 DETAILED ANALYSIS

### Technical Complexity
{final_analysis['groq_analysis'].get('complexity_reasoning', 'N/A')}

### Authenticity Assessment
{final_analysis['groq_analysis'].get('authenticity_reasoning', 'N/A')}

---

*Generated by GitHub Repo Scanner • Powered by Groq AI*
"""
        
        return report
    
    def analyze_repository(self, repo_url: str) -> Dict:
        """Main analysis function"""
        
        print(f"🔍 Analyzing: {repo_url}")
        
        print("📥 Fetching data...")
        repo_data = self.fetch_repo_data(repo_url)
        
        if "error" in repo_data:
            return repo_data
        
        print("📊 Analyzing commits...")
        commit_analysis = self.analyze_commit_patterns(repo_data.get('commits', []))
        
        print("🤖 Running AI analysis...")
        groq_analysis = self.analyze_with_groq(repo_data)
        
        if "error" in groq_analysis:
            return groq_analysis
        
        print("🎯 Calculating score...")
        final_analysis = self.calculate_final_score(groq_analysis, commit_analysis)
        
        print("📄 Generating report...")
        report = self.generate_report(repo_data, final_analysis)
        
        return {
            "repo_data": repo_data,
            "final_analysis": final_analysis,
            "report": report
        }