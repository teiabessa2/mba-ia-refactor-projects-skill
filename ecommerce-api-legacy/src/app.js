const express = require('express');
const config = require('./config');
const logger = require('./utils/logger');
const { initDb } = require('./db/database');
const checkoutRoutes = require('./routes/checkout.routes');
const adminRoutes = require('./routes/admin.routes');
const usersRoutes = require('./routes/users.routes');
const errorHandler = require('./middlewares/errorHandler');

if (!config.adminApiKey) {
    throw new Error('ADMIN_API_KEY não configurada — defina a variável de ambiente antes de iniciar a aplicação.');
}

const app = express();
app.use(express.json());

app.use(checkoutRoutes);
app.use(adminRoutes);
app.use(usersRoutes);

app.use(errorHandler);

async function start() {
    await initDb();
    app.listen(config.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

start();
