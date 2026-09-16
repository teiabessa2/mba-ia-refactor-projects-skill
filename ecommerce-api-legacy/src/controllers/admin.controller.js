const reportsService = require('../services/reports.service');

async function financialReport(req, res, next) {
    try {
        const { page, size } = req.query;
        const result = await reportsService.generateFinancialReport({ page, size });
        res.json(result);
    } catch (err) {
        next(err);
    }
}

module.exports = { financialReport };
