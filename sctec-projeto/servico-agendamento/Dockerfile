# 1. Imagem base do Python (conforme PDF) [cite: 55]
FROM python:3.9-slim

# 2. Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# 3. Copia o arquivo de dependências primeiro (para cache)
COPY requirements.txt .

# 4. Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia todo o código do serviço (app.py, index.html, etc.)
COPY . .

# 6. Expõe a porta que o Flask usa
EXPOSE 5000

# 7. Comando para rodar a aplicação
#    '--host=0.0.0.0' é crucial para permitir conexões de fora do contêiner
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]