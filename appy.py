import streamlit as st
import sys
import os
import plotly.graph_objects as go

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repo_analyzer import GitHubRepoAnalyzer
import config

# Page config
st.set_page_config(
    page_title="GitHub Repo Scanner",
    page_icon="🔍",
    layout="wide"
)

# CSS
st.markdown("""
    <style>
    .big-score {
        font-size: 72px;
        font-weight: bold;
        text-align: center;
        padding: 30px;
        border-radius: 15px;
        margin: 20px 0;
    }
    .green-score { color: #10b981; background: #d1fae5; }
    .yellow-score { color: #f59e0b; background: #fef3c7; }
    .orange-score { color: #f97316; background: #ffedd5; }
    .red-score { color: #ef4444; background: #fee2e2; }
    </style>
""", unsafe_allow_html=True)

# Session state
if 'result' not in st.session_state:
    st.session_state.result = None
if 'analyzing' not in st.session_state:
    st.session_state.analyzing = False

# Title
st.title("🔍 GitHub Repo Intelligence Scanner")
st.markdown("**Detect AI-generated code & resume padding**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # ✅ FIXED: API key hidden by default
    groq_key_input = st.text_input(
        "Groq API Key:",
        type="password",
        value="",
        help="Optional: Enter key here, or leave blank to use config.py"
    )
    
    # Use config.py if user didn't enter anything
    groq_key = groq_key_input if groq_key_input else config.GROQ_API_KEY
    
    # Show status
    if groq_key:
        st.success("✅ API key loaded")
    else:
        st.error("❌ No API key found in config.py")
    
    st.markdown("---")
    st.markdown("### 📚 Examples:")
    example = st.selectbox("", [
        "Custom URL",
        "tensorflow/tensorflow",
        "facebook/react",
        "streamlit/streamlit",
        "vercel/next.js"
    ])
    
    st.markdown("---")
    st.info("""
    ### 🎯 What We Detect:
    - 🤖 AI-generated code
    - 📋 Resume padding
    - 🔬 Technical complexity
    - 📊 Authenticity score
    """)

# Main
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔗 Repository URL")
    
    if example == "Custom URL":
        default_url = ""
    else:
        default_url = f"https://github.com/{example}"
    
    repo_url = st.text_input(
        "GitHub URL:",
        value=default_url,
        placeholder="https://github.com/user/repo"
    )
    
    analyze_btn = st.button(
        "🔍 Analyze Repository",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.analyzing
    )
    
    if analyze_btn and not st.session_state.analyzing:
        if not groq_key:
            st.error("⚠️ Add Groq API key to config.py")
        elif not repo_url or not repo_url.startswith("https://github.com/"):
            st.error("⚠️ Enter valid GitHub URL")
        else:
            st.session_state.analyzing = True
            st.rerun()
    
    if not st.session_state.analyzing and not st.session_state.result:
        st.markdown("---")
        st.info("""
        **💡 How to use:**
        
        1. Make sure API key is in config.py
        2. Enter a GitHub repository URL
        3. Click "Analyze Repository"
        4. Wait ~15-20 seconds
        5. Review results
        
        **Try analyzing:**
        - Your own projects
        - Candidate portfolios
        - Popular open source repos
        """)

with col2:
    st.subheader("📊 Results")
    
    if st.session_state.analyzing:
        with st.spinner("🔍 Analyzing repository... This may take 15-20 seconds"):
            try:
                analyzer = GitHubRepoAnalyzer(groq_key=groq_key)
                result = analyzer.analyze_repository(repo_url)
                
                if "error" in result:
                    st.error(f"❌ Error: {result['error']}")
                    st.session_state.analyzing = False
                else:
                    st.session_state.result = result
                    st.session_state.analyzing = False
                    st.success("✅ Analysis Complete!")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                st.exception(e)
                st.session_state.analyzing = False
    
    elif st.session_state.result:
        result = st.session_state.result
        analysis = result['final_analysis']
        repo_data = result['repo_data']
        
        # Big Score Display
        score = analysis['authenticity_score']
        color_class = {
            "green": "green-score",
            "yellow": "yellow-score",
            "orange": "orange-score",
            "red": "red-score"
        }.get(analysis['color'], "green-score")
        
        st.markdown(
            f'<div class="big-score {color_class}">{score:.0f}/100</div>',
            unsafe_allow_html=True
        )
        
        st.markdown(f"### {analysis['category']}")
        st.progress(score/100, text=f"Authenticity: {score:.0f}%")
        
        st.markdown("---")
        
        # Metrics
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("🤖 AI-Generated", f"{analysis['ai_generated_score']}%")
        with m2:
            st.metric("🔬 Complexity", f"{analysis['technical_complexity']}/10")
        with m3:
            padding = analysis['groq_analysis'].get('resume_padding_score', 0)
            st.metric("📋 Padding", f"{padding}%")
        
        st.markdown("---")
        
        # Recommendation
        st.subheader("💡 Hiring Recommendation")
        if score >= 75:
            st.success(analysis['hiring_recommendation'])
        elif score >= 50:
            st.warning(analysis['hiring_recommendation'])
        else:
            st.error(analysis['hiring_recommendation'])
        
        st.markdown("---")
        
        # Red Flags
        st.subheader(f"🚩 Red Flags Detected ({len(analysis['red_flags'])})")
        if analysis['red_flags']:
            for flag in analysis['red_flags']:
                st.warning(flag)
        else:
            st.success("✅ No major red flags detected")
        
        # Charts
        st.markdown("---")
        st.subheader("📈 Visual Analysis")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Radar chart
            categories = ['Authenticity', 'Complexity', 'Originality']
            values = [
                analysis['authenticity_score'],
                analysis['technical_complexity'] * 10,
                100 - analysis['ai_generated_score']
            ]
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Scores',
                line_color='#3b82f6'
            ))
            
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=False,
                title="Score Profile",
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with chart_col2:
            # Bar chart
            risk_data = {
                'Factor': ['AI-Generated', 'Resume Padding', 'Low Complexity'],
                'Score': [
                    analysis['ai_generated_score'],
                    padding,
                    (10 - analysis['technical_complexity']) * 10
                ]
            }
            
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=risk_data['Factor'],
                y=risk_data['Score'],
                marker_color=['#ef4444', '#f59e0b', '#3b82f6'],
                text=risk_data['Score'],
                textposition='outside'
            ))
            
            fig2.update_layout(
                title="Risk Factors",
                yaxis_title="Score (0-100)",
                showlegend=False,
                height=300
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        # Detailed Info
        with st.expander("🔬 Detailed Analysis"):
            st.markdown("**Repository Info:**")
            st.write(f"- Name: {repo_data.get('name')}")
            st.write(f"- Description: {repo_data.get('description')}")
            st.write(f"- Language: {repo_data.get('language')}")
            st.write(f"- Stars: {repo_data.get('stars')}")
            
            st.markdown("---")
            st.markdown("**Commit Analysis:**")
            commit_analysis = analysis['commit_analysis']
            st.write(f"- Total commits: {commit_analysis.get('total_commits', 0)}")
            st.write(f"- Suspicious patterns: {len(commit_analysis.get('red_flags', []))}")
            
            if commit_analysis.get('commit_messages'):
                st.markdown("**Recent Commits:**")
                for i, msg in enumerate(commit_analysis.get('commit_messages', [])[:5], 1):
                    st.caption(f"{i}. {msg}")
        
        # Full Report
        with st.expander("📄 Full Report"):
            st.markdown(result['report'])
        
        # Download
        st.download_button(
            "📥 Download Report",
            result['report'],
            file_name=f"analysis_{repo_data.get('name', 'repo')}.md",
            mime="text/markdown",
            use_container_width=True
        )
        
        # Reset
        if st.button("🔄 Analyze Another Repository", use_container_width=True):
            st.session_state.result = None
            st.session_state.analyzing = False
            st.rerun()
    
    else:
        st.info("👈 Enter repository URL and click Analyze")
        st.markdown("""
        ### 🎯 What You'll Get:
        
        - **Authenticity Score (0-100)**
        - **AI-Generated Detection**
        - **Technical Complexity (1-10)**
        - **Resume Padding Indicators**
        - **Red Flag Analysis**
        - **Hiring Recommendations**
        
        ### 🆓 100% FREE:
        - Groq AI (no credit card)
        - Unlimited analyses
        - No GitHub token needed
        """)

# Footer
st.markdown("---")
st.caption("🔍 GitHub Repo Intelligence Scanner")
st.caption("⚠️ For educational purposes • Always conduct technical interviews")