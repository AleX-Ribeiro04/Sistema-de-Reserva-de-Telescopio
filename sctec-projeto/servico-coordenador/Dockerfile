# 1. Imagem base do Node.js (conforme PDF) [cite: 60]
FROM node:18-alpine

# 2. Define o diretório de trabalho
WORKDIR /app

# 3. Copia os arquivos de definição do projeto (para cache)
COPY package.json package-lock.json* ./

# 4. Instala as dependências
RUN npm install

# 5. Copia o código do servidor
COPY server.js .

# 6. Expõe a porta que o Node usa
EXPOSE 3000

# 7. Comando para rodar a aplicação
CMD ["node", "server.js"]