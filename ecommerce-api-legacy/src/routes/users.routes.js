const express = require('express');
const { requireAdmin } = require('../middlewares/adminAuth');
const usersController = require('../controllers/users.controller');

const router = express.Router();

router.delete('/api/users/:id', requireAdmin, usersController.remove);

module.exports = router;
