const config = require('../config');
const { AppError } = require('../utils/errors');

function requireAdmin(req, res, next) {
    const providedKey = req.get('x-admin-api-key');
    if (!providedKey || providedKey !== config.adminApiKey) {
        return next(new AppError('Não autorizado', 401));
    }
    next();
}

module.exports = { requireAdmin };
