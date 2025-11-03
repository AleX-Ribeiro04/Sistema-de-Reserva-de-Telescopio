const express = require('express');
const app = express();
const port = 3000; // Conforme API.md

app.use(express.json()); // Middleware para parsear JSON

// Estrutura de dados em memória para manter os locks (conforme MODELOS.md)
const locks = {};

/**
 * Função de logging estruturado (baseado no seu LOGGING.md)
 */
function log(level, message) {
    const timestamp = new Date().toISOString();
    // Formato: NIVEL:TIMESTAMP:SERVICO:MENSAGEM
    console.log(`${level}:${timestamp}:servico-coordenador:${message}`);
}

/**
 * Endpoint para adquirir um lock
 * 
 */
app.post('/lock', (req, res) => {
    const { resource_id } = req.body;

    if (!resource_id) {
        return res.status(400).json({ success: false, error: "resource_id é obrigatório" });
    }

    log('INFO', `Recebido pedido de lock para recurso ${resource_id}`); // [cite: 275]

    // Verifica se o recurso já está travado
    if (locks[resource_id]) {
        log('WARNING', `Recurso ${resource_id} já em uso, negando lock`); // [cite: 276]
        // Resposta 409 Conflict (conforme API.md)
        return res.status(409).json({
            success: false,
            resource_id: resource_id,
            message: "Recurso já está em uso",
            locked_since: locks[resource_id].locked_at
        });
    }

    // Adquire o lock
    const locked_at = new Date().toISOString();
    locks[resource_id] = { locked: true, locked_at: locked_at };

    log('INFO', `Lock concedido para recurso ${resource_id}`); // [cite: 275]
    
    // Resposta 200 OK (conforme API.md)
    res.status(200).json({
        success: true,
        resource_id: resource_id,
        locked_at: locked_at,
        message: "Lock adquirido com sucesso"
    });
});

/**
 * Endpoint para liberar um lock
 * 
 */
app.post('/unlock', (req, res) => {
    const { resource_id } = req.body;

    if (!resource_id) {
        return res.status(400).json({ success: false, error: "resource_id é obrigatório" });
    }

    log('INFO', `Recebido pedido de unlock para recurso ${resource_id}`);

    if (locks[resource_id]) {
        delete locks[resource_id]; // Libera o lock
        log('INFO', `Lock liberado para recurso ${resource_id}`); // [cite: 276]
        return res.status(200).json({
            success: true,
            resource_id: resource_id,
            message: "Lock liberado com sucesso"
        });
    } else {
        // Resposta 404 (conforme API.md)
        return res.status(404).json({
            success: false,
            resource_id: resource_id,
            message: "Nenhum lock encontrado para este recurso"
        });
    }
});

app.listen(port, () => {
    log('INFO', `Serviço Coordenador (Porteiro) rodando na porta ${port}`);
});