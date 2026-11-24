FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN useradd --create-home --uid 10001 app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY lead_qualifier ./lead_qualifier
COPY app.py .
COPY .streamlit ./.streamlit
USER app
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"
# Pass ANTHROPIC_API_KEY at run time to read real leads with Claude; without it the app runs on the samples
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
