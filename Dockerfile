FROM python:3.10-slim 
# Prevent Python from writing .pyc files & buffer issues 
ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1 
WORKDIR /app 
# System dependencies 
RUN apt-get update && apt-get install -y \ 
	libpq-dev gcc \ 
	&& rm -rf /var/lib/apt/lists/* 
# Copy requirement file and install dependencies 
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt 
# Copy project files 
COPY . . 
# Collect static files on build 
RUN python manage.py collectstatic --noinput 
EXPOSE 8000 
# Run Gunicorn 
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]