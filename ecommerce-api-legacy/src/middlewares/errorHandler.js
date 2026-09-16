const logger = require('../utils/logger');

function errorHandler(err, req, res, next) {
    const statusCode = err.statusCode || 500;
    if (statusCode >= 500) {
        logger.error({ err }, 'Unhandled error');
        res.status(statusCode).send('Erro interno');
    } else {
        logger.warn({ message: err.message, statusCode }, 'Request error');
        res.status(statusCode).send(err.message);
    }
}

module.exports = errorHandler;
