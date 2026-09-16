const express = require('express');
const { requireAdmin } = require('../middlewares/adminAuth');
const adminController = require('../controllers/admin.controller');

const router = express.Router();

router.get('/api/admin/financial-report', requireAdmin, adminController.financialReport);

module.exports = router;
