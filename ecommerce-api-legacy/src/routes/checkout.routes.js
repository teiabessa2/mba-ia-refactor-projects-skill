const express = require('express');
const checkoutController = require('../controllers/checkout.controller');

const router = express.Router();

router.post('/api/checkout', checkoutController.checkout);

module.exports = router;
